from flask import Blueprint, render_template, request, jsonify, session
from planora_app.extensions import get_db
from planora_app.pomodoro.timer_services import TimerService
from bson import ObjectId
from datetime import datetime

timer_bp = Blueprint('timer', __name__, url_prefix='/timer')

@timer_bp.route('/')
def timer_page():
    """Render the timer page with subjects and latest note"""
    try:
        db = get_db()
        
        # Get user_id from session (adjust based on your auth system)
        user_id = session.get('user_id')
        if not user_id:
            # For testing without auth, use a default user
            user_id = "default_user"
        
        # Fetch user data from users collection
        user = db.users.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else db.users.find_one({"username": user_id})
        
        subjects = []
        if user and 'qna' in user and 'subjects' in user['qna']:
            subjects = user['qna']['subjects']
        else:
            # Default subjects if none exist
            subjects = ["Mathematics", "Science", "English", "Social Studies", "Hindi"]
        
        # Fetch latest note for this user
        latest_note = db.notes.find_one(
            {"user_id": str(user_id)},
            sort=[("created_at", -1)]
        )
        
        return render_template('timer.html', 
                             subjects=subjects, 
                             latest_note=latest_note,
                             user_id=str(user_id))
    
    except Exception as e:
        print(f"Error loading timer page: {e}")
        return render_template('timer.html', 
                             subjects=["Mathematics", "Science", "English"], 
                             latest_note=None,
                             user_id="default_user")


@timer_bp.route('/api/subjects', methods=['GET'])
def get_subjects():
    """API endpoint to fetch subjects dynamically"""
    try:
        db = get_db()
        user_id = session.get('user_id', 'default_user')
        
        # Fetch user data from users collection
        user = db.users.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else db.users.find_one({"username": user_id})
        
        subjects = []
        if user and 'qna' in user and 'subjects' in user['qna']:
            subjects = user['qna']['subjects']
        else:
            subjects = ["Mathematics", "Science", "English", "Social Studies", "Hindi"]
        
        return jsonify({"success": True, "subjects": subjects}), 200
    
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@timer_bp.route('/api/save-session', methods=['POST'])
def save_session():
    """Save a pomodoro session to database"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'subject', 'start_time', 'end_time', 
                          'total_time', 'no_of_cycles_decided', 'no_of_cycles_completed',
                          'break_time', 'pause_count', 'timer_per_cycle', 
                          'completion_status', 'date']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False, 
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Validate data types and values
        if not isinstance(data.get('total_time'), (int, float)) or data['total_time'] < 0:
            return jsonify({
                "success": False,
                "error": "Invalid total_time value"
            }), 400
        
        if not isinstance(data.get('no_of_cycles_completed'), int) or data['no_of_cycles_completed'] < 0:
            return jsonify({
                "success": False,
                "error": "Invalid no_of_cycles_completed value"
            }), 400
        
        if not isinstance(data.get('no_of_cycles_decided'), int) or data['no_of_cycles_decided'] < 1:
            return jsonify({
                "success": False,
                "error": "Invalid no_of_cycles_decided value"
            }), 400
        
        # Validate completion status
        valid_statuses = ['Completed', 'Not Completed', 'Partially Completed']
        if data.get('completion_status') not in valid_statuses:
            return jsonify({
                "success": False,
                "error": "Invalid completion_status value"
            }), 400
        
        # Validate subject exists in user's subjects
        db = get_db()
        user_id = data['user_id']
        user = db.users.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else db.users.find_one({"username": user_id})
        
        if user and 'qna' in user and 'subjects' in user['qna']:
            if data['subject'] not in user['qna']['subjects']:
                return jsonify({
                    "success": False,
                    "error": "Invalid subject for this user"
                }), 400
        
        # Save session using service
        result = TimerService.save_session(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 500
    
    except Exception as e:
        print(f"Error saving session: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@timer_bp.route('/api/sessions/recent', methods=['GET'])
def get_recent_sessions():
    """Get recent sessions for the user"""
    try:
        user_id = request.args.get('user_id', session.get('user_id', 'default_user'))
        limit = int(request.args.get('limit', 10))
        
        sessions = TimerService.get_recent_sessions(user_id, limit)
        
        return jsonify({
            "success": True,
            "sessions": sessions
        }), 200
    
    except Exception as e:
        print(f"Error fetching recent sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@timer_bp.route('/api/sessions/stats', methods=['GET'])
def get_session_stats():
    """Get session statistics for the user"""
    try:
        user_id = request.args.get('user_id', session.get('user_id', 'default_user'))
        days = int(request.args.get('days', 7))
        
        stats = TimerService.get_session_stats(user_id, days)
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@timer_bp.route('/api/best-time', methods=['GET'])
def get_best_time():
    """Get best study time analysis for the user"""
    try:
        user_id = request.args.get('user_id', session.get('user_id', 'default_user'))
        days = int(request.args.get('days', 30))
        
        best_time_data = TimerService.calculate_best_time(user_id, days)
        
        return jsonify({
            "success": True,
            "data": best_time_data
        }), 200
    
    except Exception as e:
        print(f"Error calculating best time: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@timer_bp.route('/api/subject-breakdown', methods=['GET'])
def get_subject_breakdown():
    """Get study time breakdown by subject"""
    try:
        user_id = request.args.get('user_id', session.get('user_id', 'default_user'))
        days = int(request.args.get('days', 7))
        
        breakdown = TimerService.get_subject_breakdown(user_id, days)
        
        return jsonify({
            "success": True,
            "breakdown": breakdown
        }), 200
    
    except Exception as e:
        print(f"Error fetching subject breakdown: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500