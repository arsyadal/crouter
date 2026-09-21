import os
import time
import uuid
import re
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("crouter.tracing")

# Current active span context variable (async-safe)
_current_span: ContextVar[Optional["Span"]] = ContextVar("crouter_current_span", default=None)

# Buffer of recent completed spans for observability / inspection
_completed_spans: List["Span"] = []
MAX_STORED_SPANS = 1000

TRACEPARENT_REGEX = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


class Span:
    """Represents an OpenTelemetry-compatible distributed tracing span."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.attributes: Dict[str, Any] = attributes or {}
        self.status: str = "UNSET"
        self.error_message: Optional[str] = None

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_status(self, status: str, error_message: Optional[str] = None) -> None:
        self.status = status
        if error_message:
            self.error_message = str(error_message)

    def finish(self) -> None:
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        if self.status == "UNSET":
            self.status = "OK"

        # Record into recent spans ring buffer
        _completed_spans.append(self)
        if len(_completed_spans) > MAX_STORED_SPANS:
            _completed_spans.pop(0)

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-01"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error_message": self.error_message,
            "attributes": self.attributes,
        }


class SpanContextManager:
    """Async & sync context manager for span lifecycle."""

    def __init__(self, span: Span):
        self.span = span
        self.token = None

    def __enter__(self) -> Span:
        self.token = _current_span.set(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_status("ERROR", str(exc_val))
            self.span.set_attribute("error.type", exc_type.__name__)
        self.span.finish()
        if self.token:
            _current_span.reset(self.token)
        return False  # Do not suppress exception

    async def __aenter__(self) -> Span:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


class OpenTelemetryTracer:
    """W3C OpenTelemetry distributed tracer with zero mandatory external dependencies."""

    @staticmethod
    def generate_trace_id() -> str:
        return uuid.uuid4().hex  # 32 hex chars

    @staticmethod
    def generate_span_id() -> str:
        return uuid.uuid4().hex[:16]  # 16 hex chars

    @staticmethod
    def extract_traceparent(header_val: Optional[str]) -> Optional[Tuple[str, str]]:
        if not header_val:
            return None
        m = TRACEPARENT_REGEX.match(header_val.strip().lower())
        if m:
            return m.group(1), m.group(2)
        return None

    def start_span(
        self,
        name: str,
        incoming_traceparent: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContextManager:
        parent = _current_span.get()
        if incoming_traceparent:
            extracted = self.extract_traceparent(incoming_traceparent)
            if extracted:
                trace_id, parent_span_id = extracted
            else:
                trace_id = self.generate_trace_id()
                parent_span_id = None
        elif parent:
            trace_id = parent.trace_id
            parent_span_id = parent.span_id
        else:
            trace_id = self.generate_trace_id()
            parent_span_id = None

        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=self.generate_span_id(),
            parent_span_id=parent_span_id,
            attributes=attributes,
        )
        return SpanContextManager(span)

    @staticmethod
    def get_current_span() -> Optional[Span]:
        return _current_span.get()

    @staticmethod
    def get_current_trace_id() -> Optional[str]:
        s = _current_span.get()
        return s.trace_id if s else None

    @staticmethod
    def get_current_traceparent() -> Optional[str]:
        s = _current_span.get()
        return s.traceparent if s else None

    @staticmethod
    def get_recent_spans(limit: int = 50) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in reversed(_completed_spans[-limit:])]

    @staticmethod
    def reset() -> None:
        _completed_spans.clear()


tracer = OpenTelemetryTracer()
