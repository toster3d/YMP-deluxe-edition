import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Never

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from config import get_settings
from extensions import Base, async_engine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

settings = get_settings()


async def initialize_database() -> None:
    """Initialize database tables if they don't exist."""
    try:
        async with async_engine.begin() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            required_tables = {"users", "recipes", "user_plan"}

            if not required_tables.issubset(tables):
                print("Creating missing tables...")
                await conn.run_sync(Base.metadata.create_all)
                print("Tables created successfully")
            else:
                print("All required tables already exist")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    await initialize_database()
    yield


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Your Meal Planner API",
        description="API for meal planning and recipe management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from routes import router

    app.include_router(router)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    def run_server() -> Never:
        """Run the server."""
        uvicorn.run(
            "app:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            proxy_headers=True,
            forwarded_allow_ips="*",
            log_level="debug" if settings.debug else "info"
        )
        raise SystemExit(0)

    run_server()
