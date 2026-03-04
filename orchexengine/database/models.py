"""SQLAlchemy ORM models for telemetry data"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Index, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class RequestLog(Base):
    """
    ORM model for storing request telemetry.

    Tracks all LLM requests including routing decisions, latency, tokens, and costs.
    """
    __tablename__ = "request_logs"

    # Primary key - UUID for collision-free IDs
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Timestamp - indexed for time-series queries
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Request identifier
    request_id = Column(String(36), nullable=False)

    # Model selection info
    selected_model = Column(String(128), nullable=False)
    provider = Column(String(32), nullable=False, index=True)  # "local" or "cloud"

    # Performance metrics
    latency_ms = Column(Integer, nullable=False)

    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)

    # Cost tracking (nullable for local models)
    estimated_cost = Column(Float, nullable=True)

    # Error tracking
    error = Column(String(512), nullable=True)

    # Routing decision info
    routing_reason = Column(String(512), nullable=False)

    # Extensibility - store arbitrary metadata
    metadata_ = Column(JSON, nullable=True)

    # Indexes for common query patterns
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
        Index('idx_provider', 'provider'),
        Index('idx_selected_model', 'selected_model'),
        Index('idx_timestamp_provider', 'timestamp', 'provider'),
    )

    def __repr__(self) -> str:
        return (
            f"<RequestLog(id={self.id}, provider={self.provider}, "
            f"model={self.selected_model}, latency={self.latency_ms}ms)>"
        )
