from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, File, UploadFile
from typing import Optional
from app.database import get_db
from app.models import ProductOut, ProductDetail
from app.utils.file_handler import save_image, delete_image

router = APIRouter(tags=["Products"])


def _build_image_url(request: Request, filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    return f"{request.base_url}static/uploads/{filename}"


def _attach_image_url(request: Request, product: dict) -> dict:
    product["product_image"] = _build_image_url(request, product.get("product_image"))
    return product


def _validate_category_ids(cursor, category_ids_str: str):
    """Parse and validate category IDs. Returns list of valid ints or raises 400."""
    try:
        ids = [int(x.strip()) for x in category_ids_str.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_ids must be comma-separated integers",
        )
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_ids cannot be empty",
        )
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(f"SELECT id FROM categories WHERE id IN ({placeholders})", ids)
    missing = set(ids) - {row["id"] for row in cursor.fetchall()}
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category IDs not found: {sorted(missing)}",
        )
    return ids


@router.get("/products", response_model=list[ProductOut])
def list_products(request: Request, category_id: Optional[int] = None, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        if category_id is not None:
            cursor.execute(
                "SELECT * FROM products WHERE FIND_IN_SET(%s, category_ids) > 0 ORDER BY id",
                (str(category_id),),
            )
        else:
            cursor.execute("SELECT * FROM products ORDER BY id")
        return [_attach_image_url(request, row) for row in cursor.fetchall()]
    finally:
        cursor.close()


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    request: Request,
    name: str = Form(..., min_length=1, max_length=100),
    price: float = Form(...),
    category_ids: str = Form(...),
    image: UploadFile = File(...),
    db=Depends(get_db),
):
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0",
        )
    cursor = db.cursor(dictionary=True)
    filename = None
    try:
        _validate_category_ids(cursor, category_ids)
        filename = save_image(image)
        cursor.execute(
            "INSERT INTO products (name, product_image, price, category_ids) VALUES (%s, %s, %s, %s)",
            (name, filename, price, category_ids),
        )
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM products WHERE id = %s", (new_id,))
        return _attach_image_url(request, cursor.fetchone())
    except HTTPException:
        # Validation errors (price, category, file type) — clean up orphaned file
        if filename:
            delete_image(filename)
        raise
    except Exception:
        # DB errors after file was saved — clean up orphaned file
        if filename:
            delete_image(filename)
        raise
    finally:
        cursor.close()


@router.get("/product/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, request: Request, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        if product["category_ids"]:
            ids = [x.strip() for x in product["category_ids"].split(",") if x.strip()]
            placeholders = ",".join(["%s"] * len(ids))
            # ORDER BY FIELD preserves the order stored in category_ids CSV
            cursor.execute(
                f"SELECT name FROM categories WHERE id IN ({placeholders}) "
                f"ORDER BY FIELD(id, {placeholders})",
                ids + ids,
            )
            product["category_names"] = ",".join(row["name"] for row in cursor.fetchall())
        else:
            product["category_names"] = ""

        product["product_image"] = _build_image_url(request, product.get("product_image"))
        del product["category_ids"]
        return product
    finally:
        cursor.close()


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    request: Request,
    name: Optional[str] = Form(None, min_length=1, max_length=100),
    price: Optional[float] = Form(None),
    category_ids: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db=Depends(get_db),
):
    if price is not None and price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0",
        )
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        if category_ids is not None:
            _validate_category_ids(cursor, category_ids)

        new_name = name if name is not None else product["name"]
        new_price = price if price is not None else product["price"]
        new_category_ids = category_ids if category_ids is not None else product["category_ids"]

        new_image_filename = product["product_image"]
        if image and image.filename:
            delete_image(product["product_image"])
            new_image_filename = save_image(image)

        cursor.execute(
            "UPDATE products SET name = %s, price = %s, category_ids = %s, product_image = %s WHERE id = %s",
            (new_name, new_price, new_category_ids, new_image_filename, product_id),
        )
        db.commit()
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        return _attach_image_url(request, cursor.fetchone())
    finally:
        cursor.close()


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db=Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT product_image FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        delete_image(product["product_image"])
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db.commit()
    finally:
        cursor.close()
