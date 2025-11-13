from planora_app.extensions import get_db
from datetime import datetime, timedelta
from bson import ObjectId
import pytz

def get_user_sessions(user_id: str, filter_type=None, filter_value=None):
    db = get_db()
    query = {"user_id": user_id}
    
    # Define IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    today_ist = datetime.now(ist).date()

    if filter_type and filter_value:
        if filter_type == "date":
            try:
                dt = datetime.strptime(filter_value, "%Y-%m-%d")
                # Create IST-aware datetime for the start and end of the day
                start_of_day = ist.localize(datetime(dt.year, dt.month, dt.day, 0, 0, 0))
                end_of_day = ist.localize(datetime(dt.year, dt.month, dt.day, 23, 59, 59))
                query["start_time"] = {"$gte": start_of_day, "$lte": end_of_day}
            except:
                pass
        elif filter_type == "month":
            try:
                month = int(filter_value)
                # Get the last day of the month
                if month == 12:
                    next_month = ist.localize(datetime(today_ist.year + 1, 1, 1))
                else:
                    next_month = ist.localize(datetime(today_ist.year, month + 1, 1))
                
                start_of_month = ist.localize(datetime(today_ist.year, month, 1))
                query["start_time"] = {"$gte": start_of_month, "$lt": next_month}
            except:
                pass
        elif filter_type == "year":
            try:
                year = int(filter_value)
                start_of_year = ist.localize(datetime(year, 1, 1))
                end_of_year = ist.localize(datetime(year, 12, 31, 23, 59, 59))
                query["start_time"] = {"$gte": start_of_year, "$lte": end_of_year}
            except:
                pass
        elif filter_type == "subject":
            # Case-insensitive subject filter
            query["subject"] = {"$regex": f"^{filter_value}$", "$options": "i"}

    sessions_cursor = db.sessions.find(query).sort("start_time", -1)
    session_list = []

    for sess in sessions_cursor:
        start_time = sess.get("start_time")
        end_time = sess.get("end_time")
        
        # Convert to IST if the datetime has timezone info
        if start_time:
            if start_time.tzinfo is None:
                # If no timezone, assume UTC and convert to IST
                start_time = pytz.UTC.localize(start_time).astimezone(ist)
            else:
                # If has timezone, convert to IST
                start_time = start_time.astimezone(ist)
        
        if end_time:
            if end_time.tzinfo is None:
                # If no timezone, assume UTC and convert to IST
                end_time = pytz.UTC.localize(end_time).astimezone(ist)
            else:
                # If has timezone, convert to IST
                end_time = end_time.astimezone(ist)

        # Get total_time from the document (it's in minutes)
        total_time_mins = sess.get("total_time", 0)
        
        # Format time display
        if total_time_mins >= 60:
            hours = total_time_mins // 60
            mins = total_time_mins % 60
            if mins > 0:
                studied_time_str = f"{hours}h {mins}m"
            else:
                studied_time_str = f"{hours}h"
        else:
            studied_time_str = f"{total_time_mins}m"
        
        # Get cycle counts
        decided_cycles = sess.get("no_of_cycles_decided", 0)
        completed_cycles = sess.get("no_of_cycles_completed", 0)

        session_list.append({
            "_id": str(sess["_id"]),
            "subject": sess.get("subject", ""),
            "studied_time": studied_time_str,
            "total_time_mins": total_time_mins,
            "date": start_time.strftime("%Y-%m-%d") if start_time else "",
            "start_time": start_time.strftime("%I:%M %p") if start_time else "",  # 12-hour format with AM/PM
            "end_time": end_time.strftime("%I:%M %p") if end_time else "",
            "completed_cycles": completed_cycles,
            "decided_cycles": decided_cycles,
            "cycles": f"{completed_cycles}/{decided_cycles}",
            "completion_status": sess.get("completion_status", ""),
            "pause_count": sess.get("pause_count", 0),
            "break_time": sess.get("break_time", 0),
            "timer_per_cycle": sess.get("timer_per_cycle", 0)
        })

    return session_list