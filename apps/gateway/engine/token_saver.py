import re
from typing import List, Tuple, Dict, Any, Optional
from apps.gateway.schemas.chat import ChatMessage

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\([a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")

LOCKFILE_OR_MINIFIED_RE = re.compile(
    r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|poetry\.lock|composer\.lock|\.min\.js|\.min\.css|\.map)$",
    re.IGNORECASE,
)

LINTER_DIAGNOSTIC_RE = re.compile(
    r"^(?:(?:\S+:\d+(?::\d+)?:\s*(?:warning|error|info|note|hint):)|(?:ts\(\d+\):)|(?:\s*at\s+\S+\s+\(.*:\d+:\d+\)))",
    re.IGNORECASE,
)


class DeterministicTokenOptimizer:
    """Engineering-grade RTK-style deterministic token optimizer.

    Safely compresses tool results, terminal logs, and bloated diffs
    without damaging code semantics and without dangerous prompt-injection hacks.
    """

    def __init__(self, is_enabled: bool = True):
        self.is_enabled = is_enabled

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count deterministically (~4 chars per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def strip_ansi(self, text: str) -> str:
        """Strip ANSI terminal color and control escape sequences."""
        return ANSI_ESCAPE_RE.sub("", text)

    def compact_diffs(self, text: str) -> str:
        """Compact bloated git diff outputs, such as lockfiles or generated assets."""
        lines = text.splitlines()
        result_lines = []
        in_lockfile_diff = False
        skipped_count = 0

        for line in lines:
            if line.startswith("diff --git ") or line.startswith("--- ") or line.startswith("+++ "):
                is_lockfile = bool(LOCKFILE_OR_MINIFIED_RE.search(line))
                if is_lockfile:
                    in_lockfile_diff = True
                    result_lines.append(line)
                    continue
                elif in_lockfile_diff and (line.startswith("diff --git ") or line.startswith("--- ")):
                    if skipped_count > 0:
                        result_lines.append(f"[... {skipped_count} lines of generated/lockfile diff compacted ...]")
                        skipped_count = 0
                    in_lockfile_diff = False

            if in_lockfile_diff:
                if line.startswith("+") or line.startswith("-") or line.startswith(" "):
                    skipped_count += 1
                    if skipped_count > 5:
                        continue
                result_lines.append(line)
            else:
                result_lines.append(line)

        if skipped_count > 0:
            result_lines.append(f"[... {skipped_count} lines of generated/lockfile diff compacted ...]")

        return "\n".join(result_lines)

    def deduplicate_linter_lines(self, text: str, max_repeats: int = 4) -> str:
        """Deduplicate repetitive diagnostic lines from linters or compilers."""
        lines = text.splitlines()
        if len(lines) < 8:
            return text

        result_lines = []
        consecutive_diagnostic_count = 0
        hidden_diagnostics = 0

        for line in lines:
            stripped = line.strip()
            is_diag = bool(LINTER_DIAGNOSTIC_RE.match(stripped))

            if is_diag:
                consecutive_diagnostic_count += 1
                if consecutive_diagnostic_count > max_repeats:
                    hidden_diagnostics += 1
                    continue
                result_lines.append(line)
            else:
                if hidden_diagnostics > 0:
                    result_lines.append(
                        f"[... {hidden_diagnostics} repetitive diagnostic lines truncated ...]"
                    )
                    hidden_diagnostics = 0
                consecutive_diagnostic_count = 0
                result_lines.append(line)

        if hidden_diagnostics > 0:
            result_lines.append(
                f"[... {hidden_diagnostics} repetitive diagnostic lines truncated ...]"
            )

        return "\n".join(result_lines)

    def collapse_identical_lines(self, text: str, max_consecutive: int = 3) -> str:
        """Collapse runs of identical lines into a single summary line."""
        lines = text.splitlines()
        if len(lines) < 6:
            return text

        result_lines = []
        prev_line: Optional[str] = None
        repeat_count = 0

        for line in lines:
            if line == prev_line and len(line.strip()) > 0:
                repeat_count += 1
                if repeat_count >= max_consecutive:
                    continue
                result_lines.append(line)
            else:
                if repeat_count >= max_consecutive:
                    omitted = repeat_count - max_consecutive + 1
                    result_lines.append(f"[... {omitted} identical lines collapsed ...]")
                prev_line = line
                repeat_count = 0
                result_lines.append(line)

        if repeat_count >= max_consecutive:
            omitted = repeat_count - max_consecutive + 1
            result_lines.append(f"[... {omitted} identical lines collapsed ...]")

        return "\n".join(result_lines)

    def compact_whitespace(self, text: str) -> str:
        """Strip trailing line spaces and collapse 3+ consecutive newlines into 2."""
        # Strip trailing whitespace on each line
        lines = [line.rstrip() for line in text.splitlines()]
        cleaned = "\n".join(lines)
        # Collapse 3 or more blank lines to 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    def compact_repetitive_paths(self, text: str) -> str:
        """Compact repetitive long workspace paths while preserving filename and relative path."""
        # If long absolute workspace prefixes repeat frequently, normalize them
        pattern = re.compile(r"([A-Za-z]:[\\/][^:\s\n\"\'`]+[\\/]crouter[\\/])", re.IGNORECASE)
        matches = pattern.findall(text)
        if len(matches) >= 3:
            common_prefix = matches[0]
            text = text.replace(common_prefix, "./")
        return text

    def optimize_text(self, text: str) -> Tuple[str, int]:
        """Optimize a single text string and return (optimized_text, tokens_saved)."""
        if not self.is_enabled or not text or len(text) < 10:
            return text, 0

        initial_tokens = self.estimate_tokens(text)

        # Apply deterministic transforms in pipeline
        transformed = self.strip_ansi(text)
        transformed = self.compact_diffs(transformed)
        transformed = self.deduplicate_linter_lines(transformed)
        transformed = self.collapse_identical_lines(transformed)
        transformed = self.compact_repetitive_paths(transformed)
        transformed = self.compact_whitespace(transformed)

        final_tokens = self.estimate_tokens(transformed)
        tokens_saved = max(0, initial_tokens - final_tokens)
        return transformed, tokens_saved

    def optimize_messages(
        self, messages: List[ChatMessage], bypass: bool = False
    ) -> Tuple[List[ChatMessage], int]:
        """Optimize messages in place or copy, returning (optimized_messages, tokens_saved)."""
        if bypass or not self.is_enabled:
            return messages, 0

        total_saved = 0
        optimized = []

        for msg in messages:
            # We focus on tool outputs, system instructions, and user messages
            # Assistant messages are preserved as-is to preserve exact context
            if msg.role in ("user", "tool", "system"):
                opt_content, saved = self.optimize_text(msg.content)
                total_saved += saved
                optimized.append(ChatMessage(role=msg.role, content=opt_content))
            else:
                optimized.append(msg)

        return optimized, total_saved


# Singleton optimizer instance
token_optimizer = DeterministicTokenOptimizer(is_enabled=True)


def is_token_saver_bypassed(header_val: Optional[str]) -> bool:
    """Check if X-CRouter-Token-Saver header requests a bypass."""
    if not header_val:
        return False
    val = header_val.strip().lower()
    return val in ("off", "false", "0", "disable", "disabled", "none")
