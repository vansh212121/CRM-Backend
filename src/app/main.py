from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from typing import Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exception_handler import register_exception_handlers
from app.db.session import db
from app.utils.deps import get_health_status
from app.db import base
from app.api.v1.endpoints import user, auth,center,appointment


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    await db.connect()
    yield
    await db.disconnect()



def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(center.router)
    app.include_router(appointment.router)

    origins = [
        "http://localhost:5173",  # Vite/React frontend dev server
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_application()


@app.get("/health", response_model=Dict[str, Any])
async def health_check(health: Dict[str, Any] = Depends(get_health_status)):
    """
    Health check endpoint that provides status and version info.
    """
    return health
