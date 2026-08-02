"""
Profile blueprint.

WHY THIS FILE EXISTS:
Demonstrates a protected route — anyone not logged in gets redirected
to /auth/login (handled by Flask-Login's login_required + the
unauthorized handler in app.py) instead of seeing this page. Also
surfaces the user_sessions table so "session management" is visibly
real, not just a table nobody looks at.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.user_session import UserSession

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def view_profile():
    sessions = (
        UserSession.query
        .filter_by(user_id=current_user.id)
        .order_by(UserSession.created_at.desc())
        .all()
    )
    return render_template("profile.html", sessions=sessions)