"""
Auth blueprint.

    GET/POST /auth/register  — create account, optional profile picture
    GET/POST /auth/login     — sign in, with "Remember Me" persistence
    POST     /auth/logout    — sign out, invalidates the tracked session

WHY SESSION TRACKING:
Every successful login creates a row in `user_sessions` (session
token, IP, user agent, expiry) — Flask-Login's cookie handles the
actual "staying logged in" mechanism, but this table gives visibility
into active sessions and sets up a future "log out of all devices"
feature.
"""

import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from database import db
from models.user import User
from models.user_session import UserSession
from utils.file_helpers import save_profile_picture

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # --- Validation -----------------------------------------------------
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email is already taken.", "error")
            return render_template("register.html")

        # --- Profile picture (optional) --------------------------------------
        profile_picture_path = None
        uploaded_file = request.files.get("profile_picture")
        if uploaded_file and uploaded_file.filename:
            profile_picture_path = save_profile_picture(
                uploaded_file,
                current_app.config["UPLOAD_FOLDER"],
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            )
            if profile_picture_path is None:
                flash("Profile picture must be a PNG, JPG, GIF, or WEBP file.", "error")
                return render_template("register.html")

        # --- Create account ---------------------------------------------------
        user = User(username=username, email=email, profile_picture=profile_picture_path)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        _track_session(user)
        flash("Account created — welcome!", "success")
        return redirect(url_for("home.index"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember_me"))

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid username/email or password.", "error")
            return render_template("login.html")

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)
        _track_session(user, remember=remember)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("home.index"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "success")
    return redirect(url_for("home.index"))


def _track_session(user, remember=False):
    """Records a row in user_sessions for this login — visibility into
    active sessions, and groundwork for a future 'log out everywhere'."""
    duration_days = current_app.config["REMEMBER_COOKIE_DURATION_DAYS"] if remember else 1
    session_entry = UserSession(
        user_id=user.id,
        session_token=secrets.token_hex(32),
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:255],
        expires_at=datetime.utcnow() + timedelta(days=duration_days),
    )
    db.session.add(session_entry)
    db.session.commit()