"""
NewsCache model.

WHY THIS FILE EXISTS:
Persists news API responses (top headlines / search results) keyed by
a cache_key (endpoint + params signature), with an expiry timestamp.
This is a database-backed cache — unlike an in-memory cache, it
survives app restarts, at the cost of a DB round-trip instead of pure
memory speed. Used by services/news_service.py once the news module
is built.
"""

from datetime import datetime
from database import db


class NewsCache(db.Model):
    __tablename__ = "news_cache"

    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    response_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<NewsCache {self.cache_key}>"