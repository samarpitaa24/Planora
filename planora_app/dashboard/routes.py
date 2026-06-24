# dashboard/routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session

from planora_app.extensions import get_db
from bson.objectid import ObjectId


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")



@dashboard_bp.route("/")
def dashboard():
    db = get_db()

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = db.users.find_one({'_id': ObjectId(session['user_id'])})

    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if not user.get('onboarding_completed', False):
        return redirect(url_for('onboarding.onboarding'))

    return render_template("dashboard.html")




