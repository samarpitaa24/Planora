from planora_app.extensions import get_db
from datetime import datetime
from bson import ObjectId


def get_user_notes(user_id: str, filter_type=None, filter_value=None):
    """
    Return notes belonging to the given user with optional filters.
    """

    db = get_db()

    query = {
        "user_id": user_id
    }

    today = datetime.utcnow().date()

    if filter_type and filter_value:

        if filter_type == "date":

            try:
                dt = datetime.strptime(
                    filter_value,
                    "%Y-%m-%d"
                )

                query["created_at"] = {
                    "$gte": datetime(dt.year, dt.month, dt.day),
                    "$lt": datetime(dt.year, dt.month, dt.day, 23, 59, 59)
                }

            except Exception:
                pass

        elif filter_type == "month":

            try:
                month = int(filter_value)

                start = datetime(today.year, month, 1)

                if month == 12:
                    end = datetime(today.year + 1, 1, 1)
                else:
                    end = datetime(today.year, month + 1, 1)

                query["created_at"] = {
                    "$gte": start,
                    "$lt": end
                }

            except Exception:
                pass

        elif filter_type == "year":

            try:
                year = int(filter_value)

                query["created_at"] = {
                    "$gte": datetime(year, 1, 1),
                    "$lt": datetime(year + 1, 1, 1)
                }

            except Exception:
                pass

        elif filter_type == "starred":

            query["starred"] = True

    notes_cursor = db.notes.find(query).sort(
        [
            ("starred", -1),
            ("created_at", -1)
        ]
    )

    notes_list = []

    for note in notes_cursor:

        text = note.get("text", "")

        words = text.split()

        snippet = (
            " ".join(words[:35]) +
            ("..." if len(words) > 35 else "")
        )

        created_at = note.get("created_at")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        notes_list.append({

            "_id": str(note["_id"]),
            "text": text,
            "snippet": snippet,
            "created_at": created_at,
            "starred": note.get("starred", False)

        })

    return notes_list


def delete_note(user_id: str, note_id: str):

    db = get_db()

    try:

        result = db.notes.delete_one({

            "_id": ObjectId(note_id),
            "user_id": user_id

        })

        return result.deleted_count > 0

    except Exception:

        return False


def update_note(user_id: str, note_id: str, text: str):

    db = get_db()

    try:

        result = db.notes.update_one(

            {
                "_id": ObjectId(note_id),
                "user_id": user_id
            },

            {
                "$set": {
                    "text": text
                }
            }

        )

        return result.modified_count > 0

    except Exception:

        return False


def toggle_star_note(user_id: str, note_id: str, starred: bool):

    db = get_db()

    try:

        result = db.notes.update_one(

            {
                "_id": ObjectId(note_id),
                "user_id": user_id
            },

            {
                "$set": {
                    "starred": starred
                }
            }

        )

        return result.modified_count > 0

    except Exception:

        return False