from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Dict, Any

from app.db.deps import get_db
from app.models.tender import Tender, Keyword, TenderKeywordMatch
from app.models.winner import Winner, CompanyProfile
from app.models.log import ParserLog
from app.services.logging_service import LoggingService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get admin dashboard with system overview"""
    try:
        # Get current date ranges
        now = datetime.utcnow()
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_end = daily_start + timedelta(days=1)
        
        weekly_start = now - timedelta(days=now.weekday())
        weekly_start = weekly_start.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_end = weekly_start + timedelta(days=7)
        
        monthly_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            monthly_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            monthly_end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Tender statistics
        total_tenders = db.query(Tender).count()
        daily_tenders = db.query(Tender).filter(Tender.created_at >= daily_start).filter(Tender.created_at < daily_end).count()
        weekly_tenders = db.query(Tender).filter(Tender.created_at >= weekly_start).filter(Tender.created_at < weekly_end).count()
        monthly_tenders = db.query(Tender).filter(Tender.created_at >= monthly_start).filter(Tender.created_at < monthly_end).count()
        
        # Keyword statistics
        total_keywords = db.query(Keyword).count()
        active_keywords = db.query(Keyword).filter(Keyword.is_active == True).count()
        
        # Winner statistics
        total_winners = db.query(Winner).count()
        total_companies = db.query(CompanyProfile).count()
        
        # Recent activity
        recent_logs = (
            db.query(ParserLog)
            .filter(ParserLog.started_at >= daily_start)
            .order_by(ParserLog.started_at.desc())
            .limit(10)
            .all()
        )
        
        # Top sources
        top_sources = (
            db.query(Tender.source, func.count(Tender.id).label('count'))
            .group_by(Tender.source)
            .order_by(func.count(Tender.id).desc())
            .limit(5)
            .all()
        )
        
        # Top keywords
        top_keywords = (
            db.query(Keyword.phrase, func.count(TenderKeywordMatch.id).label('count'))
            .join(TenderKeywordMatch)
            .filter(Keyword.is_active == True)
            .group_by(Keyword.id)
            .order_by(func.count(TenderKeywordMatch.id).desc())
            .limit(10)
            .all()
        )
        
        return {
            "dashboard": {
                "tenders": {
                    "total": total_tenders,
                    "daily": daily_tenders,
                    "weekly": weekly_tenders,
                    "monthly": monthly_tenders
                },
                "keywords": {
                    "total": total_keywords,
                    "active": active_keywords,
                    "inactive": total_keywords - active_keywords
                },
                "winners": {
                    "total": total_winners,
                    "companies": total_companies
                },
                "system": {
                    "uptime": "24/7",  # This would be calculated from logs
                    "last_update": now.isoformat(),
                    "version": "2.0.0"
                }
            },
            "charts": {
                "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
                "top_keywords": [{"keyword": k[0], "count": k[1]} for k in top_keywords]
            },
            "recent_activity": [
                {
                    "id": log.id,
                    "task_name": log.task_name,
                    "source": log.source,
                    "status": log.status,
                    "message": log.message,
                    "started_at": log.started_at.isoformat(),
                    "duration_seconds": log.duration_seconds
                }
                for log in recent_logs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/system-health")
def get_system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get detailed system health information"""
    try:
        # Database health
        db_health = {
            "connected": True,
            "tender_count": db.query(Tender).count(),
            "keyword_count": db.query(Keyword).count(),
            "winner_count": db.query(Winner).count(),
            "log_count": db.query(ParserLog).count()
        }
        
        # Recent task performance
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        
        recent_tasks = (
            db.query(ParserLog)
            .filter(ParserLog.started_at >= day_ago)
            .all()
        )
        
        performance = {
            "total_tasks": len(recent_tasks),
            "successful_tasks": len([t for t in recent_tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in recent_tasks if t.status == "failed"]),
            "average_duration": sum([t.duration_seconds or 0 for t in recent_tasks]) / len(recent_tasks) if recent_tasks else 0
        }
        
        # Storage usage (simplified)
        storage = {
            "database_size": "Unknown",  # Would need actual DB size query
            "logs_size": len(recent_tasks),  # Simplified
            "tenders_processed": db.query(Tender).count()
        }
        
        # Overall health score
        success_rate = (performance["successful_tasks"] / performance["total_tasks"]) * 100 if performance["total_tasks"] > 0 else 100
        
        if success_rate >= 95:
            health_status = "excellent"
        elif success_rate >= 85:
            health_status = "good"
        elif success_rate >= 70:
            health_status = "degraded"
        else:
            health_status = "poor"
        
        return {
            "overall_status": health_status,
            "success_rate": round(success_rate, 2),
            "database": db_health,
            "performance": performance,
            "storage": storage,
            "recommendations": _get_health_recommendations(health_status, performance)
        }
        
    except Exception as e:
        return {
            "overall_status": "error",
            "error": str(e),
            "database": {"connected": False}
        }


@router.get("/statistics")
def get_detailed_statistics(
    days_back: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed statistics for analysis"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Tender trends
        tender_trends = (
            db.query(
                func.date(Tender.created_at).label('date'),
                func.count(Tender.id).label('count')
            )
            .filter(Tender.created_at >= cutoff_date)
            .group_by(func.date(Tender.created_at))
            .order_by(func.date(Tender.created_at))
            .all()
        )
        
        # Source distribution
        source_distribution = (
            db.query(Tender.source, func.count(Tender.id).label('count'))
            .filter(Tender.created_at >= cutoff_date)
            .group_by(Tender.source)
            .order_by(func.count(Tender.id).desc())
            .all()
        )
        
        # Keyword performance
        keyword_performance = (
            db.query(
                Keyword.phrase,
                func.count(TenderKeywordMatch.id).label('matches'),
                func.count(func.distinct(Tender.id)).label('unique_tenders')
            )
            .join(TenderKeywordMatch)
            .join(Tender)
            .filter(Keyword.is_active == True)
            .filter(Tender.created_at >= cutoff_date)
            .group_by(Keyword.id)
            .order_by(func.count(TenderKeywordMatch.id).desc())
            .limit(20)
            .all()
        )
        
        # Task execution stats
        task_stats = (
            db.query(
                ParserLog.task_name,
                ParserLog.status,
                func.count(ParserLog.id).label('count'),
                func.avg(ParserLog.duration_seconds).label('avg_duration')
            )
            .filter(ParserLog.started_at >= cutoff_date)
            .group_by(ParserLog.task_name, ParserLog.status)
            .all()
        )
        
        return {
            "period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "tender_trends": [
                {"date": str(t[0]), "count": t[1]} 
                for t in tender_trends
            ],
            "source_distribution": [
                {"source": s[0], "count": s[1]} 
                for s in source_distribution
            ],
            "keyword_performance": [
                {
                    "keyword": k[0],
                    "matches": k[1],
                    "unique_tenders": k[2],
                    "efficiency": round(k[2] / k[1] * 100, 2) if k[1] > 0 else 0
                }
                for k in keyword_performance
            ],
            "task_execution": [
                {
                    "task_name": t[0],
                    "status": t[1],
                    "count": t[2],
                    "avg_duration": round(t[3] or 0, 2)
                }
                for t in task_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/cleanup")
def cleanup_old_data(
    days_to_keep: int = 90,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Clean up old data to manage storage"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean old logs
        deleted_logs = (
            db.query(ParserLog)
            .filter(ParserLog.started_at < cutoff_date)
            .delete()
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up data older than {days_to_keep} days",
            "deleted_logs": deleted_logs,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/settings")
def get_admin_settings() -> Dict[str, Any]:
    """Get current admin settings"""
    from app.core.config import settings
    
    return {
        "system": {
            "scrape_interval_minutes": settings.SCRAPE_EVERY_MINUTES,
            "telegram_bot_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "telegram_alerts_enabled": bool(settings.TELEGRAM_ALERT_CHAT_ID),
            "google_sheets_enabled": settings.GOOGLE_SHEETS_AUTO_EXPORT,
            "telegram_monitor_enabled": settings.TELEGRAM_MONITOR_ENABLED
        },
        "limits": {
            "max_tenders_per_scrape": 100,
            "max_keywords_per_request": 100,
            "max_export_days": 365,
            "cleanup_days_default": 90
        },
        "features": {
            "keyword_management": True,
            "google_sheets_export": True,
            "excel_export": True,
            "telegram_monitoring": True,
            "winner_parsing": True,
            "company_enrichment": True,
            "task_scheduling": True
        }
    }


def _get_health_recommendations(status: str, performance: Dict[str, Any]) -> list[str]:
    """Get health recommendations based on system status"""
    recommendations = []
    
    if status in ["poor", "degraded"]:
        recommendations.append("Check system logs for recent failures")
        recommendations.append("Verify external API connections")
    
    if performance.get("failed_tasks", 0) > 0:
        recommendations.append("Review failed tasks and fix underlying issues")
    
    if performance.get("average_duration", 0) > 300:  # 5 minutes
        recommendations.append("Consider optimizing task performance")
    
    if not recommendations:
        recommendations.append("System is running well")
    
    return recommendations
