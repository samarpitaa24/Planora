from flask import Blueprint, render_template, session, jsonify
from planora_app.challenges.services import get_user_challenges, update_all_challenges
from planora_app.extensions import get_db

challenges_bp = Blueprint(
    "challenges",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/challenges"
)


@challenges_bp.route("/", methods=["GET"])
def challenges_page():
    return render_template("challenges.html")


@challenges_bp.route("/api", methods=["GET"])
def api_get_challenges():
    try:
        db = get_db()
        user_id = session.get("user_id") or "68dc37187ffd67372e424594"
        data = get_user_challenges(db, user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Force an update of all challenges and return the fresh list
@challenges_bp.route("/update", methods=["POST"])
def api_update_challenges():
    try:
        db = get_db()
        user_id = session.get("user_id") or "68dc37187ffd67372e424594"

        update_all_challenges(db, user_id)

        data = get_user_challenges(db, user_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500