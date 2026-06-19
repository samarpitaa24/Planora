from flask import Blueprint, request, jsonify, session, render_template
from planora_app.notes.notes_services import save_note, get_latest_note, get_note_by_id, get_all_notes_for_user, summarize_note
import asyncio

notes_bp = Blueprint("notes_bp", __name__)

# fallback user id for dev as you requested
FALLBACK_USER_ID = "68dc37187ffd67372e424594"

@notes_bp.route("/notes/save", methods=["POST"])
def save_note_route():
    user_id = session.get("user_id") or FALLBACK_USER_ID
    payload = request.get_json() or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Note text is required."}), 400

    inserted_id = save_note(user_id, text)
    return jsonify({"success": True, "note_id": str(inserted_id)}), 201

@notes_bp.route("/notes/latest", methods=["GET"])
def latest_note_route():
    user_id = session.get("user_id") or FALLBACK_USER_ID
    note = get_latest_note(user_id)
    if not note:
        return jsonify({"latest_note": None}), 200

    return jsonify({
        "latest_note": {
            "_id": note.get("_id"),
            "text": note.get("text"),
            "created_at": note.get("created_at")
        }
    }), 200

@notes_bp.route("/notes/list", methods=["GET"])
def list_notes_route():
    """Return all notes for user as JSON."""
    user_id = session.get("user_id") or FALLBACK_USER_ID
    notes = get_all_notes_for_user(user_id)
    return jsonify({"success": True, "notes": notes}), 200

@notes_bp.route("/notes/<note_id>", methods=["GET"])
def get_note_detail_route(note_id):
    """Return a specific note by ID."""
    user_id = session.get("user_id") or FALLBACK_USER_ID
    note = get_note_by_id(user_id, note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"success": True, "note": note}), 200

@notes_bp.route("/notes-detail", methods=["GET"])
def notes_detail_page():
    """Render the notes detail page."""
    return render_template("notes_detail.html")

@notes_bp.route("/notes/<note_id>/summarize", methods=["POST"])
def summarize_note_route(note_id):
    """Generate and save a summary for a note."""
    user_id = session.get("user_id") or FALLBACK_USER_ID
    note = get_note_by_id(user_id, note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    try:
        summary = asyncio.run(summarize_note(note.get("text", "")))
        from planora_app.extensions import get_db
        db = get_db()
        db.notes.update_one(
            {"_id": __import__("bson").ObjectId(note_id)},
            {"$set": {"summary": summary}}
        )
        return jsonify({"success": True, "summary": summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
