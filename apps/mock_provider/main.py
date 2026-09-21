import asyncio
import json
import time
import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, Query, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="CRouter Deterministic Mock Provider", version="1.0.0")

# In-memory fault registry: target_id -> fault_dict
fault_registry: Dict[str, Dict[str, Any]] = {}


class FaultInjectionRequest(BaseModel):
    target: Optional[str] = "mock-a"
    status: int = 503
    latency_ms: int = 0
    drop_after_chunks: Optional[int] = None
    message: Optional[str] = None


@app.get("/health/live")
async def health_live():
    return {"status": "ok", "service": "mock_provider"}


@app.post("/mock/inject-fault")
async def inject_fault(
    target: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    latency_ms: Optional[int] = Query(None),
    drop_after_chunks: Optional[int] = Query(None),
    body: Optional[FaultInjectionRequest] = None,
):
    """Inject programmable faults for specific provider targets (e.g. mock-a)."""
    t = target or (body.target if body and body.target else "mock-a")
    st = status if status is not None else (body.status if body and body.status is not None else 503)
    lat = latency_ms if latency_ms is not None else (body.latency_ms if body and body.latency_ms is not None else 0)
    drop = drop_after_chunks if drop_after_chunks is not None else (body.drop_after_chunks if body else None)
    msg = body.message if body and body.message else f"Injected fault {st} for {t}"

    fault_registry[t] = {
        "status": st,
        "latency_ms": lat,
        "drop_after_chunks": drop,
        "message": msg,
    }
    return {"status": "injected", "target": t, "fault": fault_registry[t]}


@app.post("/mock/reset")
async def reset_faults():
    """Reset all injected faults."""
    fault_registry.clear()
    return {"status": "reset", "active_faults": {}}


@app.get("/mock/status")
async def get_faults():
    return {"active_faults": fault_registry}


async def _handle_chat_completion(
    request: Request,
    target_from_path: Optional[str] = None,
    x_mock_target: Optional[str] = Header(None, alias="X-Mock-Target"),
    x_crouter_target: Optional[str] = Header(None, alias="X-CRouter-Target-Provider"),
    x_mock_status: Optional[int] = Header(None, alias="X-Mock-Status"),
    x_mock_latency: Optional[int] = Header(None, alias="X-Mock-Latency"),
    x_mock_drop: Optional[int] = Header(None, alias="X-Mock-Drop-After"),
    query_status: Optional[int] = Query(None, alias="status"),
    query_latency: Optional[int] = Query(None, alias="latency"),
    query_drop: Optional[int] = Query(None, alias="drop_after"),
):
    body = await request.json()
    model = body.get("model", "mock-deterministic")
    messages = body.get("messages", [])
    stream = body.get("stream", False)

    target = target_from_path or x_crouter_target or x_mock_target
    if not target:
        if "mock-a" in model:
            target = "mock-a"
        elif "mock-b" in model:
            target = "mock-b"
        else:
            target = "default"

    # Check for direct parameter override or registry fault
    fault = fault_registry.get(target, {})
    status_code = query_status or x_mock_status or fault.get("status", 200)
    latency_ms = query_latency or x_mock_latency or fault.get("latency_ms", 0)
    drop_after = query_drop or x_mock_drop or fault.get("drop_after_chunks")

    if latency_ms > 0:
        await asyncio.sleep(latency_ms / 1000.0)

    if status_code != 200:
        error_type = (
            "rate_limit_error" if status_code == 429 else "upstream_service_error"
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "message": fault.get(
                        "message", f"Mock provider simulated error {status_code}"
                    ),
                    "type": error_type,
                    "code": f"mock_error_{status_code}",
                }
            },
        )

    # Determine response content
    last_user_prompt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_prompt = m.get("content", "")
            break

    response_text = f"Mock response from [{target} ({model})] answering: '{last_user_prompt[:50]}'"
    completion_id = f"chatcmpl_cr_mock_{uuid.uuid4().hex[:12]}"
    now = int(time.time())

    if stream:

        async def event_generator():
            words = response_text.split()
            chunks_emitted = 0
            for i, word in enumerate(words):
                if drop_after is not None and chunks_emitted >= drop_after:
                    # Simulate sudden network drop/upstream stream abort
                    error_payload = {
                        "error": {
                            "message": "Upstream dropped connection mid-stream",
                            "code": "simulated_drop",
                        }
                    }
                    yield f"data: {json.dumps(error_payload)}\n\n"
                    return

                chunk_payload = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": now,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant" if i == 0 else None,
                                "content": word + (" " if i < len(words) - 1 else ""),
                            },
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk_payload)}\n\n"
                chunks_emitted += 1
                await asyncio.sleep(0.02)  # realistic small delay between tokens

            if drop_after is not None and chunks_emitted >= drop_after:
                raise RuntimeError("Simulated mid-stream network drop before done")

            # Final chunk
            final_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": now,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Non-streaming response
    prompt_tokens = max(1, len(last_user_prompt) // 4)
    completion_tokens = max(1, len(response_text) // 4)

    return JSONResponse(
        status_code=200,
        content={
            "id": completion_id,
            "object": "chat.completion",
            "created": now,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        },
    )


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    x_mock_target: Optional[str] = Header(None, alias="X-Mock-Target"),
    x_crouter_target: Optional[str] = Header(None, alias="X-CRouter-Target-Provider"),
    x_mock_status: Optional[int] = Header(None, alias="X-Mock-Status"),
    x_mock_latency: Optional[int] = Header(None, alias="X-Mock-Latency"),
    x_mock_drop: Optional[int] = Header(None, alias="X-Mock-Drop-After"),
    status: Optional[int] = Query(None),
    latency: Optional[int] = Query(None),
    drop_after: Optional[int] = Query(None),
):
    return await _handle_chat_completion(
        request=request,
        target_from_path=None,
        x_mock_target=x_mock_target,
        x_crouter_target=x_crouter_target,
        x_mock_status=x_mock_status,
        x_mock_latency=x_mock_latency,
        x_mock_drop=x_mock_drop,
        query_status=status,
        query_latency=latency,
        query_drop=drop_after,
    )


@app.post("/{target}/v1/chat/completions")
async def chat_completions_for_target(
    target: str,
    request: Request,
    x_mock_target: Optional[str] = Header(None, alias="X-Mock-Target"),
    x_crouter_target: Optional[str] = Header(None, alias="X-CRouter-Target-Provider"),
    x_mock_status: Optional[int] = Header(None, alias="X-Mock-Status"),
    x_mock_latency: Optional[int] = Header(None, alias="X-Mock-Latency"),
    x_mock_drop: Optional[int] = Header(None, alias="X-Mock-Drop-After"),
    status: Optional[int] = Query(None),
    latency: Optional[int] = Query(None),
    drop_after: Optional[int] = Query(None),
):
    return await _handle_chat_completion(
        request=request,
        target_from_path=target,
        x_mock_target=x_mock_target,
        x_crouter_target=x_crouter_target,
        x_mock_status=x_mock_status,
        x_mock_latency=x_mock_latency,
        x_mock_drop=x_mock_drop,
        query_status=status,
        query_latency=latency,
        query_drop=drop_after,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
