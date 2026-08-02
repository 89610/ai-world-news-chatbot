"""
Newsletter subscriber model.

One row per email that's signed up via the footer newsletter form.
Kept separate from `users` since subscribing doesn't require an account
— anyone can subscribe with just an email, logged in or not.
"""

from datetime import datetime
from database import db


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"
