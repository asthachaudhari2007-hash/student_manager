from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

from config import Config

# ==========================================================
# Initialize Extensions
# ==========================================================

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


# ==========================================================
# User Loader
# ==========================================================

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))


# ==========================================================
# Create Flask App
# ==========================================================

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # ======================================================
    # Register Blueprints
    # ======================================================

    from app.routes.dashboard import dashboard_bp
    from app.routes.auth import auth_bp
    from app.routes.students import students_bp
    from app.routes.attendance import attendance_bp
    from app.routes.results import results_bp          # NEW
    from app.routes.feedback import feedback_bp        # NEW

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(results_bp)                 # NEW
    app.register_blueprint(feedback_bp)                # NEW

    # ======================================================
    # Import Models
    # ======================================================

    from app.models.user import User
    from app.models.student import Student
    from app.models.attendance import Attendance
    from app.models.result import Result
    from app.models.feedback import Feedback
    from app.models.feedback_form import FeedbackForm   # NEW

    # ======================================================
    # Create Tables
    # ======================================================

    with app.app_context():
        db.create_all()

    return app
