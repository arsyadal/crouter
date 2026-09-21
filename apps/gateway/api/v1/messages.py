import json
import time
import uuid
import logging
from typing import Optional, List, Dict, Any, Union, Literal
from fastapi import APIRouter, Depends, Request, Response, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
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
from apps.gateway.engine.token_saver import token_optimizer, is_token_saver_bypassed
from apps.gateway.models.entities import APIKey, RequestEvent
from apps.gateway.schemas.chat import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
)

logger = logging.getLogger("crouter.api.messages")
router = APIRouter(tags=["Anthropic Messages Protocol"])


class AnthropicContentBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = "text"
    text: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Any] = None
    content: Optional[Union[str, List[Any]]] = None


class AnthropicMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: Literal["user", "assistant"]
    content: Union[str, List[Union[AnthropicContentBlock, Dict[str, Any], str]]]


class AnthropicMessagesRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model: str
    messages: List[AnthropicMessage] = Field(..., min_length=1)
    max_tokens: int = Field(default=1024, gt=0)
    system: Optional[Union[str, List[Union[AnthropicContentBlock, Dict[str, Any], str]]]] = None
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: bool = False
    stop_sequences: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None


def _extract_text(content: Union[str, List[Any], None]) -> str:
    """Extract plain text from string or structured Anthropic content blocks."""
    if not content:
        return ""
    if isinstance(content, str):
        return content

    parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                b_type = block.get("type", "text")
                if b_type == "text" and block.get("text"):
                    parts.append(block["text"])
                elif b_type == "tool_result":
                    c = block.get("content")
                    if isinstance(c, str):
                        parts.append(c)
                    elif isinstance(c, list):
                        for sub in c:
                            if isinstance(sub, dict) and sub.get("text"):
                                parts.append(sub["text"])
                elif "text" in block:
                    parts.append(str(block["text"]))
            elif hasattr(block, "text") and block.text:
                parts.append(block.text)
            elif hasattr(block, "content") and block.content:
                parts.append(str(block.content))

    return "\n".join(parts)


@router.post("/messages")
@router.post("/v1/messages")
async def anthropic_messages(
    request_body: AnthropicMessagesRequest,
    raw_request: Request,
    api_key: APIKey = Depends(get_authenticated_key),
    db: AsyncSession = Depends(get_db),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    x_crouter_token_saver: Optional[str] = Header(None, alias="X-CRouter-Token-Saver"),
    anthropic_version: Optional[str] = Header(None, alias="anthropic-version"),
):
    """Native Anthropic Messages API protocol endpoint.

    Translates Anthropic Messages requests bidirectionally to internal router calls,
    supporting streaming SSE and non-streaming responses for Claude Code CLI and Anthropic SDKs.
    """
    request_id = x_request_id or f"msg_req_{uuid.uuid4().hex[:16]}"
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

    # 3. Translate Anthropic Messages -> Internal ChatCompletionRequest
    internal_messages: List[ChatMessage] = []

    if request_body.system:
        system_str = _extract_text(request_body.system)
        if system_str:
            internal_messages.append(ChatMessage(role="system", content=system_str))

    for msg in request_body.messages:
        text_content = _extract_text(msg.content)
        internal_messages.append(ChatMessage(role=msg.role, content=text_content))

    # Apply Deterministic Token Optimizer
    bypass_token_saver = is_token_saver_bypassed(x_crouter_token_saver)
    optimized_messages, tokens_saved = token_optimizer.optimize_messages(
        internal_messages, bypass=bypass_token_saver
    )

    chat_req = ChatCompletionRequest(
        model=request_body.model,
        messages=optimized_messages,
        temperature=request_body.temperature or 1.0,
        max_tokens=request_body.max_tokens,
        stream=request_body.stream,
    )

    # 4. Handle Streaming SSE vs Non-Streaming
    if request_body.stream:
        try:
            (
                chunk_stream,
                selected_route,
                attempts,
            ) = await routing_engine.execute_streaming(chat_req, db=db)
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
                    prompt_tokens=max(1, sum(len(m.content) for m in optimized_messages) // 4),
                    completion_tokens=0,
                )
                db.add(event)
                await db.commit()
            except Exception:
                pass
            raise e

        async def anthropic_sse_generator():
            msg_id = f"msg_{uuid.uuid4().hex[:20]}"
            chunks_count = 0
            final_status = 200
            prompt_tokens_est = max(1, sum(len(m.content) for m in optimized_messages) // 4)

            try:
                # 1. message_start event
                message_start_payload = {
                    "type": "message_start",
                    "message": {
                        "id": msg_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": request_body.model,
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {
                            "input_tokens": prompt_tokens_est,
                            "output_tokens": 1,
                        },
                    },
                }
                yield f"event: message_start\ndata: {json.dumps(message_start_payload)}\n\n"

                # 2. content_block_start event
                content_block_start_payload = {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                }
                yield f"event: content_block_start\ndata: {json.dumps(content_block_start_payload)}\n\n"

                # 3. Stream text chunks as content_block_delta
                async for chunk in chunk_stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        text_delta = chunk.choices[0].delta.content
                        chunks_count += 1
                        delta_payload = {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {"type": "text_delta", "text": text_delta},
                        }
                        yield f"event: content_block_delta\ndata: {json.dumps(delta_payload)}\n\n"

                # 4. content_block_stop event
                content_block_stop_payload = {
                    "type": "content_block_stop",
                    "index": 0,
                }
                yield f"event: content_block_stop\ndata: {json.dumps(content_block_stop_payload)}\n\n"

                # 5. message_delta event
                message_delta_payload = {
                    "type": "message_delta",
                    "delta": {
                        "stop_reason": "end_turn",
                        "stop_sequence": None,
                    },
                    "usage": {
                        "output_tokens": max(1, chunks_count),
                    },
                }
                yield f"event: message_delta\ndata: {json.dumps(message_delta_payload)}\n\n"

                # 6. message_stop event
                message_stop_payload = {"type": "message_stop"}
                yield f"event: message_stop\ndata: {json.dumps(message_stop_payload)}\n\n"

            except Exception as stream_exc:
                final_status = 502
                logger.error(f"Anthropic SSE stream error after {chunks_count} chunks: {stream_exc}")
                await routing_engine.circuit_breaker.record_failure(selected_route.route_key)
                error_payload = {
                    "type": "error",
                    "error": {
                        "type": "api_error",
                        "message": "Stream interrupted by upstream provider.",
                    },
                }
                yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
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
                            prompt_tokens=prompt_tokens_est,
                            completion_tokens=max(1, chunks_count),
                        )
                        audit_session.add(event)
                        await audit_session.commit()
                except Exception as audit_err:
                    logger.warning(f"Failed to record Anthropic audit event: {audit_err}")

        first_chunk_latency_ms = (time.perf_counter() - start_time) * 1000.0
        response_headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "anthropic-version": anthropic_version or "2023-06-01",
            "X-CRouter-Request-ID": request_id,
            "X-CRouter-Provider-Selected": selected_route.provider_name,
            "X-CRouter-Model-Selected": selected_route.upstream_model,
            "X-CRouter-Attempts": str(attempts),
            "X-CRouter-Latency-Gateway-Ms": f"{first_chunk_latency_ms:.1f}",
            "X-CRouter-Tokens-Saved": str(tokens_saved),
        }
        return StreamingResponse(
            anthropic_sse_generator(),
            headers=response_headers,
            media_type="text/event-stream",
        )

    # Non-streaming Path
    try:
        try:
            (
                completion_response,
                selected_route,
                attempts,
                upstream_latency_ms,
            ) = await routing_engine.execute_non_streaming(chat_req, db=db)
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
                    prompt_tokens=max(1, sum(len(m.content) for m in optimized_messages) // 4),
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

        # Audit RequestEvent
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
            logger.warning(f"Failed to record Anthropic non-streaming audit event: {audit_err}")

        # Translate internal response to Anthropic message format
        output_text = (
            completion_response.choices[0].message.content
            if completion_response.choices
            else ""
        )
        finish_reason = (
            completion_response.choices[0].finish_reason
            if completion_response.choices
            else "stop"
        )
        stop_reason = "end_turn"
        if finish_reason == "length":
            stop_reason = "max_tokens"
        elif finish_reason == "tool_calls":
            stop_reason = "tool_use"

        anthropic_response = {
            "id": f"msg_{uuid.uuid4().hex[:20]}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": output_text or "",
                }
            ],
            "model": request_body.model,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": completion_response.usage.prompt_tokens,
                "output_tokens": completion_response.usage.completion_tokens,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "anthropic-version": anthropic_version or "2023-06-01",
            "X-CRouter-Request-ID": request_id,
            "X-CRouter-Provider-Selected": selected_route.provider_name,
            "X-CRouter-Model-Selected": selected_route.upstream_model,
            "X-CRouter-Attempts": str(attempts),
            "X-CRouter-Latency-Gateway-Ms": f"{gateway_latency_ms:.1f}",
            "X-CRouter-Latency-Upstream-Ms": f"{upstream_latency_ms:.1f}",
            "X-CRouter-Tokens-Saved": str(tokens_saved),
        }

        return JSONResponse(
            status_code=200,
            content=anthropic_response,
            headers=headers,
        )

    finally:
        await concurrency_leaser.release(api_key.id)
