from datetime import datetime, timezone
from planora_app.extensions import get_db
from bson import ObjectId


def save_note(user_id: str, text: str):
    """
    Insert a new note.
    Returns the inserted_id.
    """
    db = get_db()

    doc = {
        "user_id": user_id,
        "text": text,
        "created_at": datetime.now(timezone.utc),
        "summary": None,
    }

    result = db.notes.insert_one(doc)
    return result.inserted_id


def get_latest_note(user_id: str):
    """
    Return latest note for a user.
    """
    db = get_db()

    doc = db.notes.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )

    return _serialize_note(doc) if doc else None


def get_note_by_id(user_id: str, note_id: str):
    """
    Return a note by id.
    """
    db = get_db()

    try:
        doc = db.notes.find_one(
            {
                "_id": ObjectId(note_id),
                "user_id": user_id,
            }
        )

        return _serialize_note(doc) if doc else None

    except Exception:
        return None


def get_all_notes_for_user(user_id: str):
    """
    Return all notes for a user.
    """
    db = get_db()

    docs = list(
        db.notes.find({"user_id": user_id}).sort(
            "created_at",
            -1,
        )
    )

    return [_serialize_note(doc) for doc in docs]


def _serialize_note(doc):
    """
    Convert Mongo document into JSON serializable dict.
    """
    if not doc:
        return None

    doc = dict(doc)
    doc["_id"] = str(doc["_id"])

    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()

    return doc


async def summarize_note(text: str) -> str:
    """
    Generate AI summary using Gemini.
    Returns a user-friendly message on failure.
    """

    try:

        import os
        from dotenv import load_dotenv
        from google import genai

        env_paths = [
            os.path.join(
                os.path.dirname(__file__),
                "../../.env",
            ),
            os.path.join(
                os.path.dirname(__file__),
                "../env",
            ),
        ]

        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(dotenv_path=env_path)
                break

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

        if not api_key:
            print("Gemini API key not configured.")
            return (
                "AI Summary is currently unavailable. "
                "Please try again later."
            )

        client = genai.Client(api_key=api_key)

        prompt = f"""
Please provide a concise and well-structured summary of the following study notes.

Organize the response into:

• Key Concepts
• Important Points
• Quick Summary

Notes:

{text}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return (
            "AI could not generate a summary at the moment. "
            "Please try again later."
        )

    except Exception as e:

        error = str(e)

        print("Summarize note error:")
        print(error)

        if (
            "RESOURCE_EXHAUSTED" in error
            or "429" in error
            or "quota" in error.lower()
        ):
            return (
                "⚠️ AI Summary is temporarily unavailable because "
                "the Gemini free quota has been reached.\n\n"
                "Please wait a few minutes and try again."
            )

        if (
            "API_KEY" in error
            or "api_key" in error.lower()
            or "authentication" in error.lower()
        ):
            return (
                "⚠️ AI Summary is currently unavailable due to an "
                "API configuration issue."
            )

        return (
            "⚠️ AI Summary could not be generated right now. "
            "Please try again after some time."
        )