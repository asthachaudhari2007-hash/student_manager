from datetime import datetime

from flask_login import UserMixin

from app import db, login_manager


# ==============================
# User Loader for Flask-Login
# ==============================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================
# User Model
# ==============================
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="Faculty"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User {self.username}>"