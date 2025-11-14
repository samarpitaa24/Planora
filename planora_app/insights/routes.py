from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from planora_app.extensions import get_db
from datetime import datetime, timedelta
from collections import defaultdict

insights_bp = Blueprint("insights", __name__, url_prefix="/insights")

@insights_bp.route("/")
def insights():
    """Render insights page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template("insights.html")


@insights_bp.route("/api/hours-by-subject", methods=["GET"])
def hours_by_subject():
    """
    API endpoint to get study hours grouped by subject
    Query params: filter_type (day/week/month/all)
    """
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']  # Keep as string, not ObjectId
    filter_type = request.args.get('filter_type', 'week')  # day, week, month, all
    
    db = get_db()
    
    # Calculate date range based on filter
    today = datetime.now()
    
    if filter_type == 'day':
        # Last 24 hours
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif filter_type == 'week':
        # Last 7 days
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif filter_type == 'month':
        # Last 30 days
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif filter_type == 'all':
        # All time - use a very old date
        start_date = "2020-01-01"
    else:
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # MongoDB aggregation pipeline
    # Note: user_id is stored as STRING in your DB, not ObjectId
    pipeline = [
        {
            "$match": {
                "user_id": user_id,  # String comparison
                "date": {"$gte": start_date},
                "completion_status": {"$in": ["Completed", "Incomplete", "Interrupted", "completed", "incomplete", "interrupted"]}
            }
        },
        {
            "$group": {
                "_id": "$subject",
                "total_minutes": {
                    "$sum": {
                        "$multiply": [
                            "$no_of_cycles_completed",
                            "$timer_per_cycle"
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "subject": "$_id",
                "total_hours": {"$divide": ["$total_minutes", 60]},
                "_id": 0
            }
        },
        {
            "$sort": {"total_hours": -1}
        }
    ]
    
    results = list(db.sessions.aggregate(pipeline))
    
    # Format for Chart.js
    subjects = [item['subject'] for item in results]
    hours = [round(item['total_hours'], 2) for item in results]
    
    return jsonify({
        "subjects": subjects,
        "hours": hours,
        "filter_type": filter_type
    })


@insights_bp.route("/api/progress-over-time", methods=["GET"])
def progress_over_time():
    """
    API endpoint to get daily study progress for last 30 days
    """
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']  # String format
    db = get_db()
    
    # Last 30 days
    today = datetime.now()
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # MongoDB aggregation pipeline
    pipeline = [
        {
            "$match": {
                "user_id": user_id,  # String comparison
                "date": {"$gte": start_date},
                "completion_status": {"$in": ["Completed", "Incomplete", "Interrupted", "completed", "incomplete", "interrupted"]}
            }
        },
        {
            "$group": {
                "_id": "$date",
                "total_minutes": {
                    "$sum": {
                        "$multiply": [
                            "$no_of_cycles_completed",
                            "$timer_per_cycle"
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "date": "$_id",
                "total_hours": {"$divide": ["$total_minutes", 60]},
                "_id": 0
            }
        },
        {
            "$sort": {"date": 1}
        }
    ]
    
    results = list(db.sessions.aggregate(pipeline))
    
    # Create a dictionary for easy lookup
    hours_by_date = {item['date']: round(item['total_hours'], 2) for item in results}
    
    # Generate all dates for last 30 days (fill missing dates with 0)
    dates = []
    hours = []
    
    for i in range(30, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(date)
        hours.append(hours_by_date.get(date, 0))
    
    return jsonify({
        "dates": dates,
        "hours": hours
    })


@insights_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Get summary statistics for the insights page
    """
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']  # String format
    db = get_db()
    
    # Total study hours (all time)
    pipeline_total = [
        {
            "$match": {
                "user_id": user_id,  # String comparison
                "completion_status": {"$in": ["Completed", "Incomplete", "Interrupted", "completed", "incomplete", "interrupted"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_minutes": {
                    "$sum": {
                        "$multiply": [
                            "$no_of_cycles_completed",
                            "$timer_per_cycle"
                        ]
                    }
                }
            }
        }
    ]
    
    total_result = list(db.sessions.aggregate(pipeline_total))
    total_hours = round(total_result[0]['total_minutes'] / 60, 1) if total_result else 0
    
    # Study streak calculation
    today = datetime.now()
    streak = 0
    current_date = today
    
    for i in range(365):  # Check up to 1 year back
        date_str = current_date.strftime("%Y-%m-%d")
        session_exists = db.sessions.find_one({
            "user_id": user_id,  # String comparison
            "date": date_str,
            "completion_status": {"$in": ["Completed", "Incomplete", "Interrupted", "completed", "incomplete", "interrupted"]}
        })
        
        if session_exists:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    # Total sessions
    total_sessions = db.sessions.count_documents({
        "user_id": user_id,  # String comparison
        "completion_status": {"$in": ["Completed", "Incomplete", "Interrupted", "completed", "incomplete", "interrupted"]}
    })
    
    return jsonify({
        "total_hours": total_hours,
        "study_streak": streak,
        "total_sessions": total_sessions
    })