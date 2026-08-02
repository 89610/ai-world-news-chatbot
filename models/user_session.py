"""
UserSession model.

WHY THIS FILE EXISTS:
Tracks active login sessions per user — supports "Remember Me"
persistence and enables a future "log out of all devices" feature.
Flask-Login's day-to-day cookie auth doesn't strictly require this
table to function, but it gives visibility into who's logged in,
from where, and when.
"""

from datetime import datetime
from database import db


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<UserSession user_id={self.user_id}>"