from datetime import datetime, UTC

from planora_app.extensions import get_db


def save_document(
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


def get_conversation_documents(conversation_id):

    db = get_db()

    return list(

        db.chat_documents.find({

            "conversation_id": conversation_id

        })

    )