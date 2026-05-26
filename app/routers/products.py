from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, File, UploadFile
from typing import Optional
from app.database import get_db
from app.models import ProductOut, ProductDetail
from app.utils.file_handler import save_image, delete_image

router = APIRouter(tags=["Products"])


# ─── Helper: Build full image URL ────────────────────────────────────────────

def _build_image_url(request: Request, filename: Optional[str]) -> Optional[str]:
    """
    Convert a stored filename (e.g. "a3f9c2b1.jpg") to a full accessible URL
    (e.g. "http://localhost:8000/static/uploads/a3f9c2b1.jpg").

    Why return a full URL instead of just the filename?
    Any client (React, Vue, mobile app) can use it directly in <img src="...">
    without needing to guess or reconstruct the base URL themselves.
    """
    if not filename:
        return None
    return f"{request.base_url}static/uploads/{filename}"


def _attach_image_url(request: Request, product: dict) -> dict:
    """Replace the raw filename in a product dict with the full URL."""
    product["product_image"] = _build_image_url(request, product.get("product_image"))
    return product


def _validate_category_ids(cursor, category_ids_str: str):
    """
    Parse and validate that all category IDs in the CSV string exist in the DB.
    Raises HTTPException(400) if any ID is missing.
    Returns the list of integer IDs.
    """
    ids = [int(x.strip()) for x in category_ids_str.split(",") if x.strip()]
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_ids cannot be empty",
        )

    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"SELECT id FROM categories WHERE id IN ({placeholders})",
        ids,
    )
    found = {row["id"] for row in cursor.fetchall()}
    missing = set(ids) - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category IDs not found: {sorted(missing)}",
        )
    return ids


# ─── GET /products ─── List products (optional category filter) ─────────────

@router.get("/products", response_model=list[ProductOut])
def list_products(
    request: Request,
    category_id: Optional[int] = None,
    db=Depends(get_db),
):
    """
    Return all products with full image URLs.
    Optional ?category_id=X filter uses MySQL's FIND_IN_SET to search the CSV column.
    """
    cursor = db.cursor(dictionary=True)

    if category_id:
        cursor.execute(
            "SELECT * FROM products WHERE FIND_IN_SET(%s, category_ids) > 0 ORDER BY id",
            (str(category_id),)
        )
    else:
        cursor.execute("SELECT * FROM products ORDER BY id")

    rows = cursor.fetchall()
    cursor.close()
    return [_attach_image_url(request, row) for row in rows]


# ─── POST /products ─── Create a product with image upload ──────────────────

@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    category_ids: str = Form(...),
    image: UploadFile = File(...),
    db=Depends(get_db),
):
    """
    Create a new product. Accepts multipart/form-data (required for file uploads).

    Validations:
    - price must be greater than 0
    - image must be jpg/jpeg/png/webp and under 5MB
    - all category IDs must exist in the categories table
    """
    # --- Validate price ---
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0",
        )

    cursor = db.cursor(dictionary=True)

    # --- Validate all category IDs exist ---
    _validate_category_ids(cursor, category_ids)

    # --- Save image (validates type and size inside file_handler) ---
    filename = save_image(image)

    # --- Insert product into DB ---
    cursor.execute(
        "INSERT INTO products (name, product_image, price, category_ids) VALUES (%s, %s, %s, %s)",
        (name, filename, price, category_ids),
    )
    db.commit()

    # --- Fetch and return newly created product with full image URL ---
    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM products WHERE id = %s", (new_id,))
    product = cursor.fetchone()
    cursor.close()
    return _attach_image_url(request, product)


# ─── GET /product/{id} ─── Product detail with category names ───────────────

@router.get("/product/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, request: Request, db=Depends(get_db)):
    """
    Return a single product's full details.
    The category_ids CSV (e.g. "1,2") is resolved to actual category names
    (e.g. "Electronics,Laptops") for a human-readable response.
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    # --- Resolve category IDs → names ---
    if product["category_ids"]:
        ids = [x.strip() for x in product["category_ids"].split(",") if x.strip()]
        placeholders = ",".join(["%s"] * len(ids))
        cursor.execute(
            f"SELECT name FROM categories WHERE id IN ({placeholders})",
            ids,
        )
        names = [row["name"] for row in cursor.fetchall()]
        product["category_names"] = ",".join(names)
    else:
        product["category_names"] = ""

    # --- Attach full image URL, remove raw category_ids field ---
    product["product_image"] = _build_image_url(request, product.get("product_image"))
    del product["category_ids"]
    cursor.close()
    return product


# ─── PUT /products/{id} ─── Update a product ────────────────────────────────

@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    request: Request,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category_ids: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db=Depends(get_db),
):
    """
    Update a product's fields. All fields are optional — only provided
    fields are changed. Validates price, category IDs, and image if provided.
    """
    # --- Validate price if provided ---
    if price is not None and price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0",
        )

    cursor = db.cursor(dictionary=True)

    # --- Fetch current product ---
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    # --- Validate new category IDs if provided ---
    if category_ids is not None:
        _validate_category_ids(cursor, category_ids)

    # --- Use existing values as defaults for fields not provided ---
    new_name = name if name is not None else product["name"]
    new_price = price if price is not None else product["price"]
    new_category_ids = category_ids if category_ids is not None else product["category_ids"]

    # --- Handle optional image replacement ---
    new_image_filename = product["product_image"]
    if image and image.filename:
        delete_image(product["product_image"])    # delete old file from disk
        new_image_filename = save_image(image)    # validates and saves new file

    # --- Persist updates ---
    cursor.execute(
        """UPDATE products
           SET name = %s, price = %s, category_ids = %s, product_image = %s
           WHERE id = %s""",
        (new_name, new_price, new_category_ids, new_image_filename, product_id),
    )
    db.commit()

    # --- Return updated product with full image URL ---
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    updated = cursor.fetchone()
    cursor.close()
    return _attach_image_url(request, updated)


# ─── DELETE /products/{id} ─── Delete product and its image ─────────────────

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db=Depends(get_db)):
    """
    Delete a product and remove its image file from disk.
    Image file is retrieved before row deletion so we know what to clean up.
    """
    cursor = db.cursor(dictionary=True)

    # --- Get image filename before deleting the row ---
    cursor.execute(
        "SELECT product_image FROM products WHERE id = %s",
        (product_id,),
    )
    product = cursor.fetchone()

    if not product:
        cursor.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    # --- Delete image file from disk ---
    delete_image(product["product_image"])

    # --- Delete DB row ---
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    db.commit()
    cursor.close()
    # 204 No Content — returns no response body
