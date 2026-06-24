# planora_app/dashboard/cards_routes.py

from flask import Blueprint, request, jsonify, session

from .cards_services import (
    calculate_best_time,
    get_priority_focus,
)

from planora_app.dashboard.cards_services import (
    get_daily_streak,
)

cards_bp = Blueprint(
    "cards",
    __name__,
    url_prefix="/cards",
)


def get_current_user():
    """
    Return the currently logged-in user's id.
    Returns None if the user is not authenticated.
    """
    return session.get("user_id")


@cards_bp.route("/best-time", methods=["GET"])
def get_best_time():

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    result = calculate_best_time(user_id)

    return jsonify(result), 200


@cards_bp.route("/priority-focus", methods=["GET"])
def priority_focus():
    """
    Returns Priority Focus card data.
    """

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    result = get_priority_focus(user_id)

    return jsonify(result), 200


@cards_bp.route("/daily-streak", methods=["GET"])
def daily_streak_route():
    """
    Returns Daily Streak card data.
    """

    user_id = get_current_user()

    if not user_id:
        return jsonify(
            {
                "success": False,
                "error": "User not authenticated",
            }
        ), 401

    result = get_daily_streak(user_id)

    return jsonify(result), 200