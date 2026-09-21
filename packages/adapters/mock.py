import json
import httpx
from typing import AsyncIterator, Any, Optional
from apps.gateway.core.errors import UpstreamProviderError, RateLimitExceededError
from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatChoice,
    ChatResponseMessage,
    ChatUsage,
    ChatChunkChoice,
    ChatChunkDelta,
)
from packages.adapters.base import BaseProviderAdapter


class MockAdapter(BaseProviderAdapter):
    """Deterministic local mock provider adapter (Rp0 zero external cost)."""

    def __init__(
        self,
        provider_name: str = "mock-a",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        base = (base_url or "http://localhost:8001").rstrip("/")
        super().__init__(
            provider_name=provider_name,
            base_url=base,
            api_key=api_key or "mock-key",
            timeout_seconds=timeout_seconds,
        )
        self._external_client = http_client

    def validate_config(self) -> bool:
        return True

    def map_request(
        self, request: ChatCompletionRequest, target_model: str
    ) -> dict[str, Any]:
        return {
            "model": target_model,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }

    def _get_target_endpoint(self) -> str:
        # If base_url already contains target or ends with /mock-a, keep it
        if "/mock-" in self.base_url or self.base_url.endswith(self.provider_name):
            return f"{self.base_url}/v1/chat/completions"
        return f"{self.base_url}/{self.provider_name}/v1/chat/completions"

    async def send_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> ChatCompletionResponse:
        endpoint = self._get_target_endpoint()
        payload = self.map_request(request, target_model)
        headers = {
            "Content-Type": "application/json",
            "X-CRouter-Target-Provider": self.provider_name,
        }

        async def _do_req(client: httpx.AsyncClient):
            res = await client.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if res.status_code != 200:
                if res.status_code == 429:
                    raise RateLimitExceededError(
                        f"Mock provider {self.provider_name} returned 429 rate limit"
                    )
                raise UpstreamProviderError(
                    f"Mock provider returned status {res.status_code}: {res.text}",
                    provider=self.provider_name,
                )
            data = res.json()
            return ChatCompletionResponse.model_validate(data)

        if self._external_client:
            return await _do_req(self._external_client)

        async with httpx.AsyncClient() as client:
            return await _do_req(client)

    async def stream_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> AsyncIterator[ChatCompletionChunk]:
        endpoint = self._get_target_endpoint()
        payload = self.map_request(request, target_model)
        headers = {
            "Content-Type": "application/json",
            "X-CRouter-Target-Provider": self.provider_name,
        }

        client_to_use = self._external_client or httpx.AsyncClient()
        should_close = self._external_client is None

        try:
            async with client_to_use.stream(
                "POST",
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    text = body.decode("utf-8", errors="replace")
                    if response.status_code == 429:
                        raise RateLimitExceededError(
                            f"Mock provider {self.provider_name} returned 429: {text}"
                        )
                    raise UpstreamProviderError(
                        f"Mock provider returned status {response.status_code}: {text}",
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
                            err_msg = chunk_dict["error"].get("message", "Upstream stream error")
                            raise UpstreamProviderError(err_msg, provider=self.provider_name)
                        yield ChatCompletionChunk.model_validate(chunk_dict)
                    except json.JSONDecodeError:
                        continue
        finally:
            if should_close:
                await client_to_use.aclose()
