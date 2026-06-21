from datetime import datetime, timedelta, timezone
from planora_app.extensions import get_db

USER_ID = "6a32d001819b846cfbfd8a44"

db = get_db()


def clear_sessions():
    db.sessions.delete_many({"user_id": USER_ID})
    print("Old sessions deleted")


def add_session(
    subject,
    days_ago,
    start_hour,
    duration_minutes,
    completed=True
):
    start_time = (
        datetime.now(timezone.utc)
        - timedelta(days=days_ago)
    ).replace(
        hour=start_hour,
        minute=0,
        second=0,
        microsecond=0
    )

    end_time = start_time + timedelta(
        minutes=duration_minutes
    )

    session = {
        "user_id": USER_ID,
        "subject": subject,

        "start_time": start_time,
        "end_time": end_time,

        "total_time": duration_minutes,

        "no_of_cycles_decided": 4,
        "no_of_cycles_completed": 4 if completed else 0,

        "break_time": 5,
        "pause_count": 0,
        "timer_per_cycle": 20,

        "completion_status":
            "Completed"
            if completed
            else "Not Completed",

        "date": start_time.date().isoformat(),

        "created_at": datetime.now(timezone.utc)
    }

    db.sessions.insert_one(session)


print("Ready")

# -------------------------
# TEST CASE 2
# -------------------------

# clear_sessions()

# for i in range(15):
#     add_session(
#         subject="Math",
#         days_ago=i,
#         start_hour=8,
#         duration_minutes=120
#     )

# print("Inserted test case 2")




# -------------------------
# TEST CASE 3
# -------------------------
# clear_sessions()

# # Math - yesterday
# add_session(
#     subject="Math",
#     days_ago=1,
#     start_hour=8,
#     duration_minutes=120
# )

# # English - 2 days ago
# add_session(
#     subject="English",
#     days_ago=2,
#     start_hour=8,
#     duration_minutes=120
# )

# # Physics - 8 days ago
# add_session(
#     subject="Physics",
#     days_ago=8,
#     start_hour=8,
#     duration_minutes=120
# )

# print("Inserted test case 3")

#TEST CASE 4 
# clear_sessions()

# # Math - 10 sessions
# for i in range(10):
#     add_session(
#         subject="Math",
#         days_ago=i % 3,
#         start_hour=8,
#         duration_minutes=120
#     )

# # Physics - 8 sessions
# for i in range(8):
#     add_session(
#         subject="Physics",
#         days_ago=i % 3,
#         start_hour=10,
#         duration_minutes=120
#     )

# # English - only 2 sessions
# for i in range(2):
#     add_session(
#         subject="English",
#         days_ago=i % 2,
#         start_hour=12,
#         duration_minutes=120
#     )

# print("Inserted test case 4")


#TEST CASE 5

clear_sessions()

for i in range(5):
    add_session(
        subject="Math",
        days_ago=i,
        start_hour=8,
        duration_minutes=120
    )

for i in range(5):
    add_session(
        subject="Physics",
        days_ago=i,
        start_hour=11,
        duration_minutes=120
    )

for i in range(5):
    add_session(
        subject="English",
        days_ago=i,
        start_hour=14,
        duration_minutes=120
    )

print("Inserted test case 5")