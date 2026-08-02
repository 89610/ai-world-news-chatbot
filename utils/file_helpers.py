"""
File upload helpers.

WHY THIS FILE EXISTS:
Handling an uploaded profile picture safely requires more than just
saving whatever the browser sends — the extension must be checked
against an allowlist (never trust the client), and the filename must
be sanitized and made unique so two users uploading "photo.jpg" don't
overwrite each other. Kept in utils/ since this logic isn't tied to
any one route and could be reused (e.g. article image uploads later).
"""

import os
import uuid
from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_profile_picture(file_storage, upload_folder: str, allowed_extensions: set) -> str:
    """Saves an uploaded file with a unique, sanitized name.

    Returns the relative path (e.g. 'static/images/profiles/abc123.jpg')
    to store in the database, or None if the file was invalid.
    """
    if not file_storage or not file_storage.filename:
        return None

    if not allowed_file(file_storage.filename, allowed_extensions):
        return None

    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    # A random unique name avoids filename collisions between users
    # and avoids leaking the original filename.
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_name)
    file_storage.save(file_path)

    return file_path.replace("\\", "/")  # normalize for URLs on Windows