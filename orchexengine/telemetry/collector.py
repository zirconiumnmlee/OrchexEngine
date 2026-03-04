"""Metrics collection logic"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import time

from .schemas import TelemetryData
from ..database.models import RequestLog
from ..database.session import SessionLocal


# Cost per 1K tokens (approximate OpenAI pricing)
COST_PER_1K_INPUT = 0.0015  # $0.0015 per 1K input tokens (GPT-3.5-turbo)
COST_PER_1K_OUTPUT = 0.0020  # $0.002 per 1K output tokens


class TelemetryCollector:
    """
    Collects and stores telemetry data for each request.
    """

    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int, provider: str) -> Optional[float]:
        """
        Calculate estimated cost for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: "local" or "cloud"

        Returns:
            Estimated cost in USD, or None for local models
        """
        if provider == "local":
            return None

        # Calculate cost based on token counts
        input_cost = (input_tokens / 1000) * COST_PER_1K_INPUT
        output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT
        return round(input_cost + output_cost, 6)

    @staticmethod
    def log_request(
        telemetry: TelemetryData,
        db: Optional[Session] = None
    ) -> RequestLog:
        """
        Log a request to the database.

        Args:
            telemetry: Telemetry data
            db: Optional database session (creates one if not provided)

        Returns:
            Created RequestLog entry
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            log_entry = RequestLog(
                request_id=telemetry.request_id,
                selected_model=telemetry.selected_model,
                provider=telemetry.provider,
                latency_ms=telemetry.latency_ms,
                input_tokens=telemetry.input_tokens,
                output_tokens=telemetry.output_tokens,
                estimated_cost=telemetry.estimated_cost,
                error=telemetry.error,
                routing_reason=telemetry.routing_reason,
                metadata_=telemetry.metadata,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            return log_entry

        except Exception as e:
            if db:
                db.rollback()
            # Re-raise if we own the session, otherwise log silently
            if close_db:
                raise
            return None
        finally:
            if close_db:
                db.close()

    @staticmethod
    def create_telemetry(
        request_id: str,
        selected_model: str,
        provider: str,
        latency_ms: int,
        routing_reason: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TelemetryData:
        """
        Create telemetry data with automatic cost calculation.

        Args:
            request_id: Unique request identifier
            selected_model: Model used
            provider: "local" or "cloud"
            latency_ms: Response latency
            routing_reason: Why this model was selected
            input_tokens: Prompt tokens
            output_tokens: Completion tokens
            error: Optional error message
            metadata: Optional additional metadata

        Returns:
            TelemetryData instance
        """
        estimated_cost = TelemetryCollector.calculate_cost(
            input_tokens, output_tokens, provider
        )

        return TelemetryData(
            request_id=request_id,
            selected_model=selected_model,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            error=error,
            routing_reason=routing_reason,
            metadata=metadata,
        )


class LatencyTracker:
    """Utility for tracking request latency"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start timing"""
        self.start_time = time.perf_counter()

    def stop(self) -> None:
        """Stop timing"""
        self.end_time = time.perf_counter()

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds"""
        if self.start_time is None:
            return 0
        end = self.end_time or time.perf_counter()
        return int((end - self.start_time) * 1000)
