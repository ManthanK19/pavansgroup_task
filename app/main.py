import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.routers import categories, products

# ─── Logging Setup ────────────────────────────────────────────────────────────
# Errors are logged to console (server-side only).
# Clients NEVER see raw error details — that's the global handler's job.
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Product & Category Management API",
    version="1.0.0",
    description="A REST API for managing products and categories with image uploads.",
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global Exception Handler ─────────────────────────────────────────────────
# Safety net for ALL unhandled errors anywhere in the app.
# Why this matters: without it, FastAPI may leak internal error details (file paths,
# library versions, stack traces) to the client — a security risk.
# This handler logs the real error on the server, returns a clean message to the client.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled error on {request.method} {request.url}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# ─── Custom 422 Validation Error Handler ─────────────────────────────────────
# FastAPI's default 422 response is technically correct but verbose and confusing.
# This reformats it into a cleaner, friendlier structure.
# Example output:
# {
#   "detail": "Validation failed",
#   "errors": [{"field": "body -> price", "message": "value is not a valid float"}]
# }
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )


# ─── Static File Serving ──────────────────────────────────────────────────────
# Ensure the upload directory exists before mounting
os.makedirs("static/uploads", exist_ok=True)

# After this mount, a file saved as "static/uploads/abc.jpg" is accessible at:
# http://localhost:8000/static/uploads/abc.jpg
app.mount("/static/uploads", StaticFiles(directory="static/uploads"), name="uploads")

# ─── Register Routers ─────────────────────────────────────────────────────────
app.include_router(categories.router)
app.include_router(products.router)


@app.get("/", tags=["Root"])
def root():
    """Health check endpoint — confirms the API is running."""
    return {"message": "API is running. Visit /docs for Swagger UI."}
