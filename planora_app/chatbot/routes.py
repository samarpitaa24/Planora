# planora_app/chatbot/routes.py

from flask import Blueprint, render_template, request, jsonify, session
from flask import request, jsonify
from planora_app.chatbot.services import (
    create_conversation,
    get_user_conversations,
    get_messages,
    save_message,
    get_gemini_reply,
    update_conversation_title,
    delete_conversation,
    toggle_pin
)
from bson import ObjectId
from planora_app.extensions import get_db

chatbot_bp = Blueprint(
    "chatbot",
    __name__
)

@chatbot_bp.route("/chatbot/")
def chatbot_page():

    return render_template("chatbot.html")

@chatbot_bp.route("/chatbot/new", methods=["POST"])
def new_chat():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conversation_id = create_conversation(user_id)

    return jsonify({
        "conversation_id": conversation_id
    })
    
    
@chatbot_bp.route("/chatbot/conversations")
def get_conversations():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conversations = get_user_conversations(user_id)

    return jsonify(conversations)

@chatbot_bp.route("/chatbot/conversation/<conversation_id>")
def load_conversation(conversation_id):

    messages = get_messages(conversation_id)

    return jsonify(messages)

@chatbot_bp.route("/chatbot/test-message", methods=["POST"])
def test_message():

    data = request.get_json()

    conversation_id = data.get("conversation_id")

    save_message(
        conversation_id,
        "user",
        "Hello World"
    )

    return jsonify({
        "success": True
    })
    
@chatbot_bp.route("/chatbot/send",methods=["POST"])
def send_message():

    data = request.get_json()

    conversation_id = data.get("conversation_id")
    message = data.get("message")

    if not conversation_id or not message:
        return jsonify({
            "error": "Missing data"
        }), 400

    save_message(
        conversation_id,
        "user",
        message
    )

    db = get_db()

    conversation = db.chat_conversations.find_one(
    {
        "_id": ObjectId(conversation_id)
    }
    )

    if (conversation and conversation.get("title") == "New Chat"):
        update_conversation_title(conversation_id, message)

    reply = get_gemini_reply(
    conversation_id,
    message)

    save_message(
        conversation_id,
        "assistant",
        reply
    )

    return jsonify({
        "reply": reply
    })
    
@chatbot_bp.route(
    "/chatbot/delete/<conversation_id>",
    methods=["DELETE"]
)
def delete_chat(conversation_id):

    delete_conversation(
        conversation_id
    )

    return jsonify({
        "success": True
    })


@chatbot_bp.route(
    "/chatbot/pin/<conversation_id>",
    methods=["POST"]
)
def pin_chat(conversation_id):

    toggle_pin(
        conversation_id
    )

    return jsonify({
        "success": True
    })