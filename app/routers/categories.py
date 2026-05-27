import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import CategoryCreate, CategoryUpdate, CategoryOut
from app.utils.file_handler import delete_image

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, created_at, updated_at FROM categories ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    return rows


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (payload.name,))
        db.commit()
    except mysql.connector.IntegrityError:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{payload.name}' already exists",
        )
    new_id = cursor.lastrowid
    cursor.execute(
        "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s", (new_id,)
    )
    new_category = cursor.fetchone()
    cursor.close()
    return new_category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s",
            (payload.name, category_id),
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
        "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s", (category_id,)
    )
    updated = cursor.fetchone()
    cursor.close()
    return updated


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db=Depends(get_db)):
    """
    Deletes a category and handles affected products in two ways:
    - If the product belongs ONLY to this category → the product is also deleted.
    - If the product belongs to other categories too → this category is removed
      from its category_ids CSV and the product stays.

    Note: Ideally this would be enforced by a database-level FK constraint with
    CASCADE rules. However, because category_ids is stored as a CSV string
    (e.g. "1,2,3") in a single VARCHAR column, MySQL cannot place a foreign key
    on it — FK constraints only work on atomic single-value columns. So we
    replicate the cascade behaviour manually here in application code.
    """
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    # Find every product that references this category ID inside its CSV column
    cursor.execute(
        "SELECT id, category_ids, product_image FROM products "
        "WHERE FIND_IN_SET(%s, category_ids) > 0",
        (str(category_id),),
    )
    affected_products = cursor.fetchall()

    for product in affected_products:
        remaining_ids = [
            i.strip()
            for i in product["category_ids"].split(",")
            if i.strip() and i.strip() != str(category_id)
        ]

        if not remaining_ids:
            # This was the only category this product belonged to → delete the product
            delete_image(product["product_image"])
            cursor.execute("DELETE FROM products WHERE id = %s", (product["id"],))
        else:
            # Product belongs to other categories too → just strip out this category
            cursor.execute(
                "UPDATE products SET category_ids = %s WHERE id = %s",
                (",".join(remaining_ids), product["id"]),
            )

    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    db.commit()
    cursor.close()
