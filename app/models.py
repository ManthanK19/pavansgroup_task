from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ─── CATEGORY SCHEMAS ────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    """Schema for POST /categories — what the client sends to create a category."""
    name: str


class CategoryUpdate(BaseModel):
    """Schema for PUT /categories/{id} — what the client sends to update a category."""
    name: str


class CategoryOut(BaseModel):
    """Schema for category responses — what we send back to the client."""
    id: int
    name: str
    created_at: datetime
    updated_at: datetime


# ─── PRODUCT SCHEMAS ─────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    """
    Schema for GET /products list.
    product_image contains the full accessible URL, not just a filename.
    """
    id: int
    name: str
    product_image: Optional[str] = None
    price: float
    category_ids: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductDetail(BaseModel):
    """
    Schema for GET /product/{id}.
    category_ids CSV is resolved to actual category names.
    product_image contains the full accessible URL.
    """
    id: int
    name: str
    product_image: Optional[str] = None
    price: float
    category_names: str
    created_at: datetime
    updated_at: datetime
