import os
from datetime import datetime, timedelta
import bcrypt
import re
import pytz
from bson import ObjectId
from werkzeug.utils import secure_filename

def calculate_study_stats(db, user_id):
    """
    Calculates the streak and progress statistics for the user based on real sessions.
    - Current Streak: consecutive study days ending today (or yesterday).
    - Longest Streak: highest streak of consecutive study days ever achieved.
    - Total Study Days: count of unique study days.
    - Total Study Hours: sum of completed study time in hours.
    """
    user_id = str(user_id)
    
    # Query sessions where completion_status is Completed (case-insensitive)
    sessions = list(db.sessions.find({
        "user_id": user_id,
        "completion_status": {"$in": ["Completed", "completed"]}
    }))
    
    # Build unique set of studied dates
    studied_days = set()
    total_minutes = 0
    
    for s in sessions:
        date_str = s.get("date")
        if date_str:
            try:
                studied_days.add(datetime.strptime(date_str, "%Y-%m-%d").date())
            except ValueError:
                pass
        total_minutes += s.get("total_time", 0)
        
    # Total Study Days is the number of unique dates
    total_study_days = len(studied_days)
    
    # Total Study Hours is the sum of completed study time divided by 60
    total_study_hours = round(total_minutes / 60.0, 1)
    
    # Current Streak Calculation (IST timezone context)
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist).date()
    
    current_streak = 0
    if today in studied_days:
        day_check = today
        while day_check in studied_days:
            current_streak += 1
            day_check -= timedelta(days=1)
    elif (today - timedelta(days=1)) in studied_days:
        day_check = today - timedelta(days=1)
        while day_check in studied_days:
            current_streak += 1
            day_check -= timedelta(days=1)
    else:
        current_streak = 0
        
    # Longest Streak Calculation
    sorted_days = sorted(list(studied_days))
    longest_streak = 0
    current_run = 0
    prev_day = None
    
    for day in sorted_days:
        if prev_day is None:
            current_run = 1
        elif day == prev_day + timedelta(days=1):
            current_run += 1
        elif day == prev_day:
            pass
        else:
            longest_streak = max(longest_streak, current_run)
            current_run = 1
        prev_day = day
    longest_streak = max(longest_streak, current_run)
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_study_days": total_study_days,
        "total_study_hours": total_study_hours
    }

def get_connected_accounts(user):
    """
    Checks the authentication providers linked to the user account.
    Returns flags for Email, Google, and GitHub connection.
    """
    user_id = str(user.get("_id", "unknown"))
    provider = user.get("oauth_provider")
    oauth_id = user.get("oauth_id")
    has_password = bool(user.get("password"))
    
    is_google = (provider == "Google")
    is_github = (provider == "GitHub")
    # If there is no oauth provider, it is a password-based email account
    is_email = not provider
    
    # DEBUG LOGS
    print(f"DEBUG [get_connected_accounts] User ID: {user_id}", flush=True)
    print(f"DEBUG [get_connected_accounts] OAuth Provider: {provider}", flush=True)
    print(f"DEBUG [get_connected_accounts] OAuth ID: {oauth_id}", flush=True)
    print(f"DEBUG [get_connected_accounts] Has Password: {has_password}", flush=True)
    print(f"DEBUG [get_connected_accounts] Email Linked: {is_email}, Google Linked: {is_google}, GitHub Linked: {is_github}", flush=True)
    
    return {
        "is_email": is_email,
        "is_google": is_google,
        "is_github": is_github
    }

def validate_password_strength(password):
    """
    Checks password strength constraints:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    return True, ""

def change_user_password(db, user_id, current_password, new_password):
    """
    Validates current password and updates to a new hashed password.
    """
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False, "User not found."
        
    stored_password = user.get("password")
    if not stored_password:
        return False, "This account does not have a local password configured."
        
    # Verify current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password):
        return False, "Incorrect current password."
        
    # Validate strength of the new password
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return False, error_msg
        
    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Update DB
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password}}
    )
    return True, "Password updated successfully."
