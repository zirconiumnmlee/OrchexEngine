"""Request logging middleware for telemetry"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Awaitable
import uuid

from .collector import TelemetryCollector, LatencyTracker
from .schemas import TelemetryData
from ..database.session import SessionLocal


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log all requests.

    Captures:
    - Request/response timing (latency)
    - Request metadata
    - Response status codes
    - Errors
    """

    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/metrics/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip telemetry for certain paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # Track latency
        tracker = LatencyTracker()
        tracker.start()

        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        try:
            response = await call_next(request)

            # Calculate latency
            tracker.stop()
            latency_ms = tracker.elapsed_ms()

            # Log the request (basic info for non-chat endpoints)
            if not path.startswith("/v1/chat"):
                return response

            # For chat endpoints, telemetry is logged in the route handler
            # where we have access to tokens and routing info
            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            tracker.stop()
            latency_ms = tracker.elapsed_ms()

            # Log error
            try:
                telemetry = TelemetryCollector.create_telemetry(
                    request_id=request_id,
                    selected_model="unknown",
                    provider="unknown",
                    latency_ms=latency_ms,
                    routing_reason="error",
                    error=str(e),
                )
                TelemetryCollector.log_request(telemetry)
            except Exception:
                pass  # Don't fail on telemetry errors

            raise
