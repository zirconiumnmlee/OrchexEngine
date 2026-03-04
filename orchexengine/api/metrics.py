"""Metrics API endpoints for telemetry data"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database.session import get_db
from ..database.metrics import MetricsStore

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def get_metrics_summary(
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=720, description="Time window in hours")
):
    """
    Get aggregated statistics for the specified time period.

    Returns usage ratio, total requests, token counts, costs, and latency.
    """
    return MetricsStore.get_summary(db, hours=hours)


@router.get("/timeseries")
def get_metrics_timeseries(
    db: Session = Depends(get_db),
    bucket_minutes: int = Query(default=60, ge=5, le=1440, description="Time bucket size in minutes"),
    hours: int = Query(default=24, ge=1, le=720, description="Time window in hours")
):
    """
    Get time-bucketed request counts.

    Returns request counts per time bucket, split by provider (local/cloud).
    """
    return MetricsStore.get_timeseries(db, bucket_minutes=bucket_minutes, hours=hours)


@router.get("/models")
def get_model_breakdown(
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=720, description="Time window in hours")
):
    """
    Get per-model breakdown of usage.

    Returns statistics for each model including count, latency, and token usage.
    """
    return MetricsStore.get_model_breakdown(db, hours=hours)


@router.get("/logs")
def get_request_logs(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    provider: Optional[str] = Query(default=None, description="Filter by provider (local/cloud)")
):
    """
    Get paginated raw request logs.

    Returns detailed information about individual requests.
    """
    logs = MetricsStore.get_logs(db, limit=limit, offset=offset, provider=provider)
    total = MetricsStore.get_total_count(db, provider=provider)

    return {
        "logs": logs,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + limit < total
        }
    }
