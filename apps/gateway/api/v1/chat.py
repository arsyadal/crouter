import json
import time
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Header
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gateway.api.deps import (
    get_db,
    get_authenticated_key,
    get_rate_limiter,
    get_concurrency_leaser,
    get_routing_engine,
)
from apps.gateway.core.errors import RateLimitExceededError, UpstreamProviderError
from apps.gateway.core.telemetry import metrics
from apps.gateway.models.entities import APIKey, RequestEvent
from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)

logger = logging.getLogger("crouter.api.chat")
router = APIRouter(tags=["Chat Completions"])


@router.post("/chat/completions")
async def chat_completions(
    request_body: ChatCompletionRequest,
    raw_request: Request,
    api_key: APIKey = Depends(get_authenticated_key),
    db: AsyncSession = Depends(get_db),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    request_id = x_request_id or f"req_{uuid.uuid4().hex[:16]}"
    start_time = time.perf_counter()

    limiter = get_rate_limiter()
    concurrency_leaser = get_concurrency_leaser()
    routing_engine = get_routing_engine()

    # 1. Rate Limiting Check
    allowed, retry_after = await limiter.check_rate_limit(
        api_key.id, api_key.rate_limit_rpm
    )
    if not allowed:
        metrics.inc_request(request_body.model, "none", 429)
        raise RateLimitExceededError(
            f"Rate limit exceeded for API key. Quota resets in {retry_after} seconds.",
            retry_after=retry_after,
        )

    # 2. Concurrency Lease Check
    acquired, active = await concurrency_leaser.acquire(
        api_key.id, api_key.max_concurrency
    )
    if not acquired:
        metrics.inc_request(request_body.model, "none", 429)
        raise RateLimitExceededError(
            f"Concurrency ceiling of {api_key.max_concurrency} exceeded for API key.",
            retry_after=1,
        )

    metrics.set_in_flight(api_key.tenant_id or "default", active)

    # 3. Handle Streaming vs Non-Streaming
    if request_body.stream:
        try:
            (
                chunk_stream,
                selected_route,
                attempts,
            ) = await routing_engine.execute_streaming(request_body, db=db)
        except Exception as e:
            await concurrency_leaser.release(api_key.id)
            status_code = getattr(e, "status_code", 500)
            metrics.inc_request(request_body.model, "none", status_code)
            try:
                event = RequestEvent(
                    tenant_id=api_key.tenant_id,
                    request_id=request_id,
                    model_alias=request_body.model,
                    selected_provider="none",
                    status_code=status_code,
                    duration_ms=int((time.perf_counter() - start_time) * 1000.0),
                    prompt_tokens=max(1, sum(len(m.content) for m in request_body.messages) // 4),
                    completion_tokens=0,
                )
                db.add(event)
                await db.commit()
            except Exception:
                pass
            raise e

        async def sse_generator():
            chunks_count = 0
            final_status = 200
            try:
                async for chunk in chunk_stream:
                    chunks_count += 1
                    payload = chunk.model_dump_json()
                    yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as stream_exc:
                final_status = 502
                logger.error(f"Stream error after {chunks_count} chunks: {stream_exc}")
                # Record breaker failure for mid-stream disconnect
                await routing_engine.circuit_breaker.record_failure(selected_route.route_key)
                error_payload = json.dumps(
                    {
                        "error": {
                            "message": "Stream interrupted by upstream provider.",
                            "type": "stream_error",
                            "code": "upstream_stream_interrupted",
                            "request_id": request_id,
                        }
                    }
                )
                yield f"data: {error_payload}\n\n"
            finally:
                await concurrency_leaser.release(api_key.id)
                duration_ms = int((time.perf_counter() - start_time) * 1000.0)
                metrics.observe_duration(duration_ms / 1000.0)
                metrics.inc_request(request_body.model, selected_route.provider_name, final_status)
                try:
                    from apps.gateway.api.deps import async_session_maker
                    async with async_session_maker() as audit_session:
                        event = RequestEvent(
                            tenant_id=api_key.tenant_id,
                            request_id=request_id,
                            model_alias=request_body.model,
                            selected_provider=selected_route.provider_name,
                            status_code=final_status,
                            duration_ms=duration_ms,
                            prompt_tokens=max(1, sum(len(m.content) for m in request_body.messages) // 4),
                            completion_tokens=chunks_count,
                        )
                        audit_session.add(event)
                        await audit_session.commit()
                except Exception as audit_err:
                    logger.warning(f"Failed to record streaming audit event: {audit_err}")

        response_headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-CRouter-Request-ID": request_id,
            "X-CRouter-Provider-Selected": selected_route.provider_name,
            "X-CRouter-Model-Selected": selected_route.upstream_model,
            "X-CRouter-Attempts": str(attempts),
        }
        return StreamingResponse(sse_generator(), headers=response_headers, media_type="text/event-stream")

    # Non-streaming Path
    try:
        try:
            (
                completion_response,
                selected_route,
                attempts,
                upstream_latency_ms,
            ) = await routing_engine.execute_non_streaming(request_body, db=db)
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            metrics.inc_request(request_body.model, "none", status_code)
            try:
                event = RequestEvent(
                    tenant_id=api_key.tenant_id,
                    request_id=request_id,
                    model_alias=request_body.model,
                    selected_provider="none",
                    status_code=status_code,
                    duration_ms=int((time.perf_counter() - start_time) * 1000.0),
                    prompt_tokens=max(1, sum(len(m.content) for m in request_body.messages) // 4),
                    completion_tokens=0,
                )
                db.add(event)
                await db.commit()
            except Exception:
                pass
            raise e

        gateway_latency_ms = (time.perf_counter() - start_time) * 1000.0
        metrics.observe_duration(gateway_latency_ms / 1000.0)
        metrics.inc_request(request_body.model, selected_route.provider_name, 200)

        # Audit RequestEvent in DB asynchronously
        try:
            event = RequestEvent(
                tenant_id=api_key.tenant_id,
                request_id=request_id,
                model_alias=request_body.model,
                selected_provider=selected_route.provider_name,
                status_code=200,
                duration_ms=int(gateway_latency_ms),
                prompt_tokens=completion_response.usage.prompt_tokens,
                completion_tokens=completion_response.usage.completion_tokens,
            )
            db.add(event)
            await db.commit()
        except Exception as audit_err:
            logger.warning(f"Failed to record audit event: {audit_err}")

        headers = {
            "X-CRouter-Request-ID": request_id,
            "X-CRouter-Provider-Selected": selected_route.provider_name,
            "X-CRouter-Model-Selected": selected_route.upstream_model,
            "X-CRouter-Attempts": str(attempts),
            "X-CRouter-Latency-Gateway-Ms": f"{gateway_latency_ms:.1f}",
            "X-CRouter-Latency-Upstream-Ms": f"{upstream_latency_ms:.1f}",
        }

        return JSONResponse(
            status_code=200,
            content=completion_response.model_dump(),
            headers=headers,
        )

    finally:
        await concurrency_leaser.release(api_key.id)
