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


class OpenRouterAdapter(BaseProviderAdapter):
    """OpenRouter Provider Adapter (OpenAI-compatible dialect)."""

    def __init__(
        self,
        provider_name: str = "openrouter",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        base = (base_url or "https://openrouter.ai/api/v1").rstrip("/")
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
            "HTTP-Referer": "https://github.com/arsyadal/crouter",
            "X-Title": "CRouter",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def send_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> ChatCompletionResponse:
        if not self.validate_config():
            raise UpstreamProviderError(
                "OpenRouter API key is not configured.", provider=self.provider_name
            )

        endpoint = f"{self.base_url}/chat/completions"
        payload = self.map_request(request, target_model)
        headers = self._get_headers()

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
                        f"OpenRouter rate limit exceeded: {res.text}"
                    )
                raise UpstreamProviderError(
                    f"OpenRouter API error {res.status_code}: {res.text}",
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
        if not self.validate_config():
            raise UpstreamProviderError(
                "OpenRouter API key is not configured.", provider=self.provider_name
            )

        endpoint = f"{self.base_url}/chat/completions"
        payload = self.map_request(request, target_model)
        headers = self._get_headers()

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
                            f"OpenRouter rate limit exceeded: {text}"
                        )
                    raise UpstreamProviderError(
                        f"OpenRouter stream error {response.status_code}: {text}",
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
                        if isinstance(chunk_dict, dict) and "error" in chunk_dict:
                            err_msg = chunk_dict["error"].get(
                                "message", "OpenRouter upstream stream error"
                            )
                            raise UpstreamProviderError(
                                err_msg, provider=self.provider_name
                            )
                        yield ChatCompletionChunk.model_validate(chunk_dict)
                    except json.JSONDecodeError:
                        continue
        finally:
            if should_close:
                await client_to_use.aclose()
