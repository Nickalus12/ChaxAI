"""Analytics module for usage tracking and insights."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import logging

from .config import ANALYTICS_DB, ENABLE_ANALYTICS

logger = logging.getLogger("chaxai.analytics")

Base = declarative_base()


class APIUsage(Base):
    """API usage tracking table."""
    
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    response_time = Column(Float)
    tokens_used = Column(Integer)
    model = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class QueryLog(Base):
    """Query logging table."""
    
    __tablename__ = "query_log"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    query = Column(String)
    response_preview = Column(String)
    sources_count = Column(Integer)
    confidence = Column(Float)
    model = Column(String)
    processing_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# Initialize database
if ENABLE_ANALYTICS:
    engine = create_engine(ANALYTICS_DB)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def track_api_usage(
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    tenant_id: str,
    user_id: Optional[str] = None,
    tokens_used: Optional[int] = None,
    model: Optional[str] = None
):
    """Track API usage asynchronously."""
    if not ENABLE_ANALYTICS:
        return
    
    def _track():
        try:
            session = SessionLocal()
            usage = APIUsage(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                tokens_used=tokens_used,
                model=model
            )
            session.add(usage)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Failed to track API usage: {e}")
    
    # Run in background
    asyncio.create_task(asyncio.to_thread(_track))


async def track_query(
    query: str,
    response_preview: str,
    sources_count: int,
    confidence: float,
    model: str,
    processing_time: float,
    tenant_id: str,
    user_id: Optional[str] = None
):
    """Track query details asynchronously."""
    if not ENABLE_ANALYTICS:
        return
    
    def _track():
        try:
            session = SessionLocal()
            log = QueryLog(
                tenant_id=tenant_id,
                user_id=user_id,
                query=query[:500],  # Truncate long queries
                response_preview=response_preview[:200],
                sources_count=sources_count,
                confidence=confidence,
                model=model,
                processing_time=processing_time
            )
            session.add(log)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Failed to track query: {e}")
    
    # Run in background
    asyncio.create_task(asyncio.to_thread(_track))


async def get_analytics_summary(
    tenant_id: str,
    period_days: int = 30
) -> Dict[str, Any]:
    """Get analytics summary for a tenant."""
    if not ENABLE_ANALYTICS:
        return {"error": "Analytics not enabled"}
    
    session = SessionLocal()
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # API usage stats
        api_stats = session.query(
            func.count(APIUsage.id).label("total_requests"),
            func.avg(APIUsage.response_time).label("avg_response_time"),
            func.sum(APIUsage.tokens_used).label("total_tokens")
        ).filter(
            APIUsage.tenant_id == tenant_id,
            APIUsage.timestamp >= start_date
        ).first()
        
        # Query stats
        query_stats = session.query(
            func.count(QueryLog.id).label("total_queries"),
            func.avg(QueryLog.confidence).label("avg_confidence"),
            func.avg(QueryLog.processing_time).label("avg_processing_time")
        ).filter(
            QueryLog.tenant_id == tenant_id,
            QueryLog.timestamp >= start_date
        ).first()
        
        # Top models
        top_models = session.query(
            QueryLog.model,
            func.count(QueryLog.id).label("count")
        ).filter(
            QueryLog.tenant_id == tenant_id,
            QueryLog.timestamp >= start_date
        ).group_by(QueryLog.model).order_by(func.count(QueryLog.id).desc()).limit(5).all()
        
        # Daily trends
        daily_trends = session.query(
            func.date(QueryLog.timestamp).label("date"),
            func.count(QueryLog.id).label("queries")
        ).filter(
            QueryLog.tenant_id == tenant_id,
            QueryLog.timestamp >= start_date
        ).group_by(func.date(QueryLog.timestamp)).all()
        
        # Error rate
        total_requests = api_stats.total_requests or 0
        error_requests = session.query(func.count(APIUsage.id)).filter(
            APIUsage.tenant_id == tenant_id,
            APIUsage.timestamp >= start_date,
            APIUsage.status_code >= 400
        ).scalar() or 0
        
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "tenant_id": tenant_id,
            "period": f"Last {period_days} days",
            "total_queries": query_stats.total_queries or 0,
            "total_requests": api_stats.total_requests or 0,
            "total_tokens": api_stats.total_tokens or 0,
            "average_response_time": round(api_stats.avg_response_time or 0, 3),
            "average_confidence": round(query_stats.avg_confidence or 0, 1),
            "average_processing_time": round(query_stats.avg_processing_time or 0, 3),
            "error_rate": round(error_rate, 2),
            "top_models": [
                {"model": m.model, "count": m.count}
                for m in top_models
            ],
            "query_trends": [
                {"date": str(t.date), "count": t.queries}
                for t in daily_trends
            ]
        }
        
    finally:
        session.close()


def init_analytics():
    """Initialize analytics module."""
    if ENABLE_ANALYTICS:
        logger.info("Analytics module initialized")
    else:
        logger.info("Analytics module disabled")
