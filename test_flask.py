from flask import Flask, request, jsonify
from wit import Wit
from dotenv import load_dotenv
import os

# .env-Datei laden
load_dotenv()


app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask läuft mit wit.ai!"

@app.route("/frage", methods=["POST"])
def frage():
    daten = request.get_json()
    nachricht = daten.get("text")

    client = Wit(os.getenv("WIT_TOKEN"))
    antwort = client.message(nachricht)

    intent = antwort["intents"][0]["name"] if antwort["intents"] else "unbekannt"

    if intent == "notfall":
        reaktion = "Ich informiere sofort den Notdienst!"
    else:
        reaktion = f"Intent erkannt: '{intent}'"

    return jsonify({"antwort": reaktion})

if __name__ == "__main__":
    app.run(port=5000)