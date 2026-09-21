import time
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.gateway.api.deps import get_db, get_authenticated_key
from apps.gateway.models.entities import RoutingPolicy, APIKey
from apps.gateway.schemas.models import ModelListResponse, ModelItem

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    api_key: APIKey = Depends(get_authenticated_key),
    db: AsyncSession = Depends(get_db),
):
    """List all available model aliases and configured endpoints."""
    stmt = select(RoutingPolicy)
    result = await db.execute(stmt)
    policies = result.scalars().all()

    items = []
    seen = set()

    for p in policies:
        items.append(
            ModelItem(
                id=p.alias,
                object="model",
                created=int(p.id.replace("-", "")[:8], 16)
                if len(p.id) >= 8
                else int(time.time()),
                owned_by="crouter",
            )
        )
        seen.add(p.alias)

    # Add default aliases if not in DB
    defaults = ["auto/coding", "mock-default", "mock-a", "mock-b"]
    for d in defaults:
        if d not in seen:
            items.append(
                ModelItem(
                    id=d,
                    object="model",
                    created=int(time.time()),
                    owned_by="crouter",
                )
            )

    return ModelListResponse(object="list", data=items)
