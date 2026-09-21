import json
import time
import uuid
import httpx
from typing import AsyncIterator, Any, Optional
from apps.gateway.core.errors import (
    UpstreamProviderError,
    RateLimitExceededError,
    InvalidRequestError,
)
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


class GeminiAdapter(BaseProviderAdapter):
    """Google Gemini REST API (v1beta) Adapter."""

    def __init__(
        self,
        provider_name: str = "gemini",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        base = (
            base_url or "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/")
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
        contents = []
        system_instruction = None

        for msg in request.messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            else:
                role = "model" if msg.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

        body: dict[str, Any] = {"contents": contents}
        if system_instruction:
            body["systemInstruction"] = system_instruction

        generation_config: dict[str, Any] = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens

        if generation_config:
            body["generationConfig"] = generation_config

        return body

    async def send_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> ChatCompletionResponse:
        if not self.validate_config():
            raise UpstreamProviderError(
                "Gemini API key is not configured.", provider=self.provider_name
            )

        endpoint = (
            f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"
        )
        payload = self.map_request(request, target_model)

        async def _do_req(client: httpx.AsyncClient):
            res = await client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            if res.status_code != 200:
                if res.status_code == 429:
                    raise RateLimitExceededError(
                        f"Gemini rate limit exceeded: {res.text}"
                    )
                raise UpstreamProviderError(
                    f"Gemini API error {res.status_code}: {res.text}",
                    provider=self.provider_name,
                )

            data = res.json()
            candidates = data.get("candidates", [])
            text = ""
            finish_reason = "stop"
            if candidates:
                cand = candidates[0]
                content = cand.get("content", {})
                parts = content.get("parts", [])
                if parts:
                    text = "".join(p.get("text", "") for p in parts)
                if cand.get("finishReason"):
                    finish_reason = cand.get("finishReason").lower()

            usage_meta = data.get("usageMetadata", {})
            prompt_tokens = usage_meta.get("promptTokenCount", 0)
            completion_tokens = usage_meta.get("candidatesTokenCount", 0)
            total_tokens = usage_meta.get("totalTokenCount", prompt_tokens + completion_tokens)

            return ChatCompletionResponse(
                id=f"chatcmpl_cr_gemini_{uuid.uuid4().hex[:12]}",
                object="chat.completion",
                created=int(time.time()),
                model=target_model,
                choices=[
                    ChatChoice(
                        index=0,
                        message=ChatResponseMessage(role="assistant", content=text),
                        finish_reason=finish_reason,
                    )
                ],
                usage=ChatUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
            )

        if self._external_client:
            return await _do_req(self._external_client)

        async with httpx.AsyncClient() as client:
            return await _do_req(client)

    async def stream_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> AsyncIterator[ChatCompletionChunk]:
        if not self.validate_config():
            raise UpstreamProviderError(
                "Gemini API key is not configured.", provider=self.provider_name
            )

        endpoint = f"{self.base_url}/models/{target_model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self.map_request(request, target_model)

        client_to_use = self._external_client or httpx.AsyncClient()
        should_close = self._external_client is None

        completion_id = f"chatcmpl_cr_gemini_{uuid.uuid4().hex[:12]}"
        now = int(time.time())

        try:
            async with client_to_use.stream(
                "POST",
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    text = body.decode("utf-8", errors="replace")
                    if response.status_code == 429:
                        raise RateLimitExceededError(
                            f"Gemini rate limit exceeded: {text}"
                        )
                    raise UpstreamProviderError(
                        f"Gemini API stream error {response.status_code}: {text}",
                        provider=self.provider_name,
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    try:
                        chunk_dict = json.loads(data_str)
                        candidates = chunk_dict.get("candidates", [])
                        if not candidates:
                            continue
                        cand = candidates[0]
                        parts = cand.get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts) if parts else ""
                        finish_reason = (
                            cand.get("finishReason").lower()
                            if cand.get("finishReason")
                            else None
                        )

                        yield ChatCompletionChunk(
                            id=completion_id,
                            object="chat.completion.chunk",
                            created=now,
                            model=target_model,
                            choices=[
                                ChatChunkChoice(
                                    index=0,
                                    delta=ChatChunkDelta(
                                        role="assistant" if text else None, content=text
                                    ),
                                    finish_reason=finish_reason,
                                )
                            ],
                        )
                    except json.JSONDecodeError:
                        continue
        finally:
            if should_close:
                await client_to_use.aclose()
