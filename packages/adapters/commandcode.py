import json
import httpx
from typing import AsyncIterator, Any, Optional
from apps.gateway.core.errors import (
    UpstreamProviderError,
    RateLimitExceededError,
)
from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
)
from packages.adapters.base import BaseProviderAdapter


class CommandCodeAdapter(BaseProviderAdapter):
    """Command Code / 9Router Provider Adapter (OpenAI-compatible dialect)."""

    def __init__(
        self,
        provider_name: str = "commandcode",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 25.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        base = (base_url or "https://api.commandcode.ai/provider/v1").rstrip("/")
        super().__init__(
            provider_name=provider_name,
            base_url=base,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        self._external_client = http_client

    def validate_config(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def map_request(
        self, request: ChatCompletionRequest, target_model: str
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": target_model,
            "messages": [m.model_dump() for m in request.messages],
            "stream": request.stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        return payload

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CRouter/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def send_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> ChatCompletionResponse:
        url = f"{self.base_url}/chat/completions"
        payload = self.map_request(request, target_model)
        headers = self._get_headers()

        client_to_use = self._external_client or httpx.AsyncClient()
        should_close = self._external_client is None
        try:
            response = await client_to_use.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                text = response.text[:250]
                if response.status_code == 429:
                    raise RateLimitExceededError(
                        f"CommandCode rate limit exceeded: {text}"
                    )
                raise UpstreamProviderError(
                    f"CommandCode HTTP {response.status_code}: {text}",
                    provider=self.provider_name,
                )

            data = response.json()
            for choice in data.get("choices", []):
                msg = choice.get("message", {})
                if not msg.get("content"):
                    msg["content"] = msg.get("reasoning") or ""
            return ChatCompletionResponse.model_validate(data)
        finally:
            if should_close:
                await client_to_use.aclose()

    async def stream_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> AsyncIterator[ChatCompletionChunk]:
        url = f"{self.base_url}/chat/completions"
        payload = self.map_request(request, target_model)
        payload["stream"] = True
        headers = self._get_headers()

        client_to_use = self._external_client or httpx.AsyncClient()
        should_close = self._external_client is None
        try:
            async with client_to_use.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    text = body.decode("utf-8", errors="replace")
                    if response.status_code == 429:
                        raise RateLimitExceededError(
                            f"CommandCode rate limit exceeded: {text}"
                        )
                    raise UpstreamProviderError(
                        f"CommandCode stream error {response.status_code}: {text}",
                        provider=self.provider_name,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_dict = json.loads(data_str)
                        if "error" in chunk_dict:
                            err_msg = chunk_dict["error"].get("message", "Stream chunk error")
                            raise UpstreamProviderError(
                                f"CommandCode stream chunk error: {err_msg}",
                                provider=self.provider_name,
                            )
                        for c in chunk_dict.get("choices", []):
                            d = c.get("delta", {})
                            if not d.get("content") and d.get("reasoning"):
                                d["content"] = d["reasoning"]
                        yield ChatCompletionChunk.model_validate(chunk_dict)
                    except json.JSONDecodeError:
                        continue
        finally:
            if should_close:
                await client_to_use.aclose()
