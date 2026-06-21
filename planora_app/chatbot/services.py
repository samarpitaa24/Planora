from datetime import datetime, UTC
from bson import ObjectId

from planora_app.extensions import get_db
import os
from google import genai
from planora_app.ai.prompts import SYSTEM_PROMPT

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
        ])
    )

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
    conversation_id: str,
    sender: str,
    message: str
):
    db = get_db()

    db.chat_messages.insert_one({
        "conversation_id": conversation_id,
        "sender": sender,
        "message": message,
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
            "message": msg["message"]
        })

    return result


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def get_gemini_reply(conversation_id: str, user_message: str):

    db = get_db()

    history = list(
        db.chat_messages.find(
            {
                "conversation_id":
                conversation_id
            }
        )
        .sort("created_at", -1)
        .limit(10)
    )

    history.reverse()

    conversation_context = ""

    for msg in history:

        conversation_context += (
            f"{msg['sender']}: "
            f"{msg['message']}\n"
        )

    prompt = f"""
        {SYSTEM_PROMPT}

        Conversation History:

        {conversation_context}

        Current Question:

        {user_message}

        Answer:
        """

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if (
            hasattr(response, "text")
            and response.text
        ):
            return response.text

        return (
            "I couldn't generate a response."
        )

    except Exception as e:

        print("Gemini Error:", e)

        return (
            "The study assistant is currently busy. "
            "Please try again."
        )
        
def update_conversation_title(
    conversation_id: str,
    title: str
):
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
    
def delete_conversation(
    conversation_id: str
):
    db = get_db()

    db.chat_conversations.delete_one({
        "_id": ObjectId(conversation_id)
    })

    db.chat_messages.delete_many({
        "conversation_id": conversation_id
    })


def toggle_pin(
    conversation_id: str
):
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


def save_chat_document(
    user_id,
    conversation_id,
    original_filename,
    stored_filename,
    page_count,
    file_size
):

    db = get_db()

    result = db.chat_documents.insert_one({

        "user_id": user_id,

        "conversation_id": conversation_id,

        "original_filename": original_filename,

        "stored_filename": stored_filename,

        "page_count": page_count,

        "file_size": file_size,

        "created_at": datetime.now(UTC)

    })

    return str(result.inserted_id)