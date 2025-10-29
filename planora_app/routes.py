from flask import Blueprint, redirect, session, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))
