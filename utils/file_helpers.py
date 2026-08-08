"""
File upload helpers.

WHY CLOUDINARY (not local disk):
Railway's filesystem is ephemeral — every restart or redeploy wipes
anything saved locally. Uploading to Cloudinary instead means profile
pictures get a permanent https URL that survives forever, regardless
of how many times the server restarts.
"""

import cloudinary
import cloudinary.uploader
from flask import current_app


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_profile_picture(file_storage, allowed_extensions: set) -> str:
    """Uploads to Cloudinary and returns the permanent secure URL,
    or None if the file was invalid or Cloudinary isn't configured."""
    if not file_storage or not file_storage.filename:
        return None

    if not allowed_file(file_storage.filename, allowed_extensions):
        return None

    cloudinary.config(
        cloud_name=current_app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=current_app.config.get("CLOUDINARY_API_KEY"),
        api_secret=current_app.config.get("CLOUDINARY_API_SECRET"),
    )

    try:
        result = cloudinary.uploader.upload(
            file_storage,
            folder="ai_news_chatbot_profiles",
            resource_type="image",
        )
        return result.get("secure_url")
    except Exception:
        return None