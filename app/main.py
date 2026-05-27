import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routers import categories, products
from app.errors import register_exception_handlers

logging.basicConfig(level=logging.ERROR)

app = FastAPI(
    title="Product & Category Management API",
    version="1.0.0",
    description="A REST API for managing products and categories with image uploads.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="static/uploads"), name="uploads")

app.include_router(categories.router)
app.include_router(products.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "API is running. Visit /docs for Swagger UI."}
