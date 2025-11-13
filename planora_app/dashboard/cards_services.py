# planora_app/dashboard/cards_services.py
from datetime import datetime, timedelta
from collections import Counter
import platform
from bson import ObjectId
from planora_app.extensions import get_db

# configuration
BUCKET_MINUTES = 15                 # bucket granularity
BUCKETS_PER_DAY = 24 * 60 // BUCKET_MINUTES  # 96
MIN_SESSIONS_REQUIRED = 15
MAX_SESSIONS_TO_FETCH = 30
# window sizes (in number of buckets). 2 hours max -> 8 buckets (8*15=120)
WINDOW_BUCKET_OPTIONS = [2, 3, 4, 6, 8]  # 30m,45m,60m,90m,120m


def _format_time_from_minutes(minutes_since_midnight: int) -> str:
    """
    Convert minutes (0..1439) to 12-hour string like '5:30 PM'.
    """
    minutes = minutes_since_midnight % (24 * 60)
    h = minutes // 60
    m = minutes % 60
    dt = datetime(2000, 1, 1, h, m)
    # Windows uses %#I, Unix uses %-I
    if platform.system() == "Windows":
        return dt.strftime("%#I:%M %p")
    else:
        return dt.strftime("%-I:%M %p")


def _minute_to_bucket_index(total_minutes: int) -> int:
    """Return bucket index 0..95 for a minute-of-day value."""
    return (total_minutes % (24 * 60)) // BUCKET_MINUTES


def _add_session_to_buckets(start_dt: datetime, end_dt: datetime, buckets: list):
    """
    Add +1 to every 15-min bucket covered by [start_dt, end_dt).
    Rounds start down to bucket floor and end up to bucket ceiling.
    """
    # convert to minute-of-day
    start_min = start_dt.hour * 60 + start_dt.minute
    # floor to bucket
    start_min = (start_min // BUCKET_MINUTES) * BUCKET_MINUTES

    end_min = end_dt.hour * 60 + end_dt.minute
    # ceil end to the next bucket boundary
    if end_min % BUCKET_MINUTES != 0:
        end_min = ((end_min // BUCKET_MINUTES) + 1) * BUCKET_MINUTES

    # iterate in 15-min steps
    cur = start_min
    while cur < end_min:
        idx = _minute_to_bucket_index(cur)
        buckets[idx] += 1
        cur += BUCKET_MINUTES


def _preferred_time_from_qna(user_doc: dict) -> str:
    """
    Try to extract a fallback preferred time string from user doc.
    Looks for 'preferred_time' key first, then qna.morning_evening_person.
    """

    qna = user_doc.get("qna", {}) or {}
    me =qna.get("morning_evening_person") or qna.get("preferred_time")
    if not me:
        return "Not set"
    me = me.lower()
    if "morning" in me:
        return "Morning (6:00 AM – 10:00 AM)"
    if "evening" in me:
        return "Evening (5:00 PM – 9:00 PM)"
    if "night" in me or "night owl" in me:
        return "Night (9:00 PM – 12:00 AM)"
    return me.title()




def calculate_best_time(user_id: str, debug: bool = False) -> dict:
    """
    Computes the user's best study time window.
    Returns {"best_time": "<start> to <end>"}.
    If debug=True, also returns sessions used and bucket counts.
    """
    db = get_db()
    
    # Fetch user safely
    try:
        user_obj = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return {"best_time": "Invalid user id format"}

    if not user_obj:
        return {"best_time": "No user found"}

    # Fetch recent sessions (max 30)
    sessions_cursor = db.sessions.find({"user_id": user_id}).sort("start_time", -1).limit(MAX_SESSIONS_TO_FETCH)
    sessions = list(sessions_cursor)

    if len(sessions) < MIN_SESSIONS_REQUIRED:
        # fallback to user's preferred time
        pref = _preferred_time_from_qna(user_obj)
        return {"best_time": pref}

    buckets = [0] * BUCKETS_PER_DAY
    session_times = []

    for s in sessions:
        start = s.get("start_time")
        end = s.get("end_time")
        if not start or not end:
            continue
        # Add session to bucket counts
        _add_session_to_buckets(start, end, buckets)
        session_times.append(f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}")

    if sum(buckets) == 0:
        pref = _preferred_time_from_qna(user_obj)
        return {"best_time": pref}

    # Sliding window over duplicated buckets (wrap-around)
    extended = buckets + buckets
    best_score = -1.0
    best_sum = 0
    best_start_idx = 0
    best_w = 0

    for w in WINDOW_BUCKET_OPTIONS:
        window_sum = sum(extended[0:w])
        for start in range(0, BUCKETS_PER_DAY):
            if start > 0:
                window_sum = window_sum - extended[start - 1] + extended[start + w - 1]
            density = window_sum / float(w)
            if (density, window_sum, -w) > (best_score, best_sum, -best_w):
                best_score = density
                best_sum = window_sum
                best_start_idx = start
                best_w = w

    start_min = (best_start_idx % BUCKETS_PER_DAY) * BUCKET_MINUTES
    end_min = start_min + best_w * BUCKET_MINUTES

    start_str = _format_time_from_minutes(start_min)
    end_str = _format_time_from_minutes(end_min % (24 * 60))

    result = {"best_time": f"{start_str} to {end_str}"}

    if debug:
        result["sessions_used"] = session_times
        result["bucket_counts"] = buckets

    return result

#SUBJECT RECOMMENDATION 

def get_priority_focus(user_id: str) -> dict:
    """
    Returns the recommended subject for the user along with reason.
    Handles categories: Last Studied, Under Studied, Over Studied, Difficulty-Based.
    """
    db = get_db()

    # Validate and fetch user
    try:
        user_obj = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return {"subject": "Invalid user", "reason": "User ID format is incorrect"}

    if not user_obj:
        return {"subject": "No user found", "reason": "Start using Planora to get recommendations"}

    today = datetime.utcnow().date()

    # Fetch last 15 sessions
    sessions_cursor = db.sessions.find({"user_id": user_id}).sort("start_time", -1).limit(15)
    sessions = list(sessions_cursor)

    # --- New user fallback (Difficulty-Based) ---
    if not sessions:
        subjects = user_obj.get("qna", {}).get("subjects", [])
        if subjects:
            mid_index = len(subjects) // 2
            subj = subjects[mid_index]
            return {"subject": subj, "reason": f"Recommended subject: {subj} (medium difficulty)"}
        return {"subject": "No subjects", "reason": "Please add subjects in your preferences"}

    # --- Build stats from sessions ---
    subject_data = {}
    for s in sessions:
        subj = s.get("subject")
        session_date_val = s.get("date")
        if not subj or not session_date_val:
            continue

        # Handle date as string or datetime
        if isinstance(session_date_val, str):
            try:
                session_date = datetime.strptime(session_date_val, "%Y-%m-%d").date()
            except ValueError:
                continue
        elif isinstance(session_date_val, datetime):
            session_date = session_date_val.date()
        else:
            continue

        if subj not in subject_data:
            subject_data[subj] = {"last_date": session_date, "count": 1}
        else:
            subject_data[subj]["count"] += 1
            if session_date > subject_data[subj]["last_date"]:
                subject_data[subj]["last_date"] = session_date

    if not subject_data:
        return {"subject": "No valid sessions", "reason": "Check your session logs"}

    # Compute days since last studied
    for subj, data in subject_data.items():
        data["days_since"] = (today - data["last_date"]).days

    # --- Last Studied (neglected) ---
    priority_subj, info = max(
        subject_data.items(),
        key=lambda x: (x[1]["days_since"], -x[1]["count"])  # tie-breaker: less frequent subject
    )
    if info["days_since"] > 0:
        reason_text = f"Last studied: {info['days_since']} day{'s' if info['days_since'] != 1 else ''} ago"
        return {"subject": priority_subj, "reason": reason_text}

    # --- Under Studied ---
    avg_count = sum(d["count"] for d in subject_data.values()) / len(subject_data)
    under_studied = [s for s, d in subject_data.items() if d["count"] < avg_count]
    if under_studied:
        subj = under_studied[0]
        reason_text = f"You should focus on {subj} today"
        return {"subject": subj, "reason": reason_text}

    # --- Over Studied / Balanced fallback ---
    return {"subject": "All subjects balanced", "reason": "Keep up your study rhythm!"}



#streaks 

def get_daily_streak(user_id: str) -> dict:
    """
    Calculates the daily streak for a user and days missed in current month.
    Returns {"streak": X, "missed": Y, "message": "..."}
    """
    db = get_db()
    try:
        user_obj = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return {"streak": 0, "missed": 0, "message": "Invalid user id"}

    if not user_obj:
        return {"streak": 0, "missed": 0, "message": "User not found"}

    join_date = user_obj.get("join_date")
    if not join_date:
        join_date = user_obj.get("created_at")  # fallback
    if isinstance(join_date, str):
        join_date = datetime.strptime(join_date, "%Y-%m-%d").date()
    else:
        join_date = join_date.date()  # if stored as datetime

    today = datetime.utcnow().date()
    start_month = max(join_date, today.replace(day=1))

    # Fetch all completed sessions in current month
    sessions_cursor = db.sessions.find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_month.strftime("%Y-%m-%d"), "$lte": today.strftime("%Y-%m-%d")},
        "completion_status": "Completed"  # <-- only completed sessions
    })
    sessions = list(sessions_cursor)

    # Build set of days user studied (date objects)
    studied_days = set()
    for s in sessions:
        date_str = s.get("date")
        if not date_str:
            continue
        try:
            studied_days.add(datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            continue

    # Daily streak: consecutive days ending today
    streak = 0
    day_check = today
    while day_check in studied_days:
        streak += 1
        day_check -= timedelta(days=1)

    # Days missed: total days from start_month to today minus studied_days
    total_days = (today - start_month).days + 1
    missed = total_days - len(studied_days)

    message = f"You've studied {streak} day{'s' if streak != 1 else ''} in a row! Keep it going!"

    return {"streak": streak, "missed": missed, "message": message}
