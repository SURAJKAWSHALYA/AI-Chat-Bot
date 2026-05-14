from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
load_dotenv()
import requests

app = Flask(__name__)

# 🔑 NEW API KEY (replace after regenerating!)

from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")



API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


def get_ai_response(message):
    try:
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a helpful, friendly chatbot."},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 512
        }

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            return f"API Error {response.status_code}: {response.text}"

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Exception Error: {str(e)}"


@app.route("/")
def home():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(debug=True)