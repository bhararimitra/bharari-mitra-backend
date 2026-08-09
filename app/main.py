"""BharariMitra FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.shared.exceptions import NotFoundError
from app.api.v1 import health, jobs, departments, districts, qualifications, organizations, search, notifications
import app.database.models  # noqa: F401 — register ORM mappers

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    configure_logging()
    settings = get_settings()
    logger.info("bhararimitra_api_starting", version=settings.APP_VERSION)

    # Optional in-process scheduler (prefer dedicated crawler_worker.py)
    if settings.ENABLE_API_SCHEDULER:
        from app.modules.crawlers.scheduler import start_scheduler, stop_scheduler

        start_scheduler()
        logger.info("api_scheduler_enabled")
    else:
        logger.info("api_scheduler_disabled", hint="use scripts/crawler_worker.py")

    yield

    logger.info("bhararimitra_api_stopping")
    if settings.ENABLE_API_SCHEDULER:
        from app.modules.crawlers.scheduler import stop_scheduler

        stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "BharariMitra public API — Maharashtra Government Jobs platform. "
            "Official data only. No authentication required for public endpoints."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    # Routers
    prefix = "/api/v1"
    app.include_router(health.router)
    app.include_router(jobs.router, prefix=prefix)
    app.include_router(notifications.router, prefix=prefix)
    app.include_router(departments.router, prefix=prefix)
    app.include_router(districts.router, prefix=prefix)
    app.include_router(qualifications.router, prefix=prefix)
    app.include_router(organizations.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)

    return app


app = create_app()
