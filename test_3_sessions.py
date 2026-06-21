from datetime import datetime, timedelta
from planora_app.extensions import get_db

USER_ID = "6a32d001819b846cfbfd8a44"

db = get_db()

# Clear old sessions
db.sessions.delete_many({
    "user_id": USER_ID
})

sessions = []

for i in range(15):

    session_date = datetime.utcnow() - timedelta(days=i)

    start_time = session_date.replace(
        hour=7,
        minute=0,
        second=0,
        microsecond=0
    )

    end_time = session_date.replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0
    )

    sessions.append({
        "user_id": USER_ID,
        "subject": "Math",
        "start_time": start_time,
        "end_time": end_time,
        "completion_status": "Completed",
        "date": session_date.date().isoformat()
    })

db.sessions.insert_many(sessions)

print(f"Inserted {len(sessions)} sessions")