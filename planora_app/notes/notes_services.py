from datetime import datetime, timezone
from planora_app.extensions import get_db
from bson import ObjectId


def save_note(user_id: str, text: str):
    """
    Insert a new note. Returns the inserted_id.
    """
    db = get_db()
    notes = db.notes
    doc = {
        "user_id": user_id,
        "text": text,
        "created_at": datetime.now(timezone.utc),
        "summary": None
    }
    result = notes.insert_one(doc)
    return result.inserted_id

def get_latest_note(user_id: str):
    """
    Return the latest note document for this user (or None).
    """
    db = get_db()
    notes = db.notes
    # find_one supports a sort parameter
    doc = notes.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    return _serialize_note(doc) if doc else None

def get_note_by_id(user_id: str, note_id: str):
    """
    Retrieve a specific note by ID for the user.
    """
    db = get_db()
    notes = db.notes
    try:
        doc = notes.find_one({"_id": ObjectId(note_id), "user_id": user_id})
        return _serialize_note(doc) if doc else None
    except Exception:
        return None

def get_all_notes_for_user(user_id: str):
    """
    Get all notes for a user, sorted by creation date (newest first).
    """
    db = get_db()
    notes = db.notes
    docs = list(notes.find({"user_id": user_id}).sort("created_at", -1))
    return [_serialize_note(doc) for doc in docs]

def _serialize_note(doc):
    """Convert note document to JSON-serializable dict."""
    if not doc:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc

async def summarize_note(text: str) -> str:
    """
    Use Gemini API to generate a summary of the note.
    """
    try:
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        # Resolve env path from project root or planora_app/env
        env_paths = [
            os.path.join(os.path.dirname(__file__), '../../.env'),
            os.path.join(os.path.dirname(__file__), '../env'),
        ]
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(dotenv_path=env_path)
                break
        
        # Try GEMINI_API_KEY first, then GOOGLE_API_KEY
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY in env file."
        
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""Please provide a concise and well-structured summary of the following study notes. 
Organize it with:
- Key Concepts (bullet points)
- Important Points (bullet points)
- Quick Summary (2-3 sentences)

Notes:
{text}"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Summarize note error: {e}")
        import traceback
        traceback.print_exc()
        return f"Could not generate summary: {str(e)}"
