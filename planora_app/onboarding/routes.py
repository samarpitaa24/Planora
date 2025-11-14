from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from planora_app.extensions import get_db

onboarding_bp = Blueprint('onboarding', __name__, url_prefix="/onboarding")


@onboarding_bp.route("/", methods=["GET", "POST"])
def onboarding():
    db = get_db()

    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('auth.login'))

    user = db.users.find_one({'_id': ObjectId(session['user_id'])})

    if user.get('onboarding_completed', False):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        try:
            # Get form data
            age = request.form.get('age')
            dob = request.form.get('dob')
            subjects = request.form.getlist('subjects')
            sleep_schedule = request.form.get('sleep_schedule')
            morning_evening_person = request.form.get('morning_evening_person')
            motivation = request.form.get('motivation')
            difficulties = request.form.getlist('difficulties')
            study_start = request.form.get('study_start')
            study_end = request.form.get('study_end')

            # Validation
            if not subjects:
                flash('Please select at least one subject', 'danger')
                return redirect(url_for('onboarding.onboarding'))

            if not difficulties:
                flash('Please select at least one difficulty', 'danger')
                return redirect(url_for('onboarding.onboarding'))

            # Validate preferred study time duration (max 3 hours)
            if study_start and study_end:
                start_time = datetime.strptime(study_start, '%H:%M')
                end_time = datetime.strptime(study_end, '%H:%M')
                
                # Handle cases where end time is past midnight
                if end_time <= start_time:
                    end_time += timedelta(days=1)
                
                duration = (end_time - start_time).total_seconds() / 3600
                
                if duration > 3:
                    flash('Preferred study time cannot exceed 3 hours', 'danger')
                    return redirect(url_for('onboarding.onboarding'))

            # Build QNA data object
            qna_data = {
                'age': int(age),
                'dob': dob,  # Stored as string in YYYY-MM-DD format
                'subjects': subjects,
                'sleep_schedule': sleep_schedule,
                'morning_evening_person': morning_evening_person,
                'motivation': motivation,
                'difficulties': difficulties,
                'preferred_study_time': {
                    'start': study_start,  # Format: HH:MM
                    'end': study_end,      # Format: HH:MM
                    'duration_hours': round(duration, 2)  # Store calculated duration
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            # Update user document
            db.users.update_one(
                {'_id': ObjectId(session['user_id'])},
                {'$set': {'qna': qna_data, 'onboarding_completed': True}}
            )

            flash('Welcome to Planora! Your preferences have been saved.', 'success')
            return redirect(url_for('dashboard.dashboard'))
            
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('onboarding.onboarding'))

    # For GET request - set max date for DOB (today's date)
    max_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('onboarding.html', user=user, max_date=max_date)