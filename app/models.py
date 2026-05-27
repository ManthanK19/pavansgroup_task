from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class ProductOut(BaseModel):
    id: int
    name: str
    product_image: Optional[str] = None
    price: float
    category_ids: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductDetail(BaseModel):
    """Single-product view where category IDs are resolved to their names."""
    id: int
    name: str
    product_image: Optional[str] = None
    price: float
    category_names: str
    created_at: datetime
    updated_at: datetime
