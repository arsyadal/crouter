import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from apps.gateway.api.deps import init_db
from apps.gateway.api.health import router as health_router
from apps.gateway.api.v1.chat import router as chat_router
from apps.gateway.api.v1.models import router as models_router
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
    logger.info("CRouter Gateway started successfully.")
    yield
    logger.info("CRouter Gateway shutting down...")


app = FastAPI(
    title="CRouter — Multi-Provider AI Inference Gateway",
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
)


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


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics scrape endpoint."""
    return metrics.export_prometheus()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.GATEWAY_HOST, port=settings.GATEWAY_PORT)
