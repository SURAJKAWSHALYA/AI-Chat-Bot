from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import requests
import os

import uuid

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


# 🤖 HUMAN-LIKE BEST FRIEND AI RESPONSE
def get_ai_response(message):
    try:
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                "You are a natural Sri Lankan Gen-Z best friend AI. "
        "You speak modern casual Sinhala like WhatsApp chats. "
        "Avoid old formal Sinhala (like 'ඔබ', 'යුත්තේ', 'කළ යුතුය'). "
        "Use simple, natural, spoken Sinhala mixed with English when needed. "
        "Example style: 'oya kohomada 😊', 'mata nam shape na bro', 'kohenda inne?' "
        "Be friendly, chill, funny, and human-like. "
        "Keep replies short and natural like real texting. "
        "Do not generate broken Sinhala or meaningless sentences. "
        "Always respond in the same language style the user uses."
                    )
                },
                {"role": "user", "content": message}
            ],
            "temperature": 0.3,
            "max_tokens": 512
        }

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            return f"API Error {response.status_code}: {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Exception Error: {str(e)}"


# 🏠 HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# 💬 TEXT CHAT API
@app.route("/get", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message")

        if not user_message:
            return jsonify({"response": "No message received"})

        bot_reply = get_ai_response(user_message)

        return jsonify({"response": bot_reply})

    except Exception as e:
        return jsonify({"response": f"Server Error: {str(e)}"})


# 🔊 VOICE CHAT API
@app.route("/voice", methods=["POST"])
def voice():
    try:
        user_message = request.json.get("message")

        if not user_message:
            return jsonify({"error": "No message"})

        bot_reply = get_ai_response(user_message)

        filename = f"voice_{uuid.uuid4().hex}.mp3"

        # Voice output (English voice, works best)
        tts = gTTS(text=bot_reply, lang="en")
        tts.save(filename)

        return send_file(filename, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)