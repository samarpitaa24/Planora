# planora_app/tasks/task_services.py
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional

def _serialize_task(doc: dict) -> dict:
    """Convert Mongo task document to JSON-serializable dict."""
    if not doc:
        return None
    doc = dict(doc)  # shallow copy
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("deadline"), datetime):
        doc["deadline"] = doc["deadline"].isoformat()
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if isinstance(doc.get("updated_at"), datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc

def create_task(db, user_id: str, name: str, deadline_str: Optional[str], priority: Optional[str], duration: Optional[str]):
    if not name or name.strip() == "":
        raise ValueError("task name is required")

    # parse deadline if provided (expects datetime-local string: YYYY-MM-DDTHH:MM)
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str)
        except Exception:
            # last resort: try to split and replace space
            try:
                deadline = datetime.fromisoformat(deadline_str.replace(" ", "T"))
            except Exception:
                raise ValueError("deadline format invalid")

    duration_val = None
    if duration is not None and duration != "":
        try:
            duration_val = float(duration)
        except Exception:
            raise ValueError("duration must be a number (hours)")

    now = datetime.utcnow()
    if deadline is not None and deadline < now:
        raise ValueError("Deadline must be in the future")

    normalized_name = name.strip()
    duplicate_query = {
        "user_id": str(user_id),
        "name": normalized_name,
        "deadline": deadline,
    }
    if db.tasks.find_one(duplicate_query):
        raise ValueError("A task with the same name and deadline already exists")

    task_doc = {
        "user_id": str(user_id),
        "name": normalized_name,
        "priority": priority or "Medium",
        "duration": duration_val,
        "deadline": deadline,
        "completed": False,
        "created_at": now,
        "updated_at": now,
    }

    result = db.tasks.insert_one(task_doc)
    task_doc["_id"] = str(result.inserted_id)
    # convert datetimes to iso for JSON return
    if deadline:
        task_doc["deadline"] = deadline.isoformat()
    task_doc["created_at"] = now.isoformat()
    task_doc["updated_at"] = now.isoformat()
    return task_doc

def get_tasks_for_user(db, user_id: str):
    cursor = db.tasks.find({"user_id": str(user_id)})
    tasks = []
    for doc in cursor:
        tasks.append(_serialize_task(doc))
    return tasks

def update_task(db, task_id: str, user_id: str, data: dict):
    query = {"_id": ObjectId(task_id), "user_id": str(user_id)}
    set_fields = {}

    if "name" in data and data["name"] is not None:
        if data["name"].strip() == "":
            raise ValueError("task name cannot be empty")
        set_fields["name"] = data["name"].strip()

    if "priority" in data and data["priority"] is not None:
        set_fields["priority"] = data["priority"]

    if "duration" in data:
        dur = data.get("duration")
        if dur in (None, ""):
            set_fields["duration"] = None
        else:
            try:
                set_fields["duration"] = float(dur)
            except Exception:
                raise ValueError("duration must be a number")

    if "deadline" in data:
        dl = data.get("deadline")
        if not dl:
            set_fields["deadline"] = None
        else:
            try:
                set_fields["deadline"] = datetime.fromisoformat(dl)
            except Exception:
                try:
                    set_fields["deadline"] = datetime.fromisoformat(dl.replace(" ", "T"))
                except Exception:
                    raise ValueError("deadline format invalid")

    if "completed" in data:
        set_fields["completed"] = bool(data.get("completed"))

    if not set_fields:
        raise ValueError("no valid fields to update")

    # Prevent duplicate tasks with the same name and deadline for this user.
    if "name" in set_fields or "deadline" in set_fields:
        existing = db.tasks.find_one({"_id": ObjectId(task_id), "user_id": str(user_id)})
        if not existing:
            raise ValueError("task not found or not owned by user")

        new_name = set_fields.get("name", existing.get("name"))
        new_deadline = set_fields.get("deadline", existing.get("deadline"))

        duplicate = db.tasks.find_one(
            {
                "user_id": str(user_id),
                "name": new_name,
                "deadline": new_deadline,
                "_id": {"$ne": ObjectId(task_id)},
            }
        )
        if duplicate:
            raise ValueError("A task with the same name and deadline already exists")

    set_fields["updated_at"] = datetime.utcnow()

    res = db.tasks.update_one(query, {"$set": set_fields})
    if res.matched_count == 0:
        raise ValueError("task not found or not owned by user")

    updated = db.tasks.find_one({"_id": ObjectId(task_id)})
    return _serialize_task(updated)

def delete_task(db, task_id: str, user_id: str):
    res = db.tasks.delete_one({"_id": ObjectId(task_id), "user_id": str(user_id)})
    return res.deleted_count

def toggle_task_complete(db, task_id: str, user_id: str, completed: bool):
    return update_task(db, task_id, user_id, {"completed": bool(completed)})

# ---------------- Dashboard: Top 3 Upcoming Tasks ----------------
def _priority_rank(priority: str) -> int:
    order = {"High": 0, "Medium": 1, "Low": 2}
    return order.get(priority or "Medium", 3)


def _task_sort_key(task: dict):
    priority_rank = _priority_rank(task.get("priority"))
    duration = task.get("duration")
    duration_value = float(duration) if duration is not None else float("inf")
    deadline = task.get("deadline")
    deadline_value = deadline if isinstance(deadline, datetime) else datetime.max
    return (priority_rank, duration_value, deadline_value)


def get_top_tasks_for_user(db, user_id: str, limit: int = 3):
    """Return top upcoming / prioritized tasks for dashboard."""
    now = datetime.utcnow()
    docs = [
        doc
        for doc in db.tasks.find({"user_id": str(user_id), "completed": False})
        if doc.get("deadline") is None or doc.get("deadline") >= now
    ]
    docs.sort(key=_task_sort_key)
    tasks = [_serialize_task(doc) for doc in docs[:limit]]
    return tasks