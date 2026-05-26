import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


# ─── GET /categories ─── List all categories ───────────────────────────────

@router.get("", response_model=list[CategoryOut])
def list_categories(db=Depends(get_db)):
    """Return all categories ordered by ID."""
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, created_at, updated_at FROM categories ORDER BY id"
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


# ─── POST /categories ─── Create a new category ────────────────────────────

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db=Depends(get_db)):
    """
    Create a category and return it with the generated ID.
    Returns 400 if the category name already exists (UNIQUE constraint).
    """
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO categories (name) VALUES (%s)",
            (payload.name,)
        )
        db.commit()
    except mysql.connector.IntegrityError:
        # IntegrityError is raised when the UNIQUE constraint on `name` is violated.
        # We catch it here and return a clean 400 instead of a raw 500 crash.
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{payload.name}' already exists",
        )

    new_id = cursor.lastrowid
    cursor.execute(
        "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s",
        (new_id,)
    )
    new_category = cursor.fetchone()
    cursor.close()
    return new_category


# ─── PUT /categories/{id} ─── Update a category ────────────────────────────

@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db=Depends(get_db)):
    """
    Update a category's name.
    Returns 404 if the category doesn't exist.
    Returns 400 if the new name is already taken by another category.
    """
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s",
            (payload.name, category_id)
        )
        db.commit()
    except mysql.connector.IntegrityError:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{payload.name}' already exists",
        )

    if cursor.rowcount == 0:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    cursor.execute(
        "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s",
        (category_id,)
    )
    updated = cursor.fetchone()
    cursor.close()
    return updated


# ─── DELETE /categories/{id} ─── Delete a category ─────────────────────────

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db=Depends(get_db)):
    """Delete a category. Returns 404 if the category doesn't exist."""
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM categories WHERE id = %s",
        (category_id,)
    )
    db.commit()

    if cursor.rowcount == 0:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    cursor.close()
    # 204 No Content — returns no response body
