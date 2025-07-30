from flask import Flask, request, jsonify
from wit import Wit
from dotenv import load_dotenv
import os
import requests

# .env-Datei laden
load_dotenv()


app = Flask(__name__)
client = Wit(os.getenv("WIT_TOKEN"))

# Antworten für erkannte Intents
antworten = {
    "notfall": "Ich informiere sofort den Notdienst!",
    "reklamation": "Es tut mir leid! Bitte schildern Sie Ihr Problem an service@example.com.",
    "verabschiedung": "Auf Wiedersehen! 👋",
    "hoeflichkeit": "Gern geschehen!",
    "kontakt": "Sie erreichen uns unter 0123 456789 oder kontakt@example.com.",
    "leistungen": "Wir bieten Rohrreinigung, Wartung, Notdienste und mehr an.",
    "oeffnungszeiten": "Unsere Öffnungszeiten: Mo–Fr, 8–18 Uhr.",
    "preise": "Gerne! Unsere Preisliste finden Sie auf der Website oder per Mail.",
    "standort": "Wir sind in Berlin, Hamburg und Umgebung tätig.",
    "verf_gbarkeit": "Wir sind rund um die Uhr erreichbar!",
    "termin_buchen": "Wann möchten Sie den Termin? Wir melden uns gleich!",
    "default": "Das habe ich leider nicht verstanden. Bitte formulieren Sie es anders."
}

@app.route("/")
def home():
    return "✅ Flask + wit.ai + WhatsApp Cloud API läuft!"

@app.route("/frage", methods=["POST"])
def frage():
    daten = request.get_json()
    nachricht = daten.get("text", "")


    wit_antwort = client.message(nachricht)
    intent = wit_antwort.get("intents", [{}])[0].get("name", "default")
    reaktion = antworten.get(intent, antworten["default"])

    return jsonify({
        "intent": intent,
        "antwort": reaktion
    })

def sende_whatsapp_nachricht(telefonnummer, text):
    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefonnummer,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Antwort gesendet:", response.json())

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == os.getenv("VERIFICATION_TOKEN"):
            return challenge, 200
        return "Unauthorized", 403

    if request.method == "POST":
        daten = request.get_json()
        try:
            eintrag = daten["entry"][0]["changes"][0]["value"]["messages"][0]
            text = eintrag["text"]["body"]
            nummer = eintrag["from"]

            wit_antwort = client.message(text)
            intent = wit_antwort.get("intents", [{}])[0].get("name", "default")
            reaktion = antworten.get(intent, antworten["default"])

            sende_whatsapp_nachricht(nummer, reaktion)
        except Exception as e:
            print("Fehler beim Verarbeiten der Nachricht:", e)

        return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)