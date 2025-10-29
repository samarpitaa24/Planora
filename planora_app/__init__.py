from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = "dummy_key_for_testing"

    # Import and register blueprints
    from planora_app.dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from planora_app.dashboard.flashcards_routes import flashcards_bp
    app.register_blueprint(flashcards_bp)

    from planora_app.dashboard.cards_routes import cards_bp   # ✅ new
    app.register_blueprint(cards_bp)
    
    from planora_app.pomodoro.timer_routes import timer_bp   # ✅ pomodoro
    app.register_blueprint(timer_bp)
    
    from planora_app.notes.notes_routes import notes_bp   
    app.register_blueprint(notes_bp)
    
    from planora_app.tasks.task_routes import tasks_bp
    app.register_blueprint(tasks_bp)
    
    # ✅ Register notes_list blueprint
    from planora_app.notes_list.notes_list_routes import notes_bp
    app.register_blueprint(notes_bp)
    
    from planora_app.sessions.sessions_routes import sessions_bp
    app.register_blueprint(sessions_bp)
    
    from planora_app.preferences.preferences_routes import preferences_bp
    app.register_blueprint(preferences_bp)
    
    # Import and register auth blueprint
    from planora_app.auth.routes import auth
    app.register_blueprint(auth)

    from planora_app.onboarding.routes import onboarding_bp
    app.register_blueprint(onboarding_bp)
    
    return app
