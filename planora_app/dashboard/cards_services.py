# planora_app/dashboard/cards_services.py
from datetime import datetime, timedelta, timezone
from collections import Counter
import platform
from bson import ObjectId
from planora_app.extensions import get_db

import pytz
IST = pytz.timezone("Asia/Kolkata")

# configuration
BUCKET_MINUTES = 15                 # bucket granularity
BUCKETS_PER_DAY = 24 * 60 // BUCKET_MINUTES  # 96
MIN_SESSIONS_REQUIRED = 5
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


def _preferred_time_from_qna(user_doc: dict):
    qna = user_doc.get("qna", {}) or {}

    preferred_time = qna.get("preferred_study_time")

    if preferred_time:
        start = preferred_time.get("start")
        end = preferred_time.get("end")

        if start and end:
            try:
                start_dt = datetime.strptime(start, "%H:%M")
                end_dt = datetime.strptime(end, "%H:%M")

                start_str = start_dt.strftime("%I:%M %p").lstrip("0")
                end_str = end_dt.strftime("%I:%M %p").lstrip("0")

                return f"{start_str} – {end_str}"

            except Exception:
                pass

    return "Start a few study sessions"




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
        return {
        "best_time": pref,
        "source": "preference"
    }
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
        return {
        "best_time": pref,
        "source": "preference"
    }

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

    result = {
    "best_time": f"{start_str} to {end_str}",
    "source": "sessions"
    }
    
    if debug:
        result["sessions_used"] = session_times
        result["bucket_counts"] = buckets

    return result

#SUBJECT RECOMMENDATION 

def get_priority_focus(user_id: str) -> dict:

    db = get_db()

    try:
        user_obj = db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return {
            "subject": "Invalid user",
            "reason": "User ID format is incorrect",
            "source": "error"
        }

    if not user_obj:
        return {
            "subject": "No user found",
            "reason": "Start using Planora to get recommendations",
            "source": "error"
        }

    subjects = user_obj.get("qna", {}).get("subjects", [])

    # CASE 1 : No subjects configured
    if not subjects:
        return {
            "subject": "No subjects",
            "reason": "Please add subjects in preferences",
            "source": "empty"
        }

    # Only consider recent history
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

    sessions = list(
        db.sessions.find({
            "user_id": user_id,
            "completion_status": "Completed",
            "start_time": {"$gte": cutoff_date}
        })
    )

    # CASE 2 : New user
    if not sessions:
        return {
            "subject": subjects[0],
            "reason": "Start building momentum with one of your selected subjects",
            "source": "new_user"
        }

    # Build statistics
    subject_stats = {
        subject: {
            "minutes": 0,
            "sessions": 0,
            "last_studied": None
        }
        for subject in subjects
    }

    for session in sessions:

        subject = session.get("subject")

        if subject not in subject_stats:
            continue

        start = session.get("start_time")
        end = session.get("end_time")

        if not start or not end:
            continue

        minutes = max(
            int((end - start).total_seconds() / 60),
            0
        )

        subject_stats[subject]["minutes"] += minutes
        subject_stats[subject]["sessions"] += 1

        last_date = start.date()

        if (
            subject_stats[subject]["last_studied"] is None
            or last_date > subject_stats[subject]["last_studied"]
        ):
            subject_stats[subject]["last_studied"] = last_date

    # CASE 3 : Never studied subjects
    never_studied = [
        s for s, stats in subject_stats.items()
        if stats["sessions"] == 0
    ]

    if never_studied:
        subject = never_studied[0]

        return {
            "subject": subject,
            "reason": f"You haven't studied {subject} yet",
            "source": "never_studied"
        }

    today = datetime.now(timezone.utc).date()

    # CASE 4 : Neglected subjects
    neglected_subject = None
    max_days = -1

    for subject, stats in subject_stats.items():

        days_since = (
            today - stats["last_studied"]
        ).days

        if days_since > max_days:
            max_days = days_since
            neglected_subject = subject

    if max_days >= 3:
        return {
            "subject": neglected_subject,
            "reason": f"Last studied {max_days} days ago",
            "source": "neglected"
        }

    # CASE 5 : Under-studied subjects
    minute_values = [
        stats["minutes"]
        for stats in subject_stats.values()
    ]

    max_minutes = max(minute_values)
    min_minutes = min(minute_values)

    # Balanced threshold = 20%
    if max_minutes > 0:

        difference_ratio = (
            (max_minutes - min_minutes)
            / max_minutes
        )

        if difference_ratio <= 0.20:
            return {
                "subject": "All subjects balanced",
                "reason": "Keep up your study rhythm!",
                "source": "balanced"
            }

    under_studied_subject = min(
        subject_stats.items(),
        key=lambda item: (
            item[1]["minutes"],
            item[1]["sessions"]
        )
    )[0]

    return {
        "subject": under_studied_subject,
        "reason": f"You've spent less time on {under_studied_subject} recently",
        "source": "under_studied"
    }

#streaks 

def get_daily_streak(user_id: str):
    """
    Lazy Daily Streak Update.

    Updates streak only when:
    - dashboard is opened
    - today's streak has not already been updated
    - user has at least one Completed or Partially Completed session today

    Afterwards only returns stored values.
    """

    db = get_db()

    try:
        user = db.users.find_one(
            {
                "_id": ObjectId(user_id)
            }
        )

    except Exception:

        return {
            "current_streak": 0,
            "highest_streak": 0,
            "message": "Invalid user"
        }

    if not user:

        return {
            "current_streak": 0,
            "highest_streak": 0,
            "message": "User not found"
        }

    current_streak = user.get("current_streak", 0)
    highest_streak = user.get("highest_streak", 0)
    last_update = user.get("last_streak_update")

    today = datetime.now(IST).date()
    today_str = today.strftime("%Y-%m-%d")

    # Already updated today
    if last_update == today_str:

        return {
            "current_streak": current_streak,
            "highest_streak": highest_streak,
            "message": f"🔥 {current_streak} day streak!"
        }

    # Check if user studied today
    session = db.sessions.find_one(
        {
            "user_id": user_id,
            "date": today_str,
            "completion_status": {
                "$in": [
                    "Completed",
                    "Partially Completed"
                ]
            }
        }
    )

    # No qualifying session today
    if not session:

        return {
            "current_streak": current_streak,
            "highest_streak": highest_streak,
            "message": "Complete a study session today!"
        }

    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if last_update == yesterday:

        current_streak += 1

    else:

        current_streak = 1

    if current_streak > highest_streak:

        highest_streak = current_streak

    db.users.update_one(

        {
            "_id": ObjectId(user_id)
        },

        {
            "$set": {

                "current_streak": current_streak,
                "highest_streak": highest_streak,
                "last_streak_update": today_str

            }
        }

    )

    return {

        "current_streak": current_streak,
        "highest_streak": highest_streak,
        "message": f"🔥 {current_streak} day streak!"

    }