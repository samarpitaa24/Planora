from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from bson.objectid import ObjectId
from datetime import datetime
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
        age = request.form.get('age')
        subjects = request.form.getlist('subjects')
        sleep_schedule = request.form.get('sleep_schedule')
        morning_evening_person = request.form.get('morning_evening_person')
        motivation = request.form.get('motivation')
        difficulties = request.form.getlist('difficulties')

        if not subjects:
            flash('Please select at least one subject', 'danger')
            return redirect(url_for('onboarding.onboarding'))

        if not difficulties:
            flash('Please select at least one difficulty', 'danger')
            return redirect(url_for('onboarding.onboarding'))

        preferences_data = {
            'user_id': ObjectId(session['user_id']),
            'age': int(age),
            'subjects': subjects,
            'sleep_schedule': sleep_schedule,
            'morning_evening_person': morning_evening_person,
            'motivation': motivation,
            'difficulties': difficulties,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        db.user_preferences.insert_one(preferences_data)

        db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'onboarding_completed': True}}
        )

        flash('Welcome to Planora! Your preferences have been saved.', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('onboarding.html', user=user)
