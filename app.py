from flask import Flask, render_template, request, jsonify, send_file, redirect, session, after_this_request
from dotenv import load_dotenv

import requests
import os
import uuid
import sqlite3

from gtts import gTTS
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# APP CONFIG
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

if not GROQ_API_KEY:
    print("❌ ERROR: GROQ API KEY NOT FOUND")

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        theme TEXT,
        language TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT
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
                    "content": """
You are AI Mithura 🤖, a professional Sinhala AI assistant.

PRIMARY LANGUAGE RULES:
- Always respond in natural, clear Sinhala (Sri Lankan style)
- Do NOT mix English unless the user uses English
- Do NOT add random words, fake names, or meaningless phrases
- Do NOT include translations like (Translation:)
- Keep Sinhala grammar clean and natural

TONE:
- Friendly like ChatGPT
- Helpful, calm, and intelligent
- Short to medium length answers
- Use emojis only when appropriate 😊

BEHAVIOR RULES:
- Never act like girlfriend/boyfriend or romantic partner
- If user asks romantic questions → politely refuse and redirect
- Always stay consistent and professional

QUALITY RULE:
- Think before responding
- Give meaningful, clear answers
- Avoid repetition and broken sentences
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": 0.2,
            "max_tokens": 300
        }

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code != 200:
            return "API Error occurred"

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except:
            return "Response parsing error"

    except Exception as e:
        return f"Error: {str(e)}"

# =========================
# HOME
# =========================
@app.route("/")
def home():
    if "user" in session:
        return redirect("/chatbot")
    return redirect("/login")

# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

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
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = str(username)
            return redirect("/chatbot")

        return "Invalid username or password"

    return render_template("login.html")

# =========================
# CHATBOT PAGE
# =========================
@app.route("/chatbot")
def chatbot():
    if "user" not in session:
        return redirect("/login")

    return render_template("index.html", username=session["user"])

# =========================
# PROFILE
# =========================
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    return render_template("profile.html", username=session["user"])

# =========================
# SETTINGS
# =========================
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if request.method == "POST":
        theme = request.form["theme"]
        language = request.form["language"]

        c.execute("SELECT * FROM settings WHERE username=?", (username,))
        existing = c.fetchone()

        if existing:
            c.execute("""
                UPDATE settings
                SET theme=?, language=?
                WHERE username=?
            """, (theme, language, username))
        else:
            c.execute("""
                INSERT INTO settings(username, theme, language)
                VALUES (?, ?, ?)
            """, (username, theme, language))

        conn.commit()

    c.execute("SELECT * FROM settings WHERE username=?", (username,))
    data = c.fetchall()

    conn.close()

    return render_template("settings.html", data=data, username=username)

# =========================
# HISTORY
# =========================
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT * FROM history WHERE username=?", (username,))
    chats = c.fetchall()

    conn.close()

    return render_template("history.html", chats=chats, username=username)

# =========================
# SAVE CHAT
# =========================
@app.route("/save_chat", methods=["POST"])
def save_chat():
    if "user" not in session:
        return jsonify({"status": "error"})

    data = request.get_json()
    message = data.get("message")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO history(username, message)
        VALUES (?, ?)
    """, (session["user"], message))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})

# =========================
# CHAT API
# =========================
@app.route("/get", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"response": "Please login first"})

    user_message = request.json.get("message")

    if not user_message or not user_message.strip():
        return jsonify({"response": "Empty message"})

    bot_reply = get_ai_response(user_message)

    # SAVE CHAT
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("INSERT INTO history(username, message) VALUES (?, ?)",
              (session["user"], f"USER: {user_message}"))

    c.execute("INSERT INTO history(username, message) VALUES (?, ?)",
              (session["user"], f"AI: {bot_reply}"))

    conn.commit()
    conn.close()

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

    @after_this_request
    def remove_file(response):
        try:
            os.remove(filename)
        except:
            pass
        return response

    return send_file(filename, mimetype="audio/mpeg")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)