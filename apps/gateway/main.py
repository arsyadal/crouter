import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from apps.gateway.api.deps import init_db, init_redis, close_redis
from apps.gateway.api.health import router as health_router
from apps.gateway.api.v1.chat import router as chat_router
from apps.gateway.api.v1.models import router as models_router
from apps.gateway.api.admin import admin_router
from apps.gateway.api.admin.dashboard import router as dashboard_router
from apps.gateway.api.admin.landing import router as landing_router
from apps.gateway.core.config import settings
from apps.gateway.core.errors import CRouterException
from apps.gateway.core.telemetry import metrics, scrub_sensitive_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("crouter.gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CRouter database...")
    await init_db()
    logger.info("Initializing Redis & engine singletons...")
    await init_redis()
    logger.info("CRouter Gateway started successfully.")
    yield
    logger.info("CRouter Gateway shutting down...")
    await close_redis()


app = FastAPI(
    title="CRouter: Multi-Provider AI Inference Gateway",
    description="One Gateway. Every Model. Resilient, OpenAI-compatible AI gateway.",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def privacy_and_telemetry_middleware(request: Request, call_next):
    """Zero-leak request middleware ensuring secrets and PII are redacted from logs and trace contexts."""
    from apps.gateway.core.tracing import tracer

    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    incoming_traceparent = request.headers.get("traceparent")
    # Verify header scrubbing
    scrubbed_headers = scrub_sensitive_data(dict(request.headers))
    logger.debug(
        f"Incoming {request.method} {request.url.path} [req_id={req_id}] headers={scrubbed_headers}"
    )

    async with tracer.start_span(
        f"{request.method} {request.url.path}",
        incoming_traceparent=incoming_traceparent,
        attributes={"http.method": request.method, "http.url": str(request.url), "request_id": req_id},
    ) as span:
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        if "X-CRouter-Request-ID" not in response.headers:
            response.headers["X-CRouter-Request-ID"] = req_id
        response.headers["X-Trace-ID"] = span.trace_id
        response.headers["traceparent"] = span.traceparent
        return response


@app.exception_handler(CRouterException)
async def crouter_exception_handler(request: Request, exc: CRouterException):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    content = exc.to_dict(request_id=req_id)
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    errors = exc.errors()
    first_err = errors[0] if errors else {}
    loc = ".".join(str(l) for l in first_err.get("loc", []))
    msg = first_err.get("msg", "Validation error")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": f"Invalid request parameter at '{loc}': {msg}",
                "type": "invalid_request_error",
                "code": "invalid_request_error",
                "param": loc or None,
                "request_id": req_id,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    logger.error(f"Unhandled server error [req_id={req_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An internal gateway error occurred.",
                "type": "internal_error",
                "code": "internal_server_error",
                "param": None,
                "request_id": req_id,
            }
        },
    )


# Mount routers
app.include_router(health_router)
app.include_router(chat_router, prefix="/v1")
app.include_router(models_router, prefix="/v1")
app.include_router(admin_router)
app.include_router(dashboard_router)
app.include_router(landing_router)


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics scrape endpoint."""
    return metrics.export_prometheus()


CROUTER_FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
  <rect width="32" height="32" rx="7" fill="#18181b"/>
  <path d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3" 
        stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="15" cy="16" r="2.2" fill="#10b981"/>
  <path d="M6 16H12.8" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
  <path d="M15 13.8V11.2L18.5 8.5" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="18.5" cy="8.5" r="1.3" fill="#ffffff"/>
  <path d="M15 18.2V20.8L18.5 23.5" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="18.5" cy="23.5" r="1.3" fill="#ffffff"/>
</svg>"""


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
async def get_favicon():
    """Serve the official CRouter browser tab favicon."""
    return Response(content=CROUTER_FAVICON_SVG, media_type="image/svg+xml")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.GATEWAY_HOST, port=settings.GATEWAY_PORT)
