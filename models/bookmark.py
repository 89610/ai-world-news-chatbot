"""
Bookmark model.

WHY THIS FILE EXISTS:
One row per article a user saves to read later. Tied to `users` via
user_id — the relationship is declared on the User side
(user.bookmarks), so this file only needs the foreign key column.
"""

from datetime import datetime
from database import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    __table_args__ = (
        db.Index(
            "ix_bookmarks_user_url", "user_id", "article_url",
            mysql_length={"article_url": 255},
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    article_title = db.Column(db.String(500), nullable=False)
    article_url = db.Column(db.String(1000), nullable=False)
    article_image = db.Column(db.String(1000))
    source_name = db.Column(db.String(200))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Bookmark {self.article_title[:40]}>"