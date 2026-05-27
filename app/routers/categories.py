import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import CategoryCreate, CategoryUpdate, CategoryOut
from app.utils.file_handler import delete_image

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, created_at, updated_at FROM categories ORDER BY id")
        return cursor.fetchall()
    finally:
        cursor.close()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (payload.name,))
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s", (new_id,)
        )
        return cursor.fetchone()
    except mysql.connector.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{payload.name}' already exists",
        )
    finally:
        cursor.close()


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        # Check existence first — UPDATE rowcount=0 doesn't reliably mean "not found"
        # because updating a row to its current value also gives rowcount=0
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s",
            (payload.name, category_id),
        )
        db.commit()
        cursor.execute(
            "SELECT id, name, created_at, updated_at FROM categories WHERE id = %s",
            (category_id,),
        )
        return cursor.fetchone()
    except mysql.connector.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category name '{payload.name}' already exists",
        )
    finally:
        cursor.close()


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db=Depends(get_db)):
    """
    Cascade logic: products belonging ONLY to this category are deleted along
    with their image file. Products with other categories keep living — just
    this category ID is stripped from their CSV.
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )

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
                delete_image(product["product_image"])
                cursor.execute("DELETE FROM products WHERE id = %s", (product["id"],))
            else:
                cursor.execute(
                    "UPDATE products SET category_ids = %s WHERE id = %s",
                    (",".join(remaining_ids), product["id"]),
                )

        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        db.commit()
    finally:
        cursor.close()
