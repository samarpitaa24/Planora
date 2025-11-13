from flask import Blueprint, render_template, session, request, jsonify
from planora_app.sessions.sessions_services import get_user_sessions

sessions_bp = Blueprint("sessions", __name__, template_folder="templates", static_folder="static")

@sessions_bp.route("/sessions")
def sessions_page():
    user_id = session.get("user_id") or "68dc37187ffd67372e424594"
    return render_template("sessions.html", user_id=user_id)

@sessions_bp.route("/sessions/fetch")
def fetch_sessions():
    user_id = request.args.get("user_id") or "68dc37187ffd67372e424594"
    filter_type = request.args.get("filter_type")
    filter_value = request.args.get("filter_value")
    
    sessions = get_user_sessions(user_id, filter_type, filter_value)
    
    return jsonify({"sessions": sessions})