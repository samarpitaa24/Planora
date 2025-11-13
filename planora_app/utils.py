# planora_app/utils.py
from datetime import datetime, timezone
from bson import ObjectId
from planora_app.extensions import get_db

def check_and_update_quota(user_id: str, tokens_needed: int) -> bool:
    db = get_db()

    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)

    user = db.users.find_one({"_id": user_id})
    if not user:
        print("❌ User not found:", user_id)
        return False

    now_utc = datetime.now(timezone.utc)
    last_reset = user.get("quota_last_reset")

    if not last_reset or now_utc.date() > last_reset.date():
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"tokens_used": 0, "quota_last_reset": now_utc}}
        )
        user["tokens_used"] = 0

    if user.get("tokens_used", 0) + tokens_needed > user.get("daily_quota", 0):
        print(f"❌ Quota exceeded: used={user.get('tokens_used', 0)}, "
              f"needed={tokens_needed}, quota={user.get('daily_quota', 0)}")
        return False

    db.users.update_one(
        {"_id": user_id},
        {"$inc": {"tokens_used": tokens_needed}}
    )
    return True
