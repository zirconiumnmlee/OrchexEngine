"""Metrics query functions for telemetry data"""

from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .models import RequestLog


class MetricsStore:
    """Query interface for telemetry metrics"""

    @staticmethod
    def get_summary(db: Session, hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated stats for the specified time period.

        Args:
            db: Database session
            hours: Time window in hours (default: 24)

        Returns:
            dict: Aggregated statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Basic counts
        total_requests = db.query(RequestLog).filter(
            RequestLog.timestamp >= cutoff
        ).count()

        # Provider breakdown
        provider_stats = db.query(
            RequestLog.provider,
            func.count(RequestLog.id).label('count')
        ).filter(
            RequestLog.timestamp >= cutoff
        ).group_by(RequestLog.provider).all()

        provider_breakdown = {row.provider: row.count for row in provider_stats}

        # Calculate usage ratio
        local_count = provider_breakdown.get('local', 0)
        cloud_count = provider_breakdown.get('cloud', 0)
        usage_ratio = local_count / total_requests if total_requests > 0 else 0

        # Token stats
        token_stats = db.query(
            func.sum(RequestLog.input_tokens).label('input'),
            func.sum(RequestLog.output_tokens).label('output'),
        ).filter(
            RequestLog.timestamp >= cutoff
        ).first()

        # Cost stats (only for cloud requests)
        cost_stats = db.query(
            func.sum(RequestLog.estimated_cost).label('total')
        ).filter(
            RequestLog.timestamp >= cutoff,
            RequestLog.provider == 'cloud'
        ).first()

        # Error count
        error_count = db.query(RequestLog).filter(
            RequestLog.timestamp >= cutoff,
            RequestLog.error.isnot(None)
        ).count()

        # Average latency
        latency_stats = db.query(
            func.avg(RequestLog.latency_ms).label('avg')
        ).filter(
            RequestLog.timestamp >= cutoff
        ).first()

        return {
            "total_requests": total_requests,
            "local_requests": local_count,
            "cloud_requests": cloud_count,
            "usage_ratio": round(usage_ratio, 3),  # Proportion using local
            "total_input_tokens": token_stats.input or 0,
            "total_output_tokens": token_stats.output or 0,
            "estimated_cost": round(cost_stats.total or 0, 4),
            "error_count": error_count,
            "avg_latency_ms": round(latency_stats.avg or 0, 2),
            "period_hours": hours,
        }

    @staticmethod
    def get_timeseries(db: Session, bucket_minutes: int = 60, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get time-bucketed request counts.

        Args:
            db: Database session
            bucket_minutes: Time bucket size in minutes
            hours: Time window in hours

        Returns:
            list: Time-series data with request counts per bucket
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # SQLite doesn't have DATE_TRUNC, so we fetch raw data and bucket in Python
        logs = db.query(
            RequestLog.timestamp,
            RequestLog.provider
        ).filter(
            RequestLog.timestamp >= cutoff
        ).order_by(RequestLog.timestamp).all()

        # Bucket the data
        buckets: Dict[str, Dict[str, int]] = {}

        for log in logs:
            # Round timestamp to bucket
            bucket_time = log.timestamp.replace(
                minute=(log.timestamp.minute // bucket_minutes) * bucket_minutes,
                second=0,
                microsecond=0
            )
            bucket_key = bucket_time.isoformat()

            if bucket_key not in buckets:
                buckets[bucket_key] = {"total": 0, "local": 0, "cloud": 0}

            buckets[bucket_key]["total"] += 1
            buckets[bucket_key][log.provider] += 1

        # Convert to list format
        result = [
            {"timestamp": ts, **counts}
            for ts, counts in sorted(buckets.items())
        ]

        return result

    @staticmethod
    def get_model_breakdown(db: Session, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get per-model breakdown of usage.

        Args:
            db: Database session
            hours: Time window in hours

        Returns:
            list: Per-model statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        stats = db.query(
            RequestLog.selected_model,
            RequestLog.provider,
            func.count(RequestLog.id).label('count'),
            func.avg(RequestLog.latency_ms).label('avg_latency'),
            func.sum(RequestLog.input_tokens).label('input_tokens'),
            func.sum(RequestLog.output_tokens).label('output_tokens'),
        ).filter(
            RequestLog.timestamp >= cutoff
        ).group_by(
            RequestLog.selected_model,
            RequestLog.provider
        ).order_by(
            desc('count')
        ).all()

        return [
            {
                "model": row.selected_model,
                "provider": row.provider,
                "count": row.count,
                "avg_latency_ms": round(row.avg_latency, 2) if row.avg_latency else 0,
                "total_input_tokens": row.input_tokens or 0,
                "total_output_tokens": row.output_tokens or 0,
            }
            for row in stats
        ]

    @staticmethod
    def get_logs(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get paginated raw request logs.

        Args:
            db: Database session
            limit: Max records to return
            offset: Pagination offset
            provider: Optional filter by provider

        Returns:
            list: Request log entries
        """
        query = db.query(RequestLog).order_by(desc(RequestLog.timestamp))

        if provider:
            query = query.filter(RequestLog.provider == provider)

        logs = query.offset(offset).limit(limit).all()

        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "request_id": log.request_id,
                "selected_model": log.selected_model,
                "provider": log.provider,
                "latency_ms": log.latency_ms,
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "estimated_cost": round(log.estimated_cost, 6) if log.estimated_cost else None,
                "error": log.error,
                "routing_reason": log.routing_reason,
            }
            for log in logs
        ]

    @staticmethod
    def get_total_count(db: Session, provider: Optional[str] = None) -> int:
        """
        Get total count of logs for pagination.

        Args:
            db: Database session
            provider: Optional filter by provider

        Returns:
            int: Total count
        """
        query = db.query(RequestLog)
        if provider:
            query = query.filter(RequestLog.provider == provider)
        return query.count()
