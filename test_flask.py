# test_flask.py
from flask import Flask, request, jsonify
from wit import Wit
from dotenv import load_dotenv
import os
import requests
import psycopg2
from psycopg2 import Error as PgError
from requests import RequestException

# ---------------------------------------------------------
# .env laden & Clients bauen
# ---------------------------------------------------------
load_dotenv()
WIT_TOKEN        = os.getenv("WIT_TOKEN")
WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN")          # 60-Tage-Token
PHONE_NUMBER_ID  = os.getenv("PHONE_NUMBER_ID")
VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")
DATABASE_URL     = os.getenv("DATABASE_URL")

app = Flask(__name__)
wit_client = Wit(WIT_TOKEN)

# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------
def get_db():
    return psycopg2.connect(DATABASE_URL)

def top_intent(text: str, min_conf: float = 0.5) -> str:
    """liefert den besten wit.ai-Intentnamen oder 'default' bei geringer Confidence."""
    try:
        resp = wit_client.message(text)
        intents = resp.get("intents", [])
        if intents:
            cand = intents[0]
            if cand.get("confidence", 0) >= min_conf and cand.get("name"):
                return cand["name"]
    except Exception as ex:
        print("⚠️ wit.ai Fehler:", ex)
    return "default"

def save_termin(telefon: str, nachricht: str, intent: str) -> None:
    try:
        with get_db() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO termine (telefonnummer, nachricht, intent) VALUES (%s, %s, %s)",
                (telefon, nachricht, intent),
            )
        print("✅ Termin gespeichert.")
    except PgError as es:
        print("❌ DB-Fehler:", es)

def send_whatsapp(to: str, body: str) -> None:
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        print("📤 WA OK:", r.json())
    except RequestException as ec:
        print("❌ WhatsApp 401/403/…:", ec)

# ---------------------------------------------------------
# Antworten pro Intent (Namen müssen zu deinen wit.ai-Intents passen)
# ---------------------------------------------------------
ANTWORTEN = {
    "notfall":         "Ich informiere sofort den Notdienst!",
    "reklamation":     "Es tut mir leid! Bitte schildern Sie Ihr Problem an service@example.com.",
    "verabschiedung":  "Auf Wiedersehen! 👋",
    "hoeflichkeit":    "Gern geschehen!",
    "kontakt":         "Sie erreichen uns unter 0123 456789 oder kontakt@example.com.",
    "leistungen":      "Wir bieten Rohrreinigung, Wartung, Notdienste und mehr an.",
    "oeffnungszeiten": "Unsere Öffnungszeiten: Mo–Fr, 8–18 Uhr.",
    "preise":          "Gerne! Unsere Preisliste finden Sie auf der Website oder per Mail.",
    "standort":        "Wir sind in Berlin, Hamburg und Umgebung tätig.",
    "verf_gbarkeit":   "Wir sind rund um die Uhr erreichbar!",
    "termin_buchen":   "Wann möchten Sie den Termin? Wir melden uns gleich!",
    "default":         "Das habe ich leider nicht verstanden. Bitte formulieren Sie es anders.",
}

# ---------------------------------------------------------
# Routen
# ---------------------------------------------------------
@app.route("/")
def root():
    return "✅ Flask + wit.ai + WhatsApp Cloud API + PostgreSQL läuft!"

@app.route("/frage", methods=["POST"])
def frage():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Kein Text"}), 400
    intent = top_intent(text)
    return jsonify({"intent": intent, "antwort": ANTWORTEN.get(intent, ANTWORTEN["default"])})

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # 1) Verifizierung
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFICATION_TOKEN:
            return challenge, 200
        return "Unauthorized", 403

    # 2) Nachrichten empfangen
    data = request.get_json(silent=True) or {}
    try:
        value = data["entry"][0]["changes"][0]["value"]

        # Status-Updates ignorieren
        if value.get("statuses"):
            return "OK", 200

        msgs = value.get("messages") or []
        if not msgs:
            return "OK", 200

        msg = msgs[0]
        from_number = msg.get("from")
        text = (msg.get("text", {}).get("body") or "").strip()
        if not (from_number and text):
            return "OK", 200

        intent = top_intent(text)                  # <- hier passiert die Klassifikation über wit.ai
        reply = ANTWORTEN.get(intent, ANTWORTEN["default"])

        if intent == "termin_buchen":
            save_termin(from_number, text, intent)

        send_whatsapp(from_number, reply)

    except (KeyError, IndexError) as ex:
        print("❌ Unerwartetes Webhook-Format:", ex)
    except PgError as ex:
        print("❌ DB-Fehler:", ex)
    except RequestException as ex:
        print("❌ WhatsApp-API-Fehler:", ex)

    return "OK", 200

# ---------------------------------------------------------
# Start
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        with get_db() as _:
            print("🟢 DB-Check ok")
    except PgError as e:
        print("🔴 DB-Check fehlgeschlagen:", e)

    app.run(port=5000)