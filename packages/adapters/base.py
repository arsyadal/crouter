import abc
from typing import AsyncIterator, Any, Optional
from apps.gateway.core.errors import (
    CRouterException,
    UpstreamProviderError,
    RateLimitExceededError,
    GatewayTimeoutError,
)
from apps.gateway.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
)


class BaseProviderAdapter(abc.ABC):
    """Standardized abstract base class for AI Provider Adapters."""

    def __init__(
        self,
        provider_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        self.provider_name = provider_name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @abc.abstractmethod
    def validate_config(self) -> bool:
        """Validate API credentials and endpoint configuration."""
        pass

    @abc.abstractmethod
    def map_request(
        self, request: ChatCompletionRequest, target_model: str
    ) -> dict[str, Any]:
        """Normalize gateway request payload into upstream provider format."""
        pass

    @abc.abstractmethod
    async def send_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> ChatCompletionResponse:
        """Execute non-streaming completion against upstream provider."""
        pass

    @abc.abstractmethod
    async def stream_completion(
        self, request: ChatCompletionRequest, target_model: str
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Execute streaming completion against upstream provider emitting SSE chunks."""
        pass

    def map_error(self, upstream_error: Exception) -> CRouterException:
        """Map provider-specific or network exceptions to standardized Gateway errors."""
        import httpx

        if isinstance(upstream_error, CRouterException):
            return upstream_error

        if isinstance(upstream_error, httpx.TimeoutException):
            return GatewayTimeoutError(
                f"Provider {self.provider_name} request timed out."
            )

        if isinstance(upstream_error, httpx.HTTPStatusError):
            status = upstream_error.response.status_code
            text = upstream_error.response.text[:200]
            if status == 429:
                return RateLimitExceededError(
                    f"Upstream provider {self.provider_name} rate limit exceeded: {text}"
                )
            return UpstreamProviderError(
                f"HTTP {status} - {text}", provider=self.provider_name
            )

        return UpstreamProviderError(str(upstream_error), provider=self.provider_name)
