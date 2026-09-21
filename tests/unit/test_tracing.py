import pytest
from apps.gateway.core.tracing import tracer, Span


def test_tracer_span_creation_and_lifecycle():
    tracer.reset()
    with tracer.start_span("test.parent", attributes={"env": "test"}) as parent:
        assert len(parent.trace_id) == 32
        assert len(parent.span_id) == 16
        assert parent.parent_span_id is None
        assert parent.attributes["env"] == "test"

        with tracer.start_span("test.child", attributes={"subsystem": "auth"}) as child:
            assert child.trace_id == parent.trace_id
            assert child.parent_span_id == parent.span_id
            assert child.attributes["subsystem"] == "auth"

    spans = tracer.get_recent_spans(limit=10)
    assert len(spans) == 2
    parent_dict = spans[0]
    child_dict = spans[1]
    assert parent_dict["name"] == "test.parent"
    assert child_dict["name"] == "test.child"
    assert child_dict["trace_id"] == parent_dict["trace_id"]
    assert child_dict["parent_span_id"] == parent_dict["span_id"]


def test_traceparent_parsing():
    raw = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parsed = tracer.extract_traceparent(raw)
    assert parsed is not None
    trace_id, span_id = parsed
    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert span_id == "00f067aa0ba902b7"

    with tracer.start_span("external.propagated", incoming_traceparent=raw) as s:
        assert s.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert s.parent_span_id == "00f067aa0ba902b7"
        assert s.traceparent.startswith("00-4bf92f3577b34da6a3ce929d0e0e4736-")
