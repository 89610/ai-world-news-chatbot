"""
Newsletter blueprint.

    POST /api/newsletter/subscribe

Stores the email in `newsletter_subscribers` and sends a real
confirmation email via Flask-Mail (Gmail SMTP). If email sending fails
(bad credentials, no internet, etc.) the subscription is still saved —
a failed email shouldn't lose someone's signup.
"""

import re
from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message

from database import db
from models.newsletter import NewsletterSubscriber

newsletter_bp = Blueprint("newsletter", __name__, url_prefix="/api/newsletter")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@newsletter_bp.route("/subscribe", methods=["POST"])
def subscribe():
    from app import mail  # imported here to avoid a circular import with app.py

    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()

    if not email or not EMAIL_PATTERN.match(email):
        return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({"ok": True, "already_subscribed": True})

    subscriber = NewsletterSubscriber(email=email)
    db.session.add(subscriber)
    db.session.commit()

    email_sent = True
    email_error = None
    if not current_app.config.get("MAIL_USERNAME"):
        email_sent = False
        email_error = "missing_mail_config"
    else:
        try:
            msg = Message(
                subject=f"You're subscribed to {current_app.config.get('APP_NAME', 'AI World News Chatbot')}",
                recipients=[email],
                body=(
                    "Thanks for subscribing!\n\n"
                    "You'll be the first to know about updates to the AI World News Chatbot project.\n\n"
                    "If you didn't sign up for this, you can safely ignore this email."
                ),
            )
            mail.send(msg)
        except Exception as exc:
            email_sent = False
            email_error = str(exc)

    return jsonify({
        "ok": True,
        "email_sent": email_sent,
        "email_error": email_error if not email_sent else None,
    })
