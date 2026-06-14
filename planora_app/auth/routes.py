import os
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from datetime import datetime
import re
import bcrypt
from authlib.integrations.flask_client import OAuth

from planora_app.extensions import get_db

auth = Blueprint("auth", __name__, url_prefix="/auth")
oauth = OAuth()


def init_oauth(app):
    """Register OAuth clients once during Flask app creation."""
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    oauth.register(
        name="github",
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"},
    )


def _missing_oauth_config(provider):
    provider_key = provider.upper()
    return not os.getenv(f"{provider_key}_CLIENT_ID") or not os.getenv(f"{provider_key}_CLIENT_SECRET")


def _oauth_redirect_uri(provider):
    return url_for(f"auth.{provider}_callback", _external=True)


def _set_login_session(user):
    session.clear()
    session["user_id"] = str(user["_id"])
    session["username"] = user.get("username") or user.get("full_name") or user.get("name") or "User"


def _unique_username(db, base_username):
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", (base_username or "user").strip().lower()) or "user"
    username = cleaned[:30]
    candidate = username
    counter = 1

    while db.users.find_one({"username": candidate}):
        suffix = str(counter)
        candidate = f"{username[:30 - len(suffix)]}{suffix}"
        counter += 1

    return candidate


def _find_user_by_oauth_or_email(db, provider, oauth_id, email=None):
    user = db.users.find_one({"oauth_provider": provider, "oauth_id": str(oauth_id)})
    if user:
        return user

    if email:
        return db.users.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})

    return None


def _create_google_user(db, user_info):
    email = (user_info.get("email") or "").lower()
    full_name = user_info.get("name") or email.split("@")[0] or "Google User"
    username_base = email.split("@")[0] if email else full_name

    user_data = {
        "full_name": full_name,
        "username": _unique_username(db, username_base),
        "email": email,
        "oauth_provider": "Google",
        "oauth_id": str(user_info.get("sub")),
        "profile_picture": user_info.get("picture"),
        "created_at": datetime.utcnow(),
        "daily_quota": 10000,
        "tokens_used": 0,
        "onboarding_completed": True,
    }

    result = db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


def _get_github_email():
    try:
        emails_response = oauth.github.get("user/emails")
        emails_response.raise_for_status()
        emails = emails_response.json()
        primary = next((item for item in emails if item.get("primary") and item.get("verified")), None)
        verified = next((item for item in emails if item.get("verified")), None)
        selected = primary or verified
        return selected.get("email").lower() if selected and selected.get("email") else None
    except Exception:
        return None


def _create_github_user(db, profile, email):
    github_username = profile.get("login") or f"github_{profile.get('id')}"
    full_name = profile.get("name") or github_username

    user_data = {
        "full_name": full_name,
        "name": full_name,
        "username": _unique_username(db, github_username),
        "github_username": github_username,
        "email": email,
        "oauth_provider": "GitHub",
        "oauth_id": str(profile.get("id")),
        "profile_picture": profile.get("avatar_url"),
        "created_at": datetime.utcnow(),
        "daily_quota": 10000,
        "tokens_used": 0,
        "onboarding_completed": True,
    }

    result = db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


@auth.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})

        stored_password = user.get('password') if user else None

        if stored_password and bcrypt.checkpw(password.encode('utf-8'), stored_password):
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
            "daily_quota": 10000,      # default quota
            "tokens_used": 0,          # default usage
            'onboarding_completed': False # ✅ New user should still go through onboarding
        }

        db.users.insert_one(user_data)

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html') # ✅ revert to correct template

@auth.route("/google")
def google_login():
    if _missing_oauth_config("google"):
        flash("Google sign-in is not configured yet.", "danger")
        return redirect(url_for("auth.login"))

    return oauth.google.authorize_redirect(_oauth_redirect_uri("google"))


@auth.route("/google/callback")
def google_callback():
    db = get_db()

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            user_info_response = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo")
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

        if not user_info.get("sub") or not user_info.get("email"):
            flash("Google did not return the required account details.", "danger")
            return redirect(url_for("auth.login"))

        email = user_info.get("email").lower()
        user = _find_user_by_oauth_or_email(db, "Google", user_info.get("sub"), email)

        if not user:
            user = _create_google_user(db, user_info)

        _set_login_session(user)
        flash("Logged in with Google successfully!", "success")
        return redirect(url_for("dashboard.dashboard"))
    except Exception:
        flash("Google sign-in failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))


@auth.route("/github")
def github_login():
    if _missing_oauth_config("github"):
        flash("GitHub sign-in is not configured yet.", "danger")
        return redirect(url_for("auth.login"))

    return oauth.github.authorize_redirect(_oauth_redirect_uri("github"))


@auth.route("/github/callback")
def github_callback():
    db = get_db()

    try:
        oauth.github.authorize_access_token()
        profile_response = oauth.github.get("user")
        profile_response.raise_for_status()
        profile = profile_response.json()

        if not profile.get("id"):
            flash("GitHub did not return the required account details.", "danger")
            return redirect(url_for("auth.login"))

        email = profile.get("email")
        email = email.lower() if email else _get_github_email()
        user = _find_user_by_oauth_or_email(db, "GitHub", profile.get("id"), email)

        if not user:
            user = _create_github_user(db, profile, email)

        _set_login_session(user)
        flash("Logged in with GitHub successfully!", "success")
        return redirect(url_for("dashboard.dashboard"))
    except Exception:
        flash("GitHub sign-in failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():
    """Logs the user out by clearing the session and redirecting to login."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
