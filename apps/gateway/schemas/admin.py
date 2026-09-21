from typing import List, Optional
from pydantic import BaseModel, Field


class KeyCreateRequest(BaseModel):
    tenant: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    rate_limit_rpm: int = Field(60, ge=1, le=100000, description="Rate limit in requests per minute")
    max_concurrency: int = Field(10, ge=1, le=10000, description="Maximum concurrent connections")
    key: Optional[str] = Field(None, description="Explicit API key (optional, default auto-generated)")


class KeyCreateResponse(BaseModel):
    id: str
    tenant: str
    key: str
    key_prefix: str
    rate_limit_rpm: int
    max_concurrency: int
    created_at: str


class KeyItemResponse(BaseModel):
    id: str
    tenant: str
    key_prefix: str
    rate_limit_rpm: int
    max_concurrency: int
    is_active: bool
    revoked_at: Optional[str] = None
    created_at: str


class KeyListResponse(BaseModel):
    data: List[KeyItemResponse]


class RouteDetail(BaseModel):
    id: str
    provider_name: str
    provider_type: str
    upstream_model: str
    priority: int
    is_enabled: bool
    route_key: str
    breaker_state: str  # CLOSED, OPEN, HALF_OPEN


class PolicyDetail(BaseModel):
    id: str
    alias: str
    description: Optional[str] = None
    max_retries: int
    timeout_ms: int
    routes: List[RouteDetail]


class RoutesListResponse(BaseModel):
    data: List[PolicyDetail]


class BreakerActionRequest(BaseModel):
    route_key: str


class BreakerActionResponse(BaseModel):
    route_key: str
    breaker_state: str
    message: str


class OverviewResponse(BaseModel):
    total_keys: int
    active_keys: int
    total_policies: int
    total_routes: int
    open_breakers_count: int
    total_requests: int
    avg_duration_ms: float
    gateway_version: str
    live_gemini_configured: bool
    live_openrouter_configured: bool
    live_commandcode_configured: bool = False
