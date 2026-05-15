from flask import Flask, render_template, request, jsonify, send_file, redirect, session
from dotenv import load_dotenv
import requests
import os
import uuid
import sqlite3


load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# =========================
# AI RESPONSE
# =========================
def get_ai_response(message):
    try:
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Sri Lankan Gen-Z friendly AI. "
                        "Speak casual Sinhala like WhatsApp chat. "
                        "Be short, natural, friendly."
                    )
                },
                {"role": "user", "content": message}
            ],
            "temperature": 0.3,
            "max_tokens": 512
        }

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            return f"API Error: {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error: {str(e)}"


# =========================
# HOME (redirect login)
# =========================
@app.route("/")
def home():
    return redirect("/login")


# =========================
# CHATBOT PAGE
# =========================
@app.route("/chatbot")
def chatbot():
    if "user" not in session:
        return redirect("/login")

    return render_template("index.html", username=session["user"])


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:
            return "Username already exists"

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/chatbot")

        return "Invalid Username or Password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# CHAT API
# =========================
@app.route("/get", methods=["POST"])
def chat():

    if "user" not in session:
        return jsonify({"response": "Please login first"})

    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"response": "No message received"})

    bot_reply = get_ai_response(user_message)

    return jsonify({"response": bot_reply})


# =========================
# VOICE API
# =========================
@app.route("/voice", methods=["POST"])
def voice():

    if "user" not in session:
        return jsonify({"error": "Please login first"})

    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"error": "No message"})

    bot_reply = get_ai_response(user_message)

    filename = f"voice_{uuid.uuid4().hex}.mp3"

    tts = gTTS(text=bot_reply, lang="en")
    tts.save(filename)

    return send_file(filename, mimetype="audio/mpeg")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)