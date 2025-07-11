from flask import Flask, request, jsonify
from wit import Wit
from dotenv import load_dotenv
import os

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
    return "✅ Flask läuft mit wit.ai!"

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


if __name__ == "__main__":
    app.run(port=5000)