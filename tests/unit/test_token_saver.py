import pytest
from apps.gateway.engine.token_saver import (
    DeterministicTokenOptimizer,
    is_token_saver_bypassed,
)
from apps.gateway.schemas.chat import ChatMessage


def test_strip_ansi_sequences():
    optimizer = DeterministicTokenOptimizer()
    raw = "\x1b[31mError:\x1b[0m Failed with code \x1b[32;1m1\x1b[0m"
    cleaned = optimizer.strip_ansi(raw)
    assert cleaned == "Error: Failed with code 1"
    assert "\x1b" not in cleaned


def test_compact_diffs_lockfile():
    optimizer = DeterministicTokenOptimizer()
    diff_text = """diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -10,25 +10,25 @@
+    "foo": "1.0.0",
+    "bar": "2.0.0",
+    "baz": "3.0.0",
+    "qux": "4.0.0",
+    "quux": "5.0.0",
+    "corge": "6.0.0",
+    "grault": "7.0.0",
+    "garply": "8.0.0",
+    "waldo": "9.0.0",
+    "fred": "10.0.0",
"""
    compacted = optimizer.compact_diffs(diff_text)
    assert "compacted" in compacted
    assert len(compacted.splitlines()) < len(diff_text.splitlines())


def test_deduplicate_repetitive_linter_lines():
    optimizer = DeterministicTokenOptimizer()
    lines = [
        "src/app.ts:10:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:11:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:12:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:13:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:14:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:15:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:16:5: error: Type 'string' is not assignable to type 'number'.",
        "src/app.ts:17:5: error: Type 'string' is not assignable to type 'number'.",
        "Done with 8 errors.",
    ]
    raw = "\n".join(lines)
    compacted = optimizer.deduplicate_linter_lines(raw, max_repeats=3)
    assert "repetitive diagnostic lines truncated" in compacted
    assert len(compacted.splitlines()) < len(lines)


def test_collapse_identical_lines():
    optimizer = DeterministicTokenOptimizer()
    lines = ["Scanning directory..."] * 10 + ["Finished scan."]
    raw = "\n".join(lines)
    compacted = optimizer.collapse_identical_lines(raw, max_consecutive=3)
    assert "identical lines collapsed" in compacted
    assert len(compacted.splitlines()) < len(lines)


def test_compact_whitespace():
    optimizer = DeterministicTokenOptimizer()
    raw = "Line 1   \n\n\n\n\nLine 2   \n\n\n\nLine 3"
    cleaned = optimizer.compact_whitespace(raw)
    assert "   \n" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Line 1\n\nLine 2\n\nLine 3" == cleaned


def test_optimize_messages_and_token_savings():
    optimizer = DeterministicTokenOptimizer()
    messages = [
        ChatMessage(
            role="user",
            content="\x1b[31mFAIL\x1b[0m test_auth\n\n\n\n" + "Duplicate error\n" * 8,
        )
    ]
    optimized, saved = optimizer.optimize_messages(messages, bypass=False)
    assert saved > 0
    assert "\x1b" not in optimized[0].content
    assert "\n\n\n" not in optimized[0].content


def test_token_saver_bypass_flag():
    assert is_token_saver_bypassed("off") is True
    assert is_token_saver_bypassed("OFF") is True
    assert is_token_saver_bypassed("false") is True
    assert is_token_saver_bypassed("0") is True
    assert is_token_saver_bypassed("disabled") is True
    assert is_token_saver_bypassed("on") is False
    assert is_token_saver_bypassed(None) is False

    optimizer = DeterministicTokenOptimizer()
    messages = [ChatMessage(role="user", content="\x1b[31mUnchanged\x1b[0m")]
    optimized, saved = optimizer.optimize_messages(messages, bypass=True)
    assert saved == 0
    assert optimized[0].content == "\x1b[31mUnchanged\x1b[0m"


def test_no_semantic_corruption_of_code_or_json():
    """Verify optimizer does NOT employ caveman-speak or corrupt valid code syntax."""
    optimizer = DeterministicTokenOptimizer()
    code = """```python
def calculate_metrics(values: list[float]) -> dict:
    # Ensure mean and variance are strictly valid
    if not values:
        return {"mean": 0.0, "variance": 0.0}
    mean = sum(values) / len(values)
    return {"mean": mean, "variance": sum((x - mean) ** 2 for x in values)}
```"""
    optimized, saved = optimizer.optimize_text(code)
    # The code semantics, punctuation, and keywords must remain intact
    assert "def calculate_metrics" in optimized
    assert '{"mean": 0.0, "variance": 0.0}' in optimized
    assert "calculate_metrics" in optimized
