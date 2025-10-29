# planora_app/tasks/task_routes.py
from flask import Blueprint, render_template, request, jsonify, session
from planora_app.extensions import get_db
from .task_services import (
    create_task,
    get_tasks_for_user,
    update_task,
    delete_task,
    toggle_task_complete,
)

tasks_bp = Blueprint("tasks_bp", __name__, url_prefix="/tasks")


@tasks_bp.route("/", methods=["GET"])
def tasks_page():
    # Renders the page with the task UI
    return render_template("task.html")


@tasks_bp.route("/api", methods=["GET"])
def api_get_tasks():
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    tasks = get_tasks_for_user(db, user_id)
    return jsonify({"success": True, "tasks": tasks})


@tasks_bp.route("/api", methods=["POST"])
def api_create_task():
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    data = request.get_json(force=True)
    try:
        task = create_task(
            db,
            user_id,
            data.get("name"),
            data.get("deadline"),
            data.get("priority"),
            data.get("duration"),
        )
        return jsonify({"success": True, "task": task}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@tasks_bp.route("/api/<task_id>", methods=["PUT"])
def api_update_task(task_id):
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    data = request.get_json(force=True)
    try:
        task = update_task(db, task_id, user_id, data)
        return jsonify({"success": True, "task": task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@tasks_bp.route("/api/<task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    deleted = delete_task(db, task_id, user_id)
    if deleted:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "task not found or not owned"}), 404


@tasks_bp.route("/api/<task_id>/toggle", methods=["PATCH"])
def api_toggle_task(task_id):
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    data = request.get_json(force=True)
    completed = data.get("completed", False)
    try:
        task = toggle_task_complete(db, task_id, user_id, completed)
        return jsonify({"success": True, "task": task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400



# ---------------- Dashboard Top Tasks ----------------
@tasks_bp.route("/api/top", methods=["GET"])
def api_get_top_tasks():
    """Return top 3 upcoming or prioritized tasks for dashboard display."""
    db = get_db()
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    from .task_services import get_top_tasks_for_user
    tasks = get_top_tasks_for_user(db, user_id)
    return jsonify({"success": True, "tasks": tasks})