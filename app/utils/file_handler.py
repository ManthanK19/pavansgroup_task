import os
import uuid
from fastapi import HTTPException

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def save_image(image_file) -> str:
    """Validate extension and size, then save the file with a UUID-based name."""
    ext = os.path.splitext(image_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: jpg, jpeg, png, webp",
        )

    content = image_file.file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum allowed size is 5MB")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, unique_name), "wb") as f:
        f.write(content)

    return unique_name


def delete_image(filename: str):
    """Remove an image from disk. Does nothing if filename is empty or file is missing."""
    if not filename:
        return
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
