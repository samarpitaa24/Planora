from flask import (
    Blueprint,
    render_template,
    session,
    request,
    jsonify,
)

from planora_app.notes_list.notes_list_services import (
    get_user_notes,
    toggle_star_note,
    delete_note,
    update_note,
)

notes_bp = Blueprint(
    "notes",
    __name__,
    template_folder="templates",
    static_folder="static",
)


def get_current_user():
    """
    Return the currently logged-in user's id.
    """
    return session.get("user_id")


@notes_bp.route("/notes")
def notes_page():

    user_id = get_current_user()

    if not user_id:
        return render_template(
            "notes_list.html",
            user_id=None,
        ), 401

    return render_template(
        "notes_list.html",
        user_id=user_id,
    )


@notes_bp.route("/notes/fetch")
def fetch_notes():

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    filter_type = request.args.get("filter_type")
    filter_value = request.args.get("filter_value")

    notes = get_user_notes(
        user_id,
        filter_type,
        filter_value,
    )

    return jsonify(
        {
            "success": True,
            "notes": notes,
        }
    ), 200


@notes_bp.route("/notes/toggle_star", methods=["POST"])
def star_note():

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    data = request.get_json() or {}

    note_id = data.get("note_id")
    new_star_value = data.get("starred")

    if not note_id:
        return jsonify(
            {
                "success": False,
                "error": "note_id is required",
            }
        ), 400

    toggle_star_note(user_id, note_id, new_star_value)

    return jsonify(
        {
            "success": True,
            "note_id": note_id,
            "starred": new_star_value,
        }
    ), 200


@notes_bp.route("/notes/delete", methods=["POST"])
def delete_note_route():

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    data = request.get_json() or {}

    note_id = data.get("note_id")

    if not note_id:
        return jsonify(
            {
                "success": False,
                "error": "note_id is required",
            }
        ), 400

    deleted = delete_note(user_id, note_id)

    if not deleted:
        return jsonify(
            {
                "success": False,
                "error": "Note not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "note_id": note_id,
        }
    ), 200


@notes_bp.route("/notes/update", methods=["POST"])
def update_note_route():

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    data = request.get_json() or {}

    note_id = data.get("note_id")
    text = (data.get("text") or "").strip()

    if not note_id or not text:
        return jsonify(
            {
                "success": False,
                "error": "note_id and text are required",
            }
        ), 400

    updated = update_note(user_id, note_id, text)

    if not updated:
        return jsonify(
            {
                "success": False,
                "error": "Unable to update note",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "note_id": note_id,
        }
    ), 200