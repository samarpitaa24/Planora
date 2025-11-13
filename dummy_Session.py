# scripts/create_dummy_sessions.py
from datetime import datetime, timedelta
import random
from planora_app.extensions import get_db

USER_ID = "6914d21e49ea9a6e4be9108c"

# Subjects available for Alice
SUBJECTS = ["Math", "Physics", "Chemistry", "English","Biology"]

# Cycles and timer options
CYCLE_OPTIONS = [1, 2, 3, 4]
TIMER_OPTIONS = [15, 20, 25]
BREAK_OPTIONS = [5, 10]

def generate_dummy_sessions():
    db = get_db()
    sessions = []

    today = datetime.utcnow()
    # Generate logs for past 15 days
    for day in range(15):
        session_date = today - timedelta(days=day)
        # 1–2 sessions per day
        for _ in range(random.randint(1, 2)):
            subject = random.choice(SUBJECTS)
            cycles = random.choice(CYCLE_OPTIONS)
            completed = random.randint(0, cycles)
            timer = random.choice(TIMER_OPTIONS)
            break_time = random.choice(BREAK_OPTIONS)
            pause_count = random.randint(0, 3)

            # Random start time within the day
            start_hour = random.randint(6, 22)
            start_minute = random.choice([0, 15, 30, 45])
            start_time = session_date.replace(
                hour=start_hour, minute=start_minute, second=0, microsecond=0
            )

            # End time = start + cycles × (timer + break)
            total_minutes = cycles * timer + (cycles - 1) * break_time
            end_time = start_time + timedelta(minutes=total_minutes)

            session = {
                "user_id": USER_ID,
                "subject": subject,
                "start_time": start_time,
                "end_time": end_time,
                "no_of_cycles_decided": cycles,
                "no_of_cycles_completed": completed,
                "break_time": break_time,
                "pause_count": pause_count,
                "timer_per_cycle": timer,
                "completion_status": "Completed" if completed == cycles else "Incomplete",
                "date": session_date.date().isoformat()
            }
            sessions.append(session)

    if sessions:
        db.sessions.insert_many(sessions)
        print(f"Inserted {len(sessions)} dummy sessions for user {USER_ID}.")
    else:
        print("No sessions generated.")

if __name__ == "__main__":
    generate_dummy_sessions()
