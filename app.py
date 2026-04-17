import json
from pathlib import Path
from uuid import uuid4
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_DIR = Path(__file__).resolve().parent / "data"
DECKS_FILE = DATA_DIR / "decks.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_ACTUAL_API_KEY_HERE")
client = genai.Client(api_key=GEMINI_API_KEY)

def basic_reply(message: str) -> str:
    text = message.strip()
    if not text:
        return "Ask me anything about your studies."
    lower = text.lower()
    if "integral" in lower or "calculus" in lower:
        return "For calculus, start by identifying the function family and apply the most direct integration rule first."
    if "physics" in lower or "quantum" in lower:
        return "For physics topics, break the problem into known variables, equations, and unit checks."
    if "summary" in lower:
        return "I can summarize it: share the topic plus 3 key points you want to keep."
    return f"Got it. Here is a basic response to '{text}': focus on concepts, then solve 2 practice questions."


def _ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DECKS_FILE.exists():
        DECKS_FILE.write_text("[]", encoding="utf-8")


def _load_decks():
    _ensure_store()
    try:
        return json.loads(DECKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_decks(decks):
    _ensure_store()
    DECKS_FILE.write_text(json.dumps(decks, indent=2), encoding="utf-8")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    
    # 4. Use the new Gemini function
    reply = get_gemini_reply(message)
    
    return jsonify({"reply": reply})
    
@app.get("/decks")
def list_decks():
    decks = _load_decks()
    return jsonify({"decks": decks})

def get_gemini_reply(message: str) -> str:
    text = message.strip()
    if not text:
        return "Ask me anything about your studies."

    try:
        # 3. Call the Gemini API
        # We use a system instruction to keep the bot focused on its persona
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
            config={
                "system_instruction": "You are a helpful study assistant. Keep answers concise and focus on helping the student understand concepts."
            }
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "I'm having trouble thinking right now. Please try again in a second!"
        
@app.post("/decks")
def create_deck():
    payload = request.get_json(silent=True) or {}
    chapter = str(payload.get("chapter", "")).strip()
    notes_topic = str(payload.get("notesTopic", "")).strip()
    cards = payload.get("cards", [])

    cleaned_cards = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        question = str(card.get("question", "")).strip()
        answer = str(card.get("answer", "")).strip()
        if question and answer:
            cleaned_cards.append({"question": question, "answer": answer})

    if not chapter:
        return jsonify({"error": "Chapter is required."}), 400
    if not cleaned_cards:
        return jsonify({"error": "Add at least one valid flashcard."}), 400

    deck = {
        "id": str(uuid4()),
        "chapter": chapter,
        "notesTopic": notes_topic,
        "cards": cleaned_cards,
        "cardCount": len(cleaned_cards),
    }

    decks = _load_decks()
    decks.append(deck)
    _save_decks(decks)
    return jsonify({"deck": deck}), 201




@app.delete("/decks/<deck_id>")
def delete_deck(deck_id: str):
    decks = _load_decks()
    next_decks = [deck for deck in decks if deck.get("id") != deck_id]
    if len(next_decks) == len(decks):
        return jsonify({"error": "Deck not found."}), 404
    _save_decks(next_decks)
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
