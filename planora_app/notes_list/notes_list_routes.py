from flask import Blueprint, render_template, session, request, jsonify
# inside notes_list_routes.py
from planora_app.notes_list.notes_list_services import get_user_notes, toggle_star_note, delete_note, update_note

from bson import ObjectId

notes_bp = Blueprint("notes", __name__, template_folder="templates", static_folder="static")

@notes_bp.route("/notes")
def notes_page():
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    return render_template("notes_list.html", user_id=user_id)

# API to fetch notes
@notes_bp.route("/notes/fetch")
def fetch_notes():
    user_id = request.args.get("user_id") or "68dc37187ffd67372e424594"
    filter_type = request.args.get("filter_type")  # date, week, month, year, starred
    filter_value = request.args.get("filter_value")  # specific value for filter
    notes = get_user_notes(user_id, filter_type, filter_value)
    return jsonify({"notes": notes})

# API to toggle star
@notes_bp.route("/notes/toggle_star", methods=["POST"])
def star_note():
    data = request.get_json()
    note_id = data.get("note_id")
    new_star_value = data.get("starred")
    toggle_star_note(note_id, new_star_value)
    return jsonify({"success": True, "note_id": note_id, "starred": new_star_value})

@notes_bp.route("/notes/delete", methods=["POST"])
def delete_note_route():
    data = request.get_json() or {}
    note_id = data.get("note_id")
    if not note_id:
        return jsonify({"success": False, "error": "note_id is required"}), 400
    deleted = delete_note(note_id)
    if not deleted:
        return jsonify({"success": False, "error": "Note not found"}), 404
    return jsonify({"success": True, "note_id": note_id}), 200

@notes_bp.route("/notes/update", methods=["POST"])
def update_note_route():
    data = request.get_json() or {}
    note_id = data.get("note_id")
    text = (data.get("text") or "").strip()
    if not note_id or not text:
        return jsonify({"success": False, "error": "note_id and text are required"}), 400
    updated = update_note(note_id, text)
    if not updated:
        return jsonify({"success": False, "error": "Unable to update note"}), 404
    return jsonify({"success": True, "note_id": note_id}), 200
