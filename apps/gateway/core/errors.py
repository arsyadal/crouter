from typing import Any, Optional


class CRouterException(Exception):
    """Base exception for all CRouter errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        error_type: str = "api_error",
        param: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.error_type = error_type
        self.param = param
        self.headers = headers or {}

    def to_dict(self, request_id: Optional[str] = None) -> dict[str, Any]:
        return {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "code": self.error_code,
                "param": self.param,
                "request_id": request_id,
            }
        }


class InvalidRequestError(CRouterException):
    """HTTP 400: Missing required fields, invalid JSON, unsupported parameters."""

    def __init__(self, message: str, param: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="invalid_request_error",
            error_type="invalid_request_error",
            param=param,
        )


class InvalidAPIKeyError(CRouterException):
    """HTTP 401: Missing Bearer token or key mismatch / revoked."""

    def __init__(self, message: str = "Invalid or missing gateway API key."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="invalid_api_key",
            error_type="authentication_error",
        )


class ForbiddenRouteError(CRouterException):
    """HTTP 403: Gateway key lacks permission to call requested model alias."""

    def __init__(self, message: str = "Gateway key lacks permission for this route."):
        super().__init__(
            message=message,
            status_code=403,
            error_code="forbidden_route",
            error_type="permission_error",
        )


class ModelNotFoundError(CRouterException):
    """HTTP 404: Requested model alias or provider route does not exist."""

    def __init__(self, message: str = "Requested model alias not found."):
        super().__init__(
            message=message,
            status_code=404,
            error_code="model_not_found",
            error_type="invalid_request_error",
        )


class RateLimitExceededError(CRouterException):
    """HTTP 429: Rate limit or concurrent connection lease exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded for API key.",
        retry_after: int = 10,
    ):
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limit_exceeded",
            error_type="rate_limit_error",
            headers={"Retry-After": str(retry_after)},
        )
        self.retry_after = retry_after


class UpstreamProviderError(CRouterException):
    """HTTP 502: Upstream provider returned an unparseable response or fatal 5xx."""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(
            message=f"Upstream provider error ({provider or 'unknown'}): {message}",
            status_code=502,
            error_code="upstream_provider_error",
            error_type="api_error",
        )
        self.provider = provider


class NoHealthyRouteError(CRouterException):
    """HTTP 503: All configured fallback routes are down or tripped by circuit breakers."""

    def __init__(self, message: str = "No healthy upstream route available."):
        super().__init__(
            message=message,
            status_code=503,
            error_code="no_healthy_route",
            error_type="service_unavailable_error",
        )


class GatewayTimeoutError(CRouterException):
    """HTTP 504: Total request deadline exceeded across routing attempts."""

    def __init__(self, message: str = "Request timed out waiting for upstream provider."):
        super().__init__(
            message=message,
            status_code=504,
            error_code="gateway_timeout",
            error_type="timeout_error",
        )
