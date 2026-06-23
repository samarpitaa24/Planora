from datetime import datetime, UTC
from bson import ObjectId

from planora_app.extensions import get_db
import os
from planora_app.ai.prompts import SYSTEM_PROMPT

import os
from planora_app.ai.pdf_utils import extract_pdf_text
from planora_app.ai.chunking import chunk_text
from planora_app.ai.gemini import generate_response
from planora_app.flashcards.services import generate_flashcards

from dotenv import load_dotenv
load_dotenv()

def create_conversation(user_id: str, title: str = "New Chat"):
    db = get_db()

    conversation = {
    "user_id": user_id,
    "title": title,
    "is_pinned": False,
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC)}

    result = db.chat_conversations.insert_one(conversation)
    return str(result.inserted_id)

def get_user_conversations(user_id: str):
    db = get_db()
    conversations = list(
        db.chat_conversations.find(
            {"user_id": user_id}
        ).sort([
            ("is_pinned", -1),
            ("updated_at", -1)
        ]))

    result = []

    for convo in conversations:
        result.append({
            "id": str(convo["_id"]),
            "title": convo.get(
                "title",
                "New Chat"
            ),
            "is_pinned": convo.get(
                "is_pinned",
                False
            )
        })

    return result

def save_message(
    conversation_id,
    sender,
    message,
    message_type="text",
    tool_id=None,
    tool_title=None
):

    db = get_db()

    db.chat_messages.insert_one({

        "conversation_id": conversation_id,
        "sender": sender,
        "message": message,
        "message_type": message_type,
        "tool_id": tool_id,
        "tool_title": tool_title,
        "created_at": datetime.now(UTC)

    })

def get_messages(conversation_id: str):
    db = get_db()
    messages = list(
        db.chat_messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1)
    )

    result = []

    for msg in messages:
        result.append({
            "sender": msg["sender"],
            "message": msg["message"],
            "message_type": msg.get("message_type","text"),
            "tool_id": msg.get("tool_id"),
            "tool_title": msg.get("tool_title")})

    return result

def get_active_document(conversation_id):
    db = get_db()
    return db.chat_documents.find_one({
        "conversation_id": conversation_id,
        "is_active": True})


def get_gemini_reply(conversation_id, user_message):
    db = get_db()
    history = list(
        db.chat_messages.find({
            "conversation_id": conversation_id
        })
        .sort("created_at", -1)
        .limit(10) )

    history.reverse()
    conversation_history = ""
    for message in history:
        conversation_history += (
            f"{message['sender']}: "
            f"{message['message']}\n"
        )

    active_document = get_active_document(conversation_id)
    
    lower_message = user_message.lower()

    if ("flashcard" in lower_message or "flashcards" in lower_message):

        if not active_document:
            return {
                "type": "text",
                "content": "Please select a study source first."
            }

        flashcard_set = generate_flashcards(
            str(active_document["_id"]),
            10
        )

        return {
            "type": "flashcards",
            "content": flashcard_set
        }
    
    pdf_context = ""

    if active_document:

        pdf_path = os.path.join(
            "planora_app",
            "static",
            "uploads",
            "pdfs",
            active_document["stored_filename"]
        )

    try:
        text, _ = extract_pdf_text(pdf_path)
        chunks = chunk_text(text)
        pdf_context = "\n\n".join(chunks[:3])

    except Exception:
        pdf_context = ""

    prompt = f"""
        {SYSTEM_PROMPT}
        Study Material:{pdf_context}
        Conversation:{conversation_history}
        Current Question:{user_message}
        Answer: """
        
    response = generate_response(prompt)

    return {
        "type": "text",
        "content": response
    }

        
def update_conversation_title(conversation_id: str,title: str):
    db = get_db()
    
    db.chat_conversations.update_one(
        {
            "_id": ObjectId(conversation_id)
        },
        {
            "$set": {
                "title": title[:50]
            }
        }
    )
    
def delete_conversation(conversation_id: str):
    db = get_db()

    db.chat_conversations.delete_one({
        "_id": ObjectId(conversation_id)
    })

    db.chat_messages.delete_many({
        "conversation_id": conversation_id
    })


def toggle_pin(conversation_id: str):
    db = get_db()

    conversation = db.chat_conversations.find_one({
        "_id": ObjectId(conversation_id)
    })

    if not conversation:
        return

    db.chat_conversations.update_one(
        {
            "_id": ObjectId(conversation_id)
        },
        {
            "$set": {
                "is_pinned":
                not conversation.get(
                    "is_pinned",
                    False
                )
            }
        }
    )
    
from datetime import datetime, UTC


def save_chat_document(user_id,conversation_id,original_filename,stored_filename,page_count,file_size):
    db = get_db()

    existing_document = db.chat_documents.find_one({
    "conversation_id": conversation_id,
    "original_filename": original_filename,
    "file_size": file_size})

    if existing_document:
        return str(existing_document["_id"])
    
    existing_active = db.chat_documents.find_one({
        "conversation_id": conversation_id,
        "is_active": True
    })

    if existing_active is None:
        is_active = True
    else:
        is_active = False

    result = db.chat_documents.insert_one({
        "user_id": user_id,
        "conversation_id": conversation_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "page_count": page_count,
        "file_size": file_size,
        "is_active": is_active,
        "created_at": datetime.now(UTC)
    })

    return str(result.inserted_id)

def get_chat_documents(conversation_id):
    db = get_db()
    documents = list(
        db.chat_documents.find({
            "conversation_id": conversation_id}))

    result = []

    for document in documents:
        result.append({
            "id": str(document["_id"]),
            "original_filename": document["original_filename"],
            "page_count": document["page_count"],
            "file_size": document["file_size"],
            "is_active": document.get(
                "is_active",
                False
            )})

    return result

def set_active_document(conversation_id, document_id):
    db = get_db()
    db.chat_documents.update_many(
        {
            "conversation_id": conversation_id
        },

        {
            "$set": {
                "is_active": False
            }
        })

    db.chat_documents.update_one(
        {
            "_id": ObjectId(document_id)
        },
        {
            "$set": {
                "is_active": True
            }
        })

    return True

def delete_chat_document(document_id):
    db = get_db()

    document = db.chat_documents.find_one({
        "_id": ObjectId(document_id)
    })

    if not document:
        return

    pdf_path = os.path.join(
        "planora_app",
        "static",
        "uploads",
        "pdfs",
        document["stored_filename"]
    )

    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    conversation_id = document["conversation_id"]

    was_active = document.get("is_active",False)

    db.chat_documents.delete_one({"_id": ObjectId(document_id)})

    if was_active:
        latest = db.chat_documents.find_one(
            {
                "conversation_id": conversation_id
            },
            sort=[("created_at", -1)]
        )

        if latest:
            db.chat_documents.update_one(
                {
                    "_id": latest["_id"]
                },
                {
                    "$set": {
                        "is_active": True
                    }
                }
            )