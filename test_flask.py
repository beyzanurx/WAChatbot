from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask läuft in IntelliJ!"

if __name__ == "__main__":
    app.run(port=5000)