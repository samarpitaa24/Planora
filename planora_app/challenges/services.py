
import datetime
import pytz

from planora_app.dashboard.cards_services import get_priority_focus
from planora_app.extensions import get_db

IST = pytz.timezone("Asia/Kolkata")

# Master list of challenges
ALL_CHALLENGES = [
    {
        "sequence": 1,
        "id": "ch1",
        "title": "5 Pomodoro Cycles",
        "badge_name": "Pomodoro Pro",
    },
    {
        "sequence": 2,
        "id": "ch2",
        "title": "Study Neglected Subject",
        "badge_name": "Focus Finder",
    },
    {
        "sequence": 3,
        "id": "ch3",
        "title": "3 Day Streak",
        "badge_name": "Streak Keeper",
    },
    {
        "sequence": 4,
        "id": "ch4",
        "title": "10 Pomodoro Cycles",
        "badge_name": "Deep Worker",
    },
    {
        "sequence": 5,
        "id": "ch5",
        "title": "5 Day Streak",
        "badge_name": "Consistency Master",
    },
    {
        "sequence": 6,
        "id": "ch6",
        "title": "Study 3 Different Subjects",
        "badge_name": "Knowledge Explorer",
    }
]


def get_current_ist_date():
    """Return the current date (IST)."""
    return datetime.datetime.now(IST).date()


def to_datetime(d):
    """Convert date -> datetime for MongoDB storage."""
    if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
        return datetime.datetime.combine(
            d,
            datetime.time.min,
            tzinfo=IST,
        )
    return d




# ✅ Ensures weekly challenges always exist
def assign_challenges_for_week(db, user_id):
    today = get_current_ist_date()
    coll = db["challenges"]

    print("\n========== CHALLENGE FUNCTION STARTED ==========")
    print("User ID received:", user_id)
    print("User ID type:", type(user_id))

    

    print(f"Current Tier = {tier}")

    for c in CHALLENGE_TIERS[tier]:
        print(f"\nChecking challenge {c['id']} for user {user_id}")

        existing = coll.find_one(
            {
                "user_id": user_id,
                "challenge_id": c["id"],
            }
        )

        if existing:
            print(f"Challenge {c['id']} already exists.")
            continue

        expected_subject = None

        if c["id"] == "ch2":
            try:
                pf = get_priority_focus(db, user_id)

                if pf and isinstance(pf, dict):
                    expected_subject = pf.get("subject")

            except Exception as e:
                print(
                    f"[assign_challenges_for_week] Could not get priority focus: {e}"
                )

                # Set a default subject if priority focus fails
                expected_subject = "Not Set"

        doc = {
            "user_id": user_id,
            "challenge_id": c["id"],
            "challenge_name": c["title"],
            "badge_name": c["badge_name"],
            "status": "not started",
            "progress": 0,
            "week_start": to_datetime(today),
            "streak_count": 0 if c["id"] == "ch3" else None,
            "expected_subject": expected_subject,
            "created_at": datetime.datetime.now(IST),
            "last_updated": datetime.datetime.now(IST),
        }

        print("Inserting challenge:", doc)

        coll.insert_one(doc)

        print(
            f"✅ Inserted challenge: {c['title']} for user {user_id}"
        )

    return True


# ✅ Update streak progress
def update_3day_streak(db, user_id):
    coll = db["challenges"]
    today = get_current_ist_date()

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch3",
        }
    )

    if not ch or ch.get("status") == "completed":
        return

    last_update = ch.get("last_updated")

    last_date = (
        last_update.astimezone(IST).date()
        if last_update
        else None
    )

    streak_count = ch.get("streak_count", 0)

    if last_date != today:
        streak_count += 1

        status = (
            "in progress"
            if streak_count < 3
            else "completed"
        )

        progress = int((streak_count / 3) * 100)

        coll.update_one(
            {"_id": ch["_id"]},
            {
                "$set": {
                    "streak_count": streak_count,
                    "status": status,
                    "progress": progress,
                    "last_updated": datetime.datetime.now(IST),
                }
            },
        )

        print(
            f"✅ Updated streak: {streak_count}/3 days for user {user_id}"
        )


# ✅ Update Pomodoro challenge
def update_5pomodoro(db, user_id):
    coll = db["challenges"]

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch1",
        }
    )

    if not ch or ch.get("status") == "completed":
        return

    start_date = (
        ch.get("week_start")
        or to_datetime(get_current_ist_date())
    )

    try:
        # ✅ FIXED: Use count_documents()
        count = db.sessions.count_documents(
            {
                "user_id": user_id,
                "start_time": {"$gte": start_date},
            }
        )

        print(
            f"📊 Found {count} pomodoro sessions for user {user_id}"
        )

    except Exception as e:
        print(
            f"[update_5pomodoro] Error querying sessions: {e}"
        )

        count = 0

    progress = min(int((count / 5) * 100), 100)

    status = (
        "completed"
        if count >= 5
        else (
            "in progress"
            if count > 0
            else "not started"
        )
    )

    coll.update_one(
        {"_id": ch["_id"]},
        {
            "$set": {
                "progress": progress,
                "status": status,
                "last_updated": datetime.datetime.now(IST),
            }
        },
    )

    print(
        f"✅ Updated Pomodoro challenge: "
        f"{count}/5 sessions, {progress}% complete"
    )


# ✅ Update Neglected Subject challenge
def update_study_neglected(db, user_id):
    coll = db["challenges"]

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch2",
        }
    )

    if not ch or ch.get("status") == "completed":
        return

    start_date = (
        ch.get("week_start")
        or to_datetime(get_current_ist_date())
    )

    subject = ch.get("expected_subject")

    if not subject:
        print(
            "⚠️ No expected subject set for neglected subject challenge"
        )
        return

    try:
        # ✅ FIXED: Use count_documents()
        count = db.sessions.count_documents(
            {
                "user_id": user_id,
                "subject": subject,
                "start_time": {"$gte": start_date},
            }
        )

        print(
            f"📊 Found {count} sessions for subject "
            f"'{subject}' for user {user_id}"
        )

    except Exception as e:
        print(
            f"[update_study_neglected] Error querying sessions: {e}"
        )

        count = 0

    status = (
        "completed"
        if count >= 1
        else "not started"
    )

    progress = 100 if count >= 1 else 0

    coll.update_one(
        {"_id": ch["_id"]},
        {
            "$set": {
                "progress": progress,
                "status": status,
                "last_updated": datetime.datetime.now(IST),
            }
        },
    )

    print(
        f"✅ Updated Neglected Subject challenge: {status}"
    )


# Complete 10 Pomodoro Sessions
def update_10pomodoro(db, user_id):

    coll = db["challenges"]

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch4",
        }
    )

    if not ch:
        return

    count = db.sessions.count_documents(
        {
            "user_id": user_id
        }
    )

    progress = min(
        int((count / 10) * 100),
        100
    )

    status = (
        "completed"
        if count >= 10
        else "in progress"
    )

    coll.update_one(
        {"_id": ch["_id"]},
        {
            "$set": {
                "progress": progress,
                "status": status,
                "last_updated": datetime.datetime.now(IST),
            }
        },
    )

# Maintain 5 Day Streak

def update_5day_streak(db, user_id):

    coll = db["challenges"]

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch5",
        }
    )

    if not ch:
        return

    streak = ch.get("streak_count", 0)

    if streak >= 5:

        coll.update_one(
            {"_id": ch["_id"]},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100
                }
            }
        )

# Study 3 Different Subjects

def update_3subjects(db, user_id):

    coll = db["challenges"]

    ch = coll.find_one(
        {
            "user_id": user_id,
            "challenge_id": "ch6",
        }
    )

    if not ch:
        return

    pipeline = [
        {
            "$match": {
                "user_id": user_id
            }
        },
        {
            "$group": {
                "_id": "$subject"
            }
        }
    ]

    subjects = list(
        db.sessions.aggregate(pipeline)
    )

    count = len(subjects)

    progress = min(
        int((count / 3) * 100),
        100
    )

    status = (
        "completed"
        if count >= 3
        else "in progress"
    )

    coll.update_one(
        {"_id": ch["_id"]},
        {
            "$set": {
                "progress": progress,
                "status": status,
                "last_updated": datetime.datetime.now(IST),
            }
        },
    )


# ✅ Master updater
def update_all_challenges(db, user_id):
    print(
        f"🔄 Updating all challenges for user {user_id}"
    )

    assign_challenges_for_week(db, user_id)
    update_3day_streak(db, user_id)
    update_5pomodoro(db, user_id)
    update_study_neglected(db, user_id)
    update_10pomodoro(db, user_id)
    update_5day_streak(db, user_id)
    update_3subjects(db, user_id)

    print(
        f"✅ Finished updating all challenges for user {user_id}"
    )


# ✅ API data fetcher
def get_user_challenges(db, user_id):
    update_all_challenges(db, user_id)

    coll = db["challenges"]

    tier = get_current_tier(db, user_id)

    active_ids = [
        ch["id"]
        for ch in CHALLENGE_TIERS[tier]
    ]

    docs = list(
        coll.find(
            {
                "user_id": user_id,
                "challenge_id": {"$in": active_ids}
            },
            {"_id": 0}
        )
    )

    # Convert all date/datetime fields to ISO string
    for doc in docs:
        for field in [
            "week_start",
            "created_at",
            "last_updated",
        ]:
            if field in doc and doc[field]:
                if isinstance(
                    doc[field],
                    (datetime.date, datetime.datetime),
                ):
                    doc[field] = doc[field].isoformat()

    print(
        f"📤 Returning {len(docs)} challenges for user {user_id}"
    )

    return docs