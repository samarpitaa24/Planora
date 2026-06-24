import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from bson.objectid import ObjectId
from planora_app.extensions import get_db
from planora_app.settings.services import (
    calculate_study_stats,
    get_connected_accounts,
    change_user_password
)

settings_bp = Blueprint(
    "settings",
    __name__,
    template_folder="../templates",
    static_folder="../static",
    url_prefix="/settings"
)

@settings_bp.route("/", methods=["GET"])
@settings_bp.route("", methods=["GET"])
def settings_page():
    """
    Renders the settings page with user profile, stats, pomodoro settings, 
    and connected authentication status.
    """
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        session.clear()
        return redirect(url_for('auth.login'))
        
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    # Check if user onboarding is completed
    if not user.get('onboarding_completed', False):
        return redirect(url_for('onboarding.onboarding'))
        
    # Fetch real stats and streaks from sessions
    stats = calculate_study_stats(db, user_id)
    
    # Check connected account providers
    print(f"DEBUG [settings_page] User document from DB: email={user.get('email')}, oauth_provider={user.get('oauth_provider')}, has_password={bool(user.get('password'))}", flush=True)
    connected = get_connected_accounts(user)
    print(f"DEBUG [settings_page] Connected object returned: {connected}", flush=True)
    
    # Retrieve existing user Pomodoro settings, or set defaults
    pomodoro = user.get("pomodoro_settings", {})
    pomodoro_settings = {
        "focus_duration": pomodoro.get("focus_duration", 20),
        "short_break": pomodoro.get("short_break", 5),
        "long_break": pomodoro.get("long_break", 15),
        "num_cycles": pomodoro.get("num_cycles", 4)
    }
    
    # Format "Member Since" date
    created_at = user.get("created_at")
    if created_at:
        member_since = created_at.strftime("%B %d, %Y")
    else:
        member_since = "N/A"
        
    return render_template(
        "settings/settings.html",
        user=user,
        stats=stats,
        connected=connected,
        pomodoro=pomodoro_settings,
        member_since=member_since
    )

@settings_bp.route("/update-profile", methods=["POST"])
def update_profile():
    """
    Updates the user's full name and username.
    """
    db = get_db()
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized session."}), 401
        
    user_id = session['user_id']
    
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip().lower()
    
    if not full_name or not username:
        return jsonify({"success": False, "error": "Full Name and Username cannot be empty."}), 400
        
    # Username rules: alphanumeric + underscore, max 30 chars
    import re
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return jsonify({"success": False, "error": "Username must contain only letters, numbers, and underscores."}), 400
        
    if len(username) > 30:
        return jsonify({"success": False, "error": "Username cannot exceed 30 characters."}), 400
        
    # Check username uniqueness (excluding current user)
    existing = db.users.find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}})
    if existing:
        return jsonify({"success": False, "error": "Username is already taken."}), 400
        
    # Update user DB record
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "full_name": full_name,
            "username": username
        }}
    )
    
    # Keep session details aligned
    session['username'] = username
    
    return jsonify({"success": True, "message": "Profile updated successfully."})

@settings_bp.route("/update-avatar", methods=["POST"])
def update_avatar():
    """
    Processes profile avatar uploading (JPG/PNG only, under 2MB).
    """
    db = get_db()
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized session."}), 401
        
    user_id = session['user_id']
    
    if 'avatar' not in request.files:
        return jsonify({"success": False, "error": "No file part in request."}), 400
        
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected."}), 400
        
    # Validate extension
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['jpg', 'jpeg', 'png']:
        return jsonify({"success": False, "error": "Only JPG, JPEG, and PNG files are supported."}), 400
        
    # Validate size (read stream up to 2MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > 2 * 1024 * 1024:
        return jsonify({"success": False, "error": "Image file size exceeds the 2 MB limit."}), 400
        
    # Create local upload directory
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file securely using custom name
    filename = f"user_{user_id}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # Delete old file if name is different or override it
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
        
    file.save(file_path)
    
    # Generate static URL
    avatar_url = f"/static/uploads/avatars/{filename}"
    
    # Save URL to db user record
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": avatar_url}}
    )
    
    return jsonify({
        "success": True,
        "avatar_url": avatar_url,
        "message": "Profile picture updated successfully."
    })

@settings_bp.route("/remove-avatar", methods=["POST"])
def remove_avatar():
    """
    Removes user's avatar image, falling back to default styling.
    """
    db = get_db()
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized session."}), 401
        
    user_id = session['user_id']
    
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 400
        
    # Delete physical image file from static if present
    profile_pic = user.get("profile_picture")
    if profile_pic and "uploads/avatars/" in profile_pic:
        filename = profile_pic.split("uploads/avatars/")[-1]
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars', filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    # Reset field in DB
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": ""} }
    )
    
    return jsonify({"success": True, "message": "Profile picture removed successfully."})

@settings_bp.route("/update-pomodoro", methods=["POST"])
def update_pomodoro():
    """
    Updates the user's custom Pomodoro study settings.
    """
    db = get_db()
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized session."}), 401
        
    user_id = session['user_id']
    
    try:
        focus = int(request.form.get("focus_duration", 20))
        short_break = int(request.form.get("short_break", 5))
        long_break = int(request.form.get("long_break", 15))
        cycles = int(request.form.get("num_cycles", 4))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "All Pomodoro inputs must be valid integers."}), 400
        
    if focus <= 0 or short_break <= 0 or long_break <= 0 or cycles <= 0:
        return jsonify({"success": False, "error": "Settings values must be greater than zero."}), 400
        
    pomodoro_settings = {
        "focus_duration": focus,
        "short_break": short_break,
        "long_break": long_break,
        "num_cycles": cycles
    }
    
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"pomodoro_settings": pomodoro_settings}}
    )
    
    return jsonify({"success": True, "message": "Pomodoro settings saved successfully."})

@settings_bp.route("/change-password", methods=["POST"])
def change_password():
    """
    Processes local password updates for email/password users.
    """
    db = get_db()
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized session."}), 401
        
    user_id = session['user_id']
    
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "error": "All password fields are required."}), 400
        
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "New passwords do not match."}), 400
        
    success, message = change_user_password(db, user_id, current_password, new_password)
    if not success:
        return jsonify({"success": False, "error": message}), 400
        
    return jsonify({"success": True, "message": message})
