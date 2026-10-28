"""
main.py — FastAPI application entry point.

Run locally:
    uvicorn main:app --reload
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from llm.base import LLMError, LLMValidationError
from routers import auth, knowledge_base, meta, projects, scenes

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Emotional Mapping API",
    version="1.0.0",
    description="Backend decision-support API for Emotional Mapping: AI-Powered Filmmaking & Audience Response Analysis",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers (Consistent Error Contract) ──────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Uniform error format for all HTTPException instances."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"http_{exc.status_code}",
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Uniform error format for request body/query validation failures."""
    errors = exc.errors()
    msg = errors[0].get("msg", "Invalid request data.") if errors else "Validation failed."
    field = " -> ".join(str(loc) for loc in errors[0].get("loc", [])) if errors else ""
    full_message = f"{field}: {msg}" if field else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": full_message,
                "details": errors,
            }
        },
    )


@app.exception_handler(LLMValidationError)
async def llm_validation_exception_handler(request: Request, exc: LLMValidationError):
    """Map LLM parsing failures to HTTP 502 with a safe, descriptive message."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"code": "ai_validation_error", "message": exc.message}},
    )


@app.exception_handler(LLMError)
async def llm_exception_handler(request: Request, exc: LLMError):
    """Map general upstream LLM errors to HTTP 503 with a safe message."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": {"code": "ai_service_error", "message": exc.message}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all to guarantee unhandled exceptions return informative messages."""
    logger.exception("Unhandled server exception: %s", exc)
    error_msg = f"{type(exc).__name__}: {str(exc)}"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": error_msg,
            }
        },
    )


# ── Routers (Mounted under /api/v1) ───────────────────────────────────────────
api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(auth.router)
api_v1.include_router(meta.router)
api_v1.include_router(projects.router)
api_v1.include_router(scenes.router)
api_v1.include_router(knowledge_base.router)

app.include_router(api_v1)


# ── Health Checks ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """Liveness probe for Render, Vercel, and uptime monitoring."""
    return {
        "status": "ok",
        "environment": settings.env,
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=(settings.env == "development"))
