import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import BOT_NAME, GREETING, MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_HISTORY = 20
MAX_MESSAGE_LENGTH = 2000

generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.3,
    max_output_tokens=1500,
)


def build_contents(history, message):
    contents = []
    for turn in history[-MAX_HISTORY:]:
        role = "model" if turn.get("role") == "bot" else "user"
        text = str(turn.get("text", "")).strip()
        if text:
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text)])
            )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


@app.route("/")
def index():
    return render_template("index.html", bot_name=BOT_NAME, greeting=GREETING)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please type a question."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "Your message is too long. Please shorten it."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=generation_config,
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "I could not generate a response. Please rephrase your question."
        return jsonify({"reply": reply})
    except Exception:
        return jsonify({"error": "The service is unavailable right now. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
