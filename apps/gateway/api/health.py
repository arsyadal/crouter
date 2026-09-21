from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.gateway.api.deps import get_db, get_redis
from apps.gateway.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def health_live():
    """Liveness probe: returns 200 if gateway process is running."""
    return {"status": "ok"}


@router.get("/ready")
async def health_ready(
    db: AsyncSession = Depends(get_db),
):
    """Readiness probe: checks database and redis connections."""
    db_ok = False
    redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_client = await get_redis()
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    else:
        # If in-memory fallback is enabled, consider redis check passed
        redis_ok = settings.REDIS_FALLBACK_IN_MEMORY

    is_ready = db_ok and redis_ok
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else ("in_memory" if settings.REDIS_FALLBACK_IN_MEMORY else "error"),
        },
    )
