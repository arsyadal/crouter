from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.gateway.api.deps import get_db, get_circuit_breaker
from apps.gateway.core.config import settings
from apps.gateway.engine.breaker import CircuitBreaker, CircuitState
from apps.gateway.models.entities import APIKey, RoutingPolicy, ModelRoute, RequestEvent
from apps.gateway.schemas.admin import OverviewResponse

router = APIRouter(tags=["Admin - Overview"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """Retrieve gateway overview telemetry and operational health."""
    # Count keys
    stmt_keys = select(APIKey).options(selectinload(APIKey.tenant))
    res_keys = await db.execute(stmt_keys)
    all_keys = res_keys.scalars().all()
    total_keys = len(all_keys)
    active_keys = sum(1 for k in all_keys if k.is_active)

    # Count policies and routes
    stmt_pol = (
        select(RoutingPolicy)
        .options(
            selectinload(RoutingPolicy.routes).selectinload(ModelRoute.provider)
        )
    )
    res_pol = await db.execute(stmt_pol)
    policies = res_pol.scalars().all()
    total_policies = len(policies)
    total_routes = sum(len(p.routes) for p in policies)

    # Count open breakers
    open_breakers = 0
    if total_policies > 0:
        for p in policies:
            for r in p.routes:
                prov_name = r.provider.name if r.provider else "unknown"
                route_key = f"{prov_name}:{r.upstream_model}"
                st = await breaker.get_state(route_key)
                if st == CircuitState.OPEN:
                    open_breakers += 1
    else:
        # Fallback to default built-in policy counts matching routes endpoint
        total_policies = 2
        total_routes = 5
        default_keys = [
            "mock-a:mock-deterministic",
            "mock-b:mock-deterministic",
            "gemini:gemini-1.5-flash",
            "openrouter:meta-llama/llama-3.2-3b-instruct:free",
        ]
        for rk in default_keys:
            st = await breaker.get_state(rk)
            if st == CircuitState.OPEN:
                open_breakers += 1

    # Aggregate request events
    stmt_events = select(
        func.count(RequestEvent.id),
        func.coalesce(func.avg(RequestEvent.duration_ms), 0.0),
    )
    res_events = await db.execute(stmt_events)
    row = res_events.first()
    total_requests = row[0] if row else 0
    avg_duration = float(row[1]) if row else 0.0

    return OverviewResponse(
        total_keys=total_keys,
        active_keys=active_keys,
        total_policies=total_policies,
        total_routes=total_routes,
        open_breakers_count=open_breakers,
        total_requests=total_requests,
        avg_duration_ms=round(avg_duration, 1),
        gateway_version=settings.VERSION,
        live_gemini_configured=bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 0),
        live_openrouter_configured=bool(settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY.strip()) > 0),
    )
