import os
import uuid
from fastapi import HTTPException

UPLOAD_DIR = "static/uploads"

# Only these file types are allowed — validated by extension
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# 5MB maximum file size
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5,242,880 bytes


def save_image(image_file) -> str:
    """
    Validate and save an uploaded image file to static/uploads/.

    Validations performed:
    1. File extension must be one of: jpg, jpeg, png, webp
    2. File size must not exceed 5MB

    The file is read ONCE, validated, then saved with a UUID-based name.
    Returns only the unique filename — the caller constructs the full URL.
    Raises HTTPException(400) on validation failure.
    """
    # --- Validate file extension ---
    ext = os.path.splitext(image_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed types: jpg, jpeg, png, webp",
        )

    # --- Read file content once (avoid double-read) ---
    content = image_file.file.read()

    # --- Validate file size ---
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum allowed size is 5MB",
        )

    # --- Save with UUID filename to avoid collisions and path-traversal attacks ---
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    return unique_name


def delete_image(filename: str):
    """
    Delete an image from static/uploads/.

    Silently does nothing if:
    - filename is None or empty
    - the file no longer exists on disk (already deleted)
    """
    if not filename:
        return

    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
