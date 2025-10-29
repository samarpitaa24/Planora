# dashboard/routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from . import services
from planora_app.utils import check_and_update_quota
import asyncio
from planora_app.extensions import get_db
from bson.objectid import ObjectId


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# In-memory session store: user_id -> list of messages
SESSION_CHATS = {}

# Example token cost estimation per message
TOKENS_PER_MSG = 50

@dashboard_bp.route("/")
def dashboard():
    db = get_db()

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = db.users.find_one({'_id': ObjectId(session['user_id'])})

    if not user.get('onboarding_completed', False):
        return redirect(url_for('onboarding.onboarding'))

    return render_template("dashboard.html")




@dashboard_bp.route("/chat", methods=["POST"])
def chat():
    """
    Expects JSON:
    {
        "user_id": "<user_id>",
        "message": "User text"
    }
    """
    data = request.get_json()
    user_id = data.get("user_id")
    user_message = data.get("message")

    if not user_id or not user_message:
        return jsonify({"error": "user_id and message required"}), 400

    # Initialize session if not present
    if user_id not in SESSION_CHATS:
        SESSION_CHATS[user_id] = []

    # Check quota before processing
    if not check_and_update_quota(user_id, TOKENS_PER_MSG):
        return jsonify({"error": "Daily token quota exceeded!"}), 403

    # Append user message to session
    SESSION_CHATS[user_id].append({"sender": "user", "message": user_message})
    # Keep only last 50 messages per session
    SESSION_CHATS[user_id] = SESSION_CHATS[user_id][-50:]

    # Generate system prompt (keep last 6 messages for context)
    system_prompt = (
        "You are Planora's Study Assistant, an AI tutor. Follow these rules strictly:\n"
        "Answer only study-related questions; do not discuss unrelated topics.\n"
        "Keep answers concise, clear, and easy to understand.\n"
        "Provide examples only if they help explain the concept.\n"
        "Use simple language; avoid unnecessary jargon.\n"
        "Do not answer anything beyond the scope of study help.\n"
        "Maintain context of the ongoing session.\n\n"
        "Conversation so far:\n"
    )

    recent_msgs = SESSION_CHATS[user_id][-6:]
    for msg in recent_msgs:
        system_prompt += f"{msg['sender']}: {msg['message']}\n"

    # Call Gemini API (synchronous)
    bot_reply = asyncio.run(services.call_gemini_api(system_prompt))

    # Append bot reply to session
    SESSION_CHATS[user_id].append({"sender": "bot", "message": bot_reply})

    # Log for debugging
    print(f"[Chat] {user_id}: {user_message} -> {bot_reply}")

    return jsonify({"reply": bot_reply})
