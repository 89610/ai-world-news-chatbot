from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.user_session import UserSession
from database import db
from models.user import User
from utils.file_helpers import save_profile_picture

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


@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        new_username = request.form.get("username", "").strip()

        if not new_username or len(new_username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("edit_profile.html")

        # Only block it if some OTHER user already has this username —
        # saving your own unchanged username should never fail.
        existing = User.query.filter(
            User.username == new_username, User.id != current_user.id
        ).first()
        if existing:
            flash("That username is already taken.", "error")
            return render_template("edit_profile.html")

        current_user.username = new_username

        uploaded_file = request.files.get("profile_picture")
        if uploaded_file and uploaded_file.filename:
            picture_path = save_profile_picture(
                uploaded_file,
                
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            )
            if picture_path is None:
                flash("Profile picture must be a PNG, JPG, GIF, or WEBP file.", "error")
                return render_template("edit_profile.html")
            current_user.profile_picture = picture_path

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.view_profile"))

    return render_template("edit_profile.html")