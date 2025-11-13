from planora_app.extensions import get_db
from datetime import datetime, timedelta
from bson import ObjectId
import pytz

class TimerService:
    """Service class for timer-related database operations"""
    
    @staticmethod
    def save_session(session_data):
        """
        Save a pomodoro session to the sessions collection
        
        Args:
            session_data (dict): Session information containing:
                - user_id: User identifier (username or ObjectId string)
                - subject: Subject studied
                - start_time: Session start timestamp (ISO string in IST)
                - end_time: Session end timestamp (ISO string in IST)
                - total_time: Total study time in minutes
                - no_of_cycles_decided: Total number of cycles decided
                - no_of_cycles_completed: Number of completed cycles
                - break_time: Break time in minutes
                - pause_count: Number of times paused
                - timer_per_cycle: Time per cycle in minutes
                - completion_status: "Completed", "Not Completed", or "Partially Completed"
                - date: Date string in YYYY-MM-DD format (IST)
        
        Returns:
            dict: Result with success status and session_id or error
        """
        try:
            db = get_db()
            
            # Define IST timezone
            ist = pytz.timezone('Asia/Kolkata')
            
            # Parse datetime strings (they come as IST from client)
            start_time_str = session_data['start_time']
            end_time_str = session_data['end_time']
            
            # Parse as naive datetime first
            start_time_naive = datetime.fromisoformat(start_time_str)
            end_time_naive = datetime.fromisoformat(end_time_str)
            
            # Localize to IST (treat as IST time)
            start_time_ist = ist.localize(start_time_naive)
            end_time_ist = ist.localize(end_time_naive)
            
            # Store in MongoDB with timezone info (keep as IST)
            # MongoDB will store it properly with timezone
            
            # Get user_id - convert to string for consistency
            user_id = str(session_data['user_id'])
            
            # Prepare session document for sessions collection
            session_doc = {
                "user_id": user_id,
                "subject": session_data['subject'],
                "start_time": start_time_ist,  # Store with IST timezone
                "end_time": end_time_ist,      # Store with IST timezone
                "total_time": int(session_data['total_time']),  # in minutes
                "no_of_cycles_decided": int(session_data['no_of_cycles_decided']),
                "no_of_cycles_completed": int(session_data['no_of_cycles_completed']),
                "break_time": int(session_data['break_time']),
                "pause_count": int(session_data['pause_count']),
                "timer_per_cycle": int(session_data['timer_per_cycle']),
                "completion_status": session_data['completion_status'],
                "date": session_data['date'],
                "created_at": datetime.now(ist)  # Current time in IST
            }
            
            print(f"Saving session with IST times:")
            print(f"  Start (IST): {start_time_ist}")
            print(f"  End (IST): {end_time_ist}")
            print(f"  Date: {session_data['date']}")
            
            # Insert into sessions collection
            result = db.sessions.insert_one(session_doc)
            
            # Update user statistics in users collection
            TimerService._update_user_stats(
                user_id,
                session_data['total_time'],
                session_data['no_of_cycles_completed'],
                session_data['completion_status'] == 'Completed'
            )
            
            return {
                "success": True,
                "session_id": str(result.inserted_id),
                "message": "Session saved successfully"
            }
        
        except Exception as e:
            print(f"Error in save_session: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _update_user_stats(user_id, study_time, cycles_completed, session_completed):
        """
        Update user's study statistics
        """
        try:
            db = get_db()
            ist = pytz.timezone('Asia/Kolkata')
            current_time_ist = datetime.now(ist)
            
            # Store in separate user_stats collection
            db.user_stats.update_one(
                {"user_id": user_id},
                {
                    "$inc": {
                        "total_study_time": study_time,
                        "total_cycles": cycles_completed,
                        "total_sessions": 1,
                        "completed_sessions": 1 if session_completed else 0
                    },
                    "$set": {
                        "last_study_date": current_time_ist,
                        "last_updated": current_time_ist
                    }
                },
                upsert=True
            )
            
            # Update users collection
            update_query = {"username": user_id}
            if ObjectId.is_valid(user_id):
                update_query = {"_id": ObjectId(user_id)}
            
            db.users.update_one(
                update_query,
                {
                    "$set": {
                        "last_study_date": current_time_ist
                    }
                }
            )
        
        except Exception as e:
            print(f"Error updating user stats: {e}")
    
    @staticmethod
    def get_recent_sessions(user_id, limit=10):
        """Get recent sessions for a user from sessions collection"""
        try:
            db = get_db()
            user_id = str(user_id)
            
            sessions = list(db.sessions.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
            
            # Convert ObjectId and datetime to string for JSON serialization
            for session in sessions:
                session['_id'] = str(session['_id'])
                
                # Convert datetime objects to ISO format strings
                if 'start_time' in session and session['start_time']:
                    session['start_time'] = session['start_time'].isoformat()
                
                if 'end_time' in session and session['end_time']:
                    session['end_time'] = session['end_time'].isoformat()
                
                if 'created_at' in session and session['created_at']:
                    session['created_at'] = session['created_at'].isoformat()
            
            return sessions
        
        except Exception as e:
            print(f"Error fetching recent sessions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_session_stats(user_id, days=7):
        """Get session statistics for a user over a period"""
        try:
            db = get_db()
            user_id = str(user_id)
            ist = pytz.timezone('Asia/Kolkata')
            
            # Calculate date range in IST
            end_date_ist = datetime.now(ist)
            start_date_ist = end_date_ist - timedelta(days=days)
            
            # Aggregate statistics from sessions collection
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": start_date_ist, "$lte": end_date_ist}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_sessions": {"$sum": 1},
                        "total_time": {"$sum": "$total_time"},
                        "total_cycles": {"$sum": "$no_of_cycles_completed"},
                        "completed_sessions": {
                            "$sum": {"$cond": [{"$eq": ["$completion_status", "Completed"]}, 1, 0]}
                        },
                        "total_pauses": {"$sum": "$pause_count"}
                    }
                }
            ]
            
            result = list(db.sessions.aggregate(pipeline))
            
            if result:
                stats = result[0]
                stats.pop('_id', None)
                
                # Add additional computed metrics
                if stats['total_sessions'] > 0:
                    stats['avg_time_per_session'] = round(stats['total_time'] / stats['total_sessions'], 1)
                    stats['completion_rate'] = round((stats['completed_sessions'] / stats['total_sessions']) * 100, 1)
                    stats['avg_cycles_per_session'] = round(stats['total_cycles'] / stats['total_sessions'], 1)
                else:
                    stats['avg_time_per_session'] = 0
                    stats['completion_rate'] = 0
                    stats['avg_cycles_per_session'] = 0
                
                return stats
            else:
                return {
                    "total_sessions": 0,
                    "total_time": 0,
                    "total_cycles": 0,
                    "completed_sessions": 0,
                    "total_pauses": 0,
                    "avg_time_per_session": 0,
                    "completion_rate": 0,
                    "avg_cycles_per_session": 0
                }
        
        except Exception as e:
            print(f"Error calculating stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                "total_sessions": 0,
                "total_time": 0,
                "total_cycles": 0,
                "completed_sessions": 0,
                "total_pauses": 0,
                "avg_time_per_session": 0,
                "completion_rate": 0,
                "avg_cycles_per_session": 0
            }
    
    @staticmethod
    def get_subject_breakdown(user_id, days=7):
        """Get study time breakdown by subject"""
        try:
            db = get_db()
            user_id = str(user_id)
            ist = pytz.timezone('Asia/Kolkata')
            
            # Calculate date range in IST
            end_date_ist = datetime.now(ist)
            start_date_ist = end_date_ist - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": start_date_ist, "$lte": end_date_ist}
                    }
                },
                {
                    "$group": {
                        "_id": "$subject",
                        "total_time": {"$sum": "$total_time"},
                        "session_count": {"$sum": 1},
                        "cycles_completed": {"$sum": "$no_of_cycles_completed"}
                    }
                },
                {
                    "$sort": {"total_time": -1}
                }
            ]
            
            results = list(db.sessions.aggregate(pipeline))
            
            # Format results
            breakdown = []
            for item in results:
                breakdown.append({
                    "subject": item['_id'],
                    "total_time": item['total_time'],
                    "session_count": item['session_count'],
                    "cycles_completed": item['cycles_completed'],
                    "avg_time_per_session": round(item['total_time'] / item['session_count'], 1)
                })
            
            return breakdown
        
        except Exception as e:
            print(f"Error getting subject breakdown: {e}")
            return []
    
    @staticmethod
    def calculate_best_time(user_id, days=30):
        """
        Calculate the best study time windows for a user
        """
        try:
            db = get_db()
            user_id = str(user_id)
            ist = pytz.timezone('Asia/Kolkata')
            
            # Get sessions from last 'days' days
            cutoff_date_ist = datetime.now(ist) - timedelta(days=days)
            
            sessions = list(db.sessions.find({
                "user_id": user_id,
                "created_at": {"$gte": cutoff_date_ist}
            }))
            
            if not sessions:
                return {
                    "best_times": [], 
                    "message": "Not enough data. Complete more study sessions to get insights.",
                    "total_sessions_analyzed": 0
                }
            
            # Count sessions by hour of day (in IST)
            hour_data = {}
            for session in sessions:
                # Get hour from start_time (already in IST)
                start_time = session['start_time']
                hour = start_time.hour
                
                if hour not in hour_data:
                    hour_data[hour] = {
                        "count": 0,
                        "total_time": 0,
                        "total_cycles": 0,
                        "completed_count": 0
                    }
                
                hour_data[hour]["count"] += 1
                hour_data[hour]["total_time"] += session['total_time']
                hour_data[hour]["total_cycles"] += session['no_of_cycles_completed']
                if session.get('completion_status') == 'Completed':
                    hour_data[hour]["completed_count"] += 1
            
            # Calculate productivity score for each hour
            best_times = []
            for hour, data in hour_data.items():
                avg_time = data["total_time"] / data["count"]
                avg_cycles = data["total_cycles"] / data["count"]
                completion_rate = (data["completed_count"] / data["count"]) * 100
                
                # Productivity score
                score = (avg_cycles * 4) + (completion_rate * 0.4) + (avg_time / 10)
                
                # Format time slot
                start_hour = hour
                end_hour = (hour + 1) % 24
                time_slot = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                
                # Add period label
                if 5 <= hour < 12:
                    period = "Morning"
                elif 12 <= hour < 17:
                    period = "Afternoon"
                elif 17 <= hour < 21:
                    period = "Evening"
                else:
                    period = "Night"
                
                best_times.append({
                    "hour": hour,
                    "time_slot": time_slot,
                    "period": period,
                    "session_count": data["count"],
                    "avg_time": round(avg_time, 1),
                    "avg_cycles": round(avg_cycles, 1),
                    "completion_rate": round(completion_rate, 1),
                    "productivity_score": round(score, 2)
                })
            
            # Sort by productivity score
            best_times.sort(key=lambda x: x["productivity_score"], reverse=True)
            
            return {
                "best_times": best_times[:5],
                "total_sessions_analyzed": len(sessions),
                "analysis_period_days": days
            }
        
        except Exception as e:
            print(f"Error calculating best time: {e}")
            import traceback
            traceback.print_exc()
            return {
                "best_times": [], 
                "error": str(e),
                "total_sessions_analyzed": 0
            }






# from planora_app.extensions import get_db
# from datetime import datetime, timedelta
# from bson import ObjectId
# import pytz

# class TimerService:
#     """Service class for timer-related database operations"""
    
#     @staticmethod
#     def save_session(session_data):
#         """
#         Save a pomodoro session to the sessions collection
        
#         Args:
#             session_data (dict): Session information containing:
#                 - user_id: User identifier (username or ObjectId string)
#                 - subject: Subject studied
#                 - start_time: Session start timestamp (ISO string without timezone)
#                 - end_time: Session end timestamp (ISO string without timezone)
#                 - total_time: Total study time in minutes
#                 - no_of_cycles_decided: Total number of cycles decided
#                 - no_of_cycles_completed: Number of completed cycles
#                 - break_time: Break time in minutes
#                 - pause_count: Number of times paused
#                 - timer_per_cycle: Time per cycle in minutes
#                 - completion_status: "Completed", "Not Completed", or "Partially Completed"
#                 - date: Date string in YYYY-MM-DD format
        
#         Returns:
#             dict: Result with success status and session_id or error
#         """
#         try:
#             db = get_db()
            
#             # Define IST timezone
#             ist = pytz.timezone('Asia/Kolkata')
            
#             # Parse datetime strings as IST (they come from client's local time)
#             start_time_str = session_data['start_time']
#             end_time_str = session_data['end_time']
            
#             # Parse as naive datetime first
#             start_time_naive = datetime.fromisoformat(start_time_str)
#             end_time_naive = datetime.fromisoformat(end_time_str)
            
#             # Localize to IST (treat as IST time)
#             start_time_ist = ist.localize(start_time_naive)
#             end_time_ist = ist.localize(end_time_naive)
            
#             # Convert to UTC for storage (MongoDB best practice)
#             start_time_utc = start_time_ist.astimezone(pytz.UTC)
#             end_time_utc = end_time_ist.astimezone(pytz.UTC)
            
#             # Get user_id - convert to string for consistency
#             user_id = str(session_data['user_id'])
            
#             # Prepare session document for sessions collection
#             session_doc = {
#                 "user_id": user_id,
#                 "subject": session_data['subject'],
#                 "start_time": start_time_utc,
#                 "end_time": end_time_utc,
#                 "total_time": int(session_data['total_time']),  # in minutes
#                 "no_of_cycles_decided": int(session_data['no_of_cycles_decided']),
#                 "no_of_cycles_completed": int(session_data['no_of_cycles_completed']),
#                 "break_time": int(session_data['break_time']),
#                 "pause_count": int(session_data['pause_count']),
#                 "timer_per_cycle": int(session_data['timer_per_cycle']),
#                 "completion_status": session_data['completion_status'],
#                 "date": session_data['date'],
#                 "created_at": datetime.now(ist).astimezone(pytz.UTC)  # Current time in UTC
#             }
            
#             print(f"Saving session with IST times:")
#             print(f"  Start (IST): {start_time_ist}")
#             print(f"  End (IST): {end_time_ist}")
#             print(f"  Start (UTC stored): {start_time_utc}")
#             print(f"  End (UTC stored): {end_time_utc}")
            
#             # Insert into sessions collection
#             result = db.sessions.insert_one(session_doc)
            
#             # Update user statistics in users collection
#             TimerService._update_user_stats(
#                 user_id,
#                 session_data['total_time'],
#                 session_data['no_of_cycles_completed'],
#                 session_data['completion_status'] == 'Completed'
#             )
            
#             return {
#                 "success": True,
#                 "session_id": str(result.inserted_id),
#                 "message": "Session saved successfully"
#             }
        
#         except Exception as e:
#             print(f"Error in save_session: {e}")
#             import traceback
#             traceback.print_exc()
#             return {
#                 "success": False,
#                 "error": str(e)
#             }
    
#     @staticmethod
#     def _update_user_stats(user_id, study_time, cycles_completed, session_completed):
#         """
#         Update user's study statistics
#         Can be stored in users collection or separate user_stats collection
#         """
#         try:
#             db = get_db()
#             ist = pytz.timezone('Asia/Kolkata')
#             current_time_utc = datetime.now(ist).astimezone(pytz.UTC)
            
#             # Option 1: Store in separate user_stats collection (recommended for analytics)
#             db.user_stats.update_one(
#                 {"user_id": user_id},
#                 {
#                     "$inc": {
#                         "total_study_time": study_time,
#                         "total_cycles": cycles_completed,
#                         "total_sessions": 1,
#                         "completed_sessions": 1 if session_completed else 0
#                     },
#                     "$set": {
#                         "last_study_date": current_time_utc,
#                         "last_updated": current_time_utc
#                     }
#                 },
#                 upsert=True
#             )
            
#             # Option 2: Also update a summary field in users collection (optional)
#             # This makes it easier to display user stats without joining collections
#             update_query = {"username": user_id}
#             if ObjectId.is_valid(user_id):
#                 update_query = {"_id": ObjectId(user_id)}
            
#             db.users.update_one(
#                 update_query,
#                 {
#                     "$set": {
#                         "last_study_date": current_time_utc
#                     }
#                 }
#             )
        
#         except Exception as e:
#             print(f"Error updating user stats: {e}")
    
#     @staticmethod
#     def get_recent_sessions(user_id, limit=10):
#         """Get recent sessions for a user from sessions collection"""
#         try:
#             db = get_db()
#             user_id = str(user_id)
#             ist = pytz.timezone('Asia/Kolkata')
            
#             sessions = list(db.sessions.find(
#                 {"user_id": user_id}
#             ).sort("created_at", -1).limit(limit))
            
#             # Convert ObjectId and datetime to string for JSON serialization
#             # Convert UTC times to IST for display
#             for session in sessions:
#                 session['_id'] = str(session['_id'])
                
#                 # Convert UTC to IST
#                 if 'start_time' in session and session['start_time']:
#                     utc_time = session['start_time'].replace(tzinfo=pytz.UTC)
#                     ist_time = utc_time.astimezone(ist)
#                     session['start_time'] = ist_time.isoformat()
                
#                 if 'end_time' in session and session['end_time']:
#                     utc_time = session['end_time'].replace(tzinfo=pytz.UTC)
#                     ist_time = utc_time.astimezone(ist)
#                     session['end_time'] = ist_time.isoformat()
                
#                 if 'created_at' in session and session['created_at']:
#                     utc_time = session['created_at'].replace(tzinfo=pytz.UTC)
#                     ist_time = utc_time.astimezone(ist)
#                     session['created_at'] = ist_time.isoformat()
            
#             return sessions
        
#         except Exception as e:
#             print(f"Error fetching recent sessions: {e}")
#             import traceback
#             traceback.print_exc()
#             return []
    
#     @staticmethod
#     def get_session_stats(user_id, days=7):
#         """Get session statistics for a user over a period"""
#         try:
#             db = get_db()
#             user_id = str(user_id)
#             ist = pytz.timezone('Asia/Kolkata')
            
#             # Calculate date range in IST, then convert to UTC for query
#             end_date_ist = datetime.now(ist)
#             start_date_ist = end_date_ist - timedelta(days=days)
            
#             # Convert to UTC for MongoDB query
#             end_date_utc = end_date_ist.astimezone(pytz.UTC).replace(tzinfo=None)
#             start_date_utc = start_date_ist.astimezone(pytz.UTC).replace(tzinfo=None)
            
#             # Aggregate statistics from sessions collection
#             pipeline = [
#                 {
#                     "$match": {
#                         "user_id": user_id,
#                         "created_at": {"$gte": start_date_utc, "$lte": end_date_utc}
#                     }
#                 },
#                 {
#                     "$group": {
#                         "_id": None,
#                         "total_sessions": {"$sum": 1},
#                         "total_time": {"$sum": "$total_time"},
#                         "total_cycles": {"$sum": "$no_of_cycles_completed"},
#                         "completed_sessions": {
#                             "$sum": {"$cond": [{"$eq": ["$completion_status", "Completed"]}, 1, 0]}
#                         },
#                         "total_pauses": {"$sum": "$pause_count"}
#                     }
#                 }
#             ]
            
#             result = list(db.sessions.aggregate(pipeline))
            
#             if result:
#                 stats = result[0]
#                 stats.pop('_id', None)
                
#                 # Add additional computed metrics
#                 if stats['total_sessions'] > 0:
#                     stats['avg_time_per_session'] = round(stats['total_time'] / stats['total_sessions'], 1)
#                     stats['completion_rate'] = round((stats['completed_sessions'] / stats['total_sessions']) * 100, 1)
#                     stats['avg_cycles_per_session'] = round(stats['total_cycles'] / stats['total_sessions'], 1)
#                 else:
#                     stats['avg_time_per_session'] = 0
#                     stats['completion_rate'] = 0
#                     stats['avg_cycles_per_session'] = 0
                
#                 return stats
#             else:
#                 return {
#                     "total_sessions": 0,
#                     "total_time": 0,
#                     "total_cycles": 0,
#                     "completed_sessions": 0,
#                     "total_pauses": 0,
#                     "avg_time_per_session": 0,
#                     "completion_rate": 0,
#                     "avg_cycles_per_session": 0
#                 }
        
#         except Exception as e:
#             print(f"Error calculating stats: {e}")
#             import traceback
#             traceback.print_exc()
#             return {
#                 "total_sessions": 0,
#                 "total_time": 0,
#                 "total_cycles": 0,
#                 "completed_sessions": 0,
#                 "total_pauses": 0,
#                 "avg_time_per_session": 0,
#                 "completion_rate": 0,
#                 "avg_cycles_per_session": 0
#             }
    
#     @staticmethod
#     def get_subject_breakdown(user_id, days=7):
#         """Get study time breakdown by subject"""
#         try:
#             db = get_db()
#             user_id = str(user_id)
#             ist = pytz.timezone('Asia/Kolkata')
            
#             # Calculate date range in IST, then convert to UTC
#             end_date_ist = datetime.now(ist)
#             start_date_ist = end_date_ist - timedelta(days=days)
            
#             end_date_utc = end_date_ist.astimezone(pytz.UTC).replace(tzinfo=None)
#             start_date_utc = start_date_ist.astimezone(pytz.UTC).replace(tzinfo=None)
            
#             pipeline = [
#                 {
#                     "$match": {
#                         "user_id": user_id,
#                         "created_at": {"$gte": start_date_utc, "$lte": end_date_utc}
#                     }
#                 },
#                 {
#                     "$group": {
#                         "_id": "$subject",
#                         "total_time": {"$sum": "$total_time"},
#                         "session_count": {"$sum": 1},
#                         "cycles_completed": {"$sum": "$no_of_cycles_completed"}
#                     }
#                 },
#                 {
#                     "$sort": {"total_time": -1}
#                 }
#             ]
            
#             results = list(db.sessions.aggregate(pipeline))
            
#             # Format results
#             breakdown = []
#             for item in results:
#                 breakdown.append({
#                     "subject": item['_id'],
#                     "total_time": item['total_time'],
#                     "session_count": item['session_count'],
#                     "cycles_completed": item['cycles_completed'],
#                     "avg_time_per_session": round(item['total_time'] / item['session_count'], 1)
#                 })
            
#             return breakdown
        
#         except Exception as e:
#             print(f"Error getting subject breakdown: {e}")
#             return []
    
#     @staticmethod
#     def calculate_best_time(user_id, days=30):
#         """
#         Calculate the best study time windows for a user
#         Based on start_time and end_time of sessions from sessions collection
        
#         Returns time slots with highest productivity
#         """
#         try:
#             db = get_db()
#             user_id = str(user_id)
#             ist = pytz.timezone('Asia/Kolkata')
            
#             # Get sessions from last 'days' days
#             cutoff_date_ist = datetime.now(ist) - timedelta(days=days)
#             cutoff_date_utc = cutoff_date_ist.astimezone(pytz.UTC).replace(tzinfo=None)
            
#             sessions = list(db.sessions.find({
#                 "user_id": user_id,
#                 "created_at": {"$gte": cutoff_date_utc}
#             }))
            
#             if not sessions:
#                 return {
#                     "best_times": [], 
#                     "message": "Not enough data. Complete more study sessions to get insights.",
#                     "total_sessions_analyzed": 0
#                 }
            
#             # Count sessions by hour of day (in IST)
#             hour_data = {}
#             for session in sessions:
#                 # Convert UTC start_time to IST
#                 utc_time = session['start_time'].replace(tzinfo=pytz.UTC)
#                 ist_time = utc_time.astimezone(ist)
#                 hour = ist_time.hour
                
#                 if hour not in hour_data:
#                     hour_data[hour] = {
#                         "count": 0,
#                         "total_time": 0,
#                         "total_cycles": 0,
#                         "completed_count": 0
#                     }
                
#                 hour_data[hour]["count"] += 1
#                 hour_data[hour]["total_time"] += session['total_time']
#                 hour_data[hour]["total_cycles"] += session['no_of_cycles_completed']
#                 if session.get('completion_status') == 'Completed':
#                     hour_data[hour]["completed_count"] += 1
            
#             # Calculate productivity score for each hour
#             best_times = []
#             for hour, data in hour_data.items():
#                 avg_time = data["total_time"] / data["count"]
#                 avg_cycles = data["total_cycles"] / data["count"]
#                 completion_rate = (data["completed_count"] / data["count"]) * 100
                
#                 # Productivity score weighted by:
#                 # - Average cycles completed (40%)
#                 # - Completion rate (40%)
#                 # - Average time studied (20%)
#                 score = (avg_cycles * 4) + (completion_rate * 0.4) + (avg_time / 10)
                
#                 # Format time slot
#                 start_hour = hour
#                 end_hour = (hour + 1) % 24
#                 time_slot = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                
#                 # Add period label (Morning/Afternoon/Evening/Night)
#                 if 5 <= hour < 12:
#                     period = "Morning"
#                 elif 12 <= hour < 17:
#                     period = "Afternoon"
#                 elif 17 <= hour < 21:
#                     period = "Evening"
#                 else:
#                     period = "Night"
                
#                 best_times.append({
#                     "hour": hour,
#                     "time_slot": time_slot,
#                     "period": period,
#                     "session_count": data["count"],
#                     "avg_time": round(avg_time, 1),
#                     "avg_cycles": round(avg_cycles, 1),
#                     "completion_rate": round(completion_rate, 1),
#                     "productivity_score": round(score, 2)
#                 })
            
#             # Sort by productivity score
#             best_times.sort(key=lambda x: x["productivity_score"], reverse=True)
            
#             return {
#                 "best_times": best_times[:5],  # Top 5 time slots
#                 "total_sessions_analyzed": len(sessions),
#                 "analysis_period_days": days
#             }
        
#         except Exception as e:
#             print(f"Error calculating best time: {e}")
#             import traceback
#             traceback.print_exc()
#             return {
#                 "best_times": [], 
#                 "error": str(e),
#                 "total_sessions_analyzed": 0
#             }