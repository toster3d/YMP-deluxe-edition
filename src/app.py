import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import uvicorn.config
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from redis.exceptions import RedisError

from config import get_settings
from extensions import Base, async_engine
from routes import router
from src.token_storage import RedisTokenStorage

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="v2/api/auth/login",
    scheme_name="JWT"
)

async def initialize_database() -> None:
    async with async_engine.begin() as conn:
        def inspect_tables(sync_conn: Any) -> list[str]:
            return sync_conn.get_bind().table_names()
            
        tables = await conn.run_sync(inspect_tables)
        required_tables = {"users", "recipes", "user_plan"}
        
        if not required_tables.issubset(tables):
            print("Creating missing tables...")
            await conn.run_sync(Base.metadata.create_all)
        else:
            print("All required tables already exist")


async def get_redis() -> AsyncGenerator[Redis[str], None]:
    """Get Redis client from the pool."""
    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    try:
        # Verify connection
        if not await redis_client.ping():
            raise RedisError("Redis ping failed")
            
        yield redis_client
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection error: {str(e)}"
        )
    finally:
        await redis_client.close()

async def get_token_storage(redis: Redis[str] = Depends(get_redis)) -> RedisTokenStorage:
    """Get token storage instance."""
    return RedisTokenStorage(redis)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown events."""
    await initialize_database()
    yield  # This will allow the application to run
    # Here you can add any shutdown logic if needed

def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="YMP API",
        description="Your Modern Project API",
        version="2.0.0",
        docs_url="/v2/docs",
        redoc_url="/v2/redoc",
        openapi_url="/v2/openapi.json",
        lifespan=lifespan  # Set the lifespan context manager here
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        router,
        prefix="/v2",
        dependencies=[Depends(oauth2_scheme)],
        tags=["v2"]
    )

    return app

# Create the FastAPI app
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="debug" if settings.debug else "info"
    )