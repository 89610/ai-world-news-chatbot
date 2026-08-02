"""
User model.

WHY THIS FILE EXISTS:
Represents a registered account. Passwords are hashed with
Flask-Bcrypt — never stored in plaintext, and Bcrypt is deliberately
slow (by design) to resist brute-force attacks. Implements
Flask-Login's UserMixin so it plugs directly into the LoginManager
added in the authentication phase.

RELATIONSHIPS:
One user has many bookmarks, many search_history entries, many
chat_history entries, and many sessions. Each relationship uses
cascade="all, delete-orphan" so deleting a user cleans up their
related rows instead of leaving orphaned data behind.
"""

from datetime import datetime
from flask_login import UserMixin
from database import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---------------------------------------------------
    bookmarks = db.relationship(
        "Bookmark", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    search_history = db.relationship(
        "SearchHistory", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    chat_history = db.relationship(
        "ChatHistory", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "UserSession", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"