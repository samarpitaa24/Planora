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
    toggle_pin,
    save_chat_document,
    get_chat_documents,
    set_active_document,
    delete_chat_document
)

from planora_app.ai.pdf_utils import (
    allowed_file,
    save_pdf,
    extract_pdf_text,
    MAX_FILE_SIZE
    )

from bson import ObjectId
from planora_app.extensions import get_db

chatbot_bp = Blueprint("chatbot",__name__)

@chatbot_bp.route("/chatbot/")
def chatbot_page():
    return render_template("chatbot.html")

@chatbot_bp.route("/chatbot/new", methods=["POST"])
def new_chat():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conversation_id = create_conversation(user_id)

    return jsonify({"conversation_id": conversation_id})
    
    
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
    save_message(conversation_id,"user","Hello World")

    return jsonify({"success": True})
    
@chatbot_bp.route("/chatbot/send", methods=["POST"])
def send_message():

    data = request.get_json()

    conversation_id = data.get("conversation_id")
    message = data.get("message", "").strip()

    if not conversation_id or not message:
        return jsonify({
            "error": "Missing data"
        }), 400

    if not ObjectId.is_valid(conversation_id):
        return jsonify({
            "error": "Invalid conversation ID format"
        }), 400

    db = get_db()

    conversation = db.chat_conversations.find_one({
        "_id": ObjectId(conversation_id)
    })

    if not conversation:
        return jsonify({
            "error": "Conversation not found"
        }), 404

    save_message(conversation_id, "user", message)

    if conversation.get("title") == "New Chat":
        update_conversation_title(conversation_id, message)

    try:

        reply = get_gemini_reply(
            conversation_id,
            message
        )

    except Exception as error:
        # print(error)

        busy_message = (
            "⚠️ Planora is currently experiencing high AI traffic.\n\n"
            "Please try again in a few moments."
        )

        save_message(
            conversation_id,
            "assistant",
            busy_message
        )

        return jsonify({

            "type": "text",

            "content": busy_message

        })

    if reply["type"] == "text":

        save_message(
            conversation_id,
            "assistant",
            reply["content"]
        )

    elif reply["type"] == "flashcards":

        save_message(conversation_id,"assistant","",message_type="flashcards",tool_id=reply["content"]["id"],tool_title=reply["content"]["title"])

    return jsonify(reply)
    
@chatbot_bp.route("/chatbot/delete/<conversation_id>",methods=["DELETE"])
def delete_chat(conversation_id):
    delete_conversation(conversation_id)
    return jsonify({"success": True})

@chatbot_bp.route("/chatbot/pin/<conversation_id>",methods=["POST"])
def pin_chat(conversation_id):
    toggle_pin(conversation_id)
    return jsonify({"success": True})
    
@chatbot_bp.route("/chatbot/upload-pdf", methods=["POST"])
def upload_pdf():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conversation_id = request.form.get("conversation_id")

    if not conversation_id:
        return jsonify({"error": "Conversation id missing"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": "Maximum file size is 10 MB"}), 400

    stored_filename, pdf_path = save_pdf(file)
    
    try:
        _, page_count = extract_pdf_text(pdf_path)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400

    document_id = save_chat_document(
        user_id=user_id,
        conversation_id=conversation_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        page_count=page_count,
        file_size=file_size)

    return jsonify({
        "success": True,
        "document_id": document_id,
        "filename": file.filename,
        "page_count": page_count
    })
    
@chatbot_bp.route("/chatbot/documents/<conversation_id>")
def load_documents(conversation_id):
    documents = get_chat_documents(conversation_id)
    return jsonify(documents)

@chatbot_bp.route("/chatbot/set-active-document",methods=["POST"])
def change_active_document():

    data = request.get_json()
    conversation_id = data.get("conversation_id")
    document_id = data.get("document_id")

    if not conversation_id:
        return jsonify({
            "error": "Conversation missing"
        }), 400

    if not document_id:
        return jsonify({
            "error": "Document missing"
        }), 400

    set_active_document(conversation_id,document_id)

    return jsonify({"success": True})

@chatbot_bp.route("/chatbot/document/<document_id>", methods=["DELETE"])
def delete_document(document_id):

    delete_chat_document(document_id)

    return jsonify({
        "success": True
    })