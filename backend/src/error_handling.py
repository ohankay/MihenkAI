"""Error handling and middleware for the FastAPI application."""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle errors."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                "Unhandled exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                    "error_type": type(exc).__name__
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal server error occurred",
                    "error_type": type(exc).__name__
                }
            )


def setup_error_handlers(app: FastAPI):
    """Setup error handlers for the FastAPI app."""
    
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        # Pydantic v2: exc.errors() may contain ctx['error'] = Exception instance
        # which is not JSON-serializable — convert to strings before serializing.
        safe_errors = []
        for err in exc.errors():
            e = dict(err)
            if "ctx" in e:
                e["ctx"] = {
                    k: str(v) if isinstance(v, Exception) else v
                    for k, v in e["ctx"].items()
                }
            # Remove url field added by pydantic v2 (verbose, not useful to clients)
            e.pop("url", None)
            safe_errors.append(e)
        logger.warning(
            "Validation error",
            extra={"path": request.url.path, "errors": safe_errors}
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed",
                "errors": safe_errors,
            },
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors."""
        logger.warning(
            "Value error",
            extra={
                "path": request.url.path,
                "error": str(exc)
            }
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc) or "Invalid value provided"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "error": str(exc),
                "error_type": type(exc).__name__
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred"
            }
        )
    
    # Add middleware
    app.add_middleware(ErrorHandlingMiddleware)
