"""
History models: search_history and chat_history.

WHY THIS FILE EXISTS:
Both tables are simple append-only logs tied to a user (or anonymous,
via nullable user_id), so they're kept in one module rather than
split across two files.
"""

from datetime import datetime
from database import db


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    search_query = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    country = db.Column(db.String(100))
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SearchHistory {self.search_query[:40]}>"


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # "user" or "assistant"
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatHistory {self.role}: {self.message[:30]}>"