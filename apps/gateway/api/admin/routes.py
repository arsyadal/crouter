from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.gateway.api.deps import get_db, get_circuit_breaker
from apps.gateway.engine.breaker import CircuitBreaker, CircuitState
from apps.gateway.models.entities import RoutingPolicy, ModelRoute, Provider
from apps.gateway.schemas.admin import (
    RoutesListResponse,
    PolicyDetail,
    RouteDetail,
    BreakerActionRequest,
    BreakerActionResponse,
)

router = APIRouter(tags=["Admin - Routes & Circuit Breakers"])


@router.get("/routes", response_model=RoutesListResponse)
async def list_routes(
    db: AsyncSession = Depends(get_db),
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """List all configured model aliases, their fallback chains, and real-time circuit breaker status."""
    stmt = (
        select(RoutingPolicy)
        .options(
            selectinload(RoutingPolicy.routes).selectinload(ModelRoute.provider)
        )
        .order_by(RoutingPolicy.alias)
    )
    result = await db.execute(stmt)
    policies = result.scalars().all()

    policy_details: List[PolicyDetail] = []
    for pol in policies:
        routes_sorted = sorted(pol.routes, key=lambda r: r.priority)
        route_items: List[RouteDetail] = []
        for r in routes_sorted:
            prov_name = r.provider.name if r.provider else "unknown"
            prov_type = r.provider.provider_type if r.provider else "unknown"
            route_key = f"{prov_name}:{r.upstream_model}"
            state = await breaker.get_state(route_key)
            route_items.append(
                RouteDetail(
                    id=r.id,
                    provider_name=prov_name,
                    provider_type=prov_type,
                    upstream_model=r.upstream_model,
                    priority=r.priority,
                    is_enabled=r.is_enabled,
                    route_key=route_key,
                    breaker_state=state.value,
                )
            )
        policy_details.append(
            PolicyDetail(
                id=pol.id,
                alias=pol.alias,
                description=pol.description,
                max_retries=pol.max_retries,
                timeout_ms=pol.timeout_ms,
                routes=route_items,
            )
        )

    # If DB has no policies yet (e.g. unseeded test or memory run), provide default mock routes
    if not policy_details:
        state_a = await breaker.get_state("mock-a:mock-deterministic")
        state_b = await breaker.get_state("mock-b:mock-deterministic")
        policy_details = [
            PolicyDetail(
                id="default-policy",
                alias="auto/coding",
                description="Default auto-coding fallback policy",
                max_retries=2,
                timeout_ms=5000,
                routes=[
                    RouteDetail(
                        id="route-mock-a",
                        provider_name="mock-a",
                        provider_type="mock",
                        upstream_model="mock-deterministic",
                        priority=1,
                        is_enabled=True,
                        route_key="mock-a:mock-deterministic",
                        breaker_state=state_a.value,
                    ),
                    RouteDetail(
                        id="route-mock-b",
                        provider_name="mock-b",
                        provider_type="mock",
                        upstream_model="mock-deterministic",
                        priority=2,
                        is_enabled=True,
                        route_key="mock-b:mock-deterministic",
                        breaker_state=state_b.value,
                    ),
                ],
            )
        ]

    return RoutesListResponse(data=policy_details)


@router.post("/breaker/reset", response_model=BreakerActionResponse)
async def reset_breaker(
    req: BreakerActionRequest,
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """Reset the circuit breaker for a given route key to CLOSED."""
    route_key = req.route_key.strip()
    if not route_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route key cannot be empty or whitespace.",
        )

    await breaker.reset(route_key)
    state = await breaker.get_state(route_key)
    return BreakerActionResponse(
        route_key=route_key,
        breaker_state=state.value,
        message=f"Circuit breaker for '{route_key}' successfully reset to {state.value}.",
    )


@router.post("/breaker/trip", response_model=BreakerActionResponse)
async def trip_breaker(
    req: BreakerActionRequest,
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """Force-trip the circuit breaker for a given route key to OPEN (for simulation/testing)."""
    route_key = req.route_key.strip()
    if not route_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Route key cannot be empty or whitespace.",
        )

    await breaker.trip(route_key)
    state = await breaker.get_state(route_key)
    return BreakerActionResponse(
        route_key=route_key,
        breaker_state=state.value,
        message=f"Circuit breaker for '{route_key}' forced to {state.value}.",
    )
