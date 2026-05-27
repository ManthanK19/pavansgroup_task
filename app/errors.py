import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


async def _global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled errors. Logs internally, never exposes details to the client."""
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    """Reformat FastAPI's default 422 response into a cleaner structure."""
    errors = [
        {"field": " -> ".join(str(x) for x in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


def register_exception_handlers(app):
    """Register all global exception handlers onto the FastAPI app instance."""
    app.add_exception_handler(Exception, _global_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
