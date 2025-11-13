from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from datetime import datetime
from bson.objectid import ObjectId
import re
import bcrypt

from planora_app.extensions import get_db

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user.get('username', user.get('full_name', 'User'))
            flash('Login successful!', 'success')

            # ✅ Check onboarding
            if not user.get('onboarding_completed', False):
                return redirect(url_for('onboarding.onboarding'))

            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db()

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # ✅ Password Validation (Keeps your logic fully intact)
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.signup'))

        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return redirect(url_for('auth.signup'))

        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter', 'danger')
            return redirect(url_for('auth.signup'))

        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter', 'danger')
            return redirect(url_for('auth.signup'))

        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number', 'danger')
            return redirect(url_for('auth.signup'))

        if not re.search(r'[!@#$%^&*]', password):
            flash('Password must contain at least one special character (!@#$%^&*)', 'danger')
            return redirect(url_for('auth.signup'))

        # ✅ Check if user exists
        if db.users.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.signup'))

        if db.users.find_one({'username': username}):
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.signup'))

        # ✅ Store hashed password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'created_at': datetime.utcnow(),
            'onboarding_completed': False # ✅ New user should still go through onboarding
        }

        db.users.insert_one(user_data)

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html') # ✅ revert to correct template

@auth.route("/logout")
def logout():
    """Logs the user out by clearing the session and redirecting to login."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
