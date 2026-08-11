from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.deps import get_db
from app.models.tender import Tender, Keyword
from app.models.log import ParserLog
from app.services.logging_service import LoggingService
from app.workers.celery_app import celery_app
from app.core.config import settings
import time


router = APIRouter(prefix="/tasks", tags=["tasks"])

# Simple in‑memory rate limiter for cron requests
_last_cron_call = 0.0  # timestamp of last cron request (monotonic)
MIN_INTERVAL = 5  # seconds between allowed cron calls



class TaskTriggerRequest(BaseModel):
    task_name: str
    immediate: bool = False


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class LogResponse(BaseModel):
    id: str
    task_name: str
    source: str
    status: str
    message: Optional[str]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    items_processed: Optional[int]
    items_found: Optional[int]

    class Config:
        from_attributes = True


@router.get("/trigger-cron", response_model=TaskResponse)
def trigger_cron(
    task_name: str,
    immediate: bool = False,
    secret: str = "",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Endpoint for external cron jobs.
    Requires `secret` matching `settings.CRON_SECRET` and respects a simple rate limit.
    """
    # Secret validation
    if not settings.CRON_SECRET or secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    # Rate limiting
    global _last_cron_call
    now = time.monotonic()
    if now - _last_cron_call < MIN_INTERVAL:
        raise HTTPException(status_code=429, detail="Too many requests – please wait")
    _last_cron_call = now

    # Reuse existing trigger logic
    request = TaskTriggerRequest(task_name=task_name, immediate=immediate)
    return trigger_task(request, background_tasks, db)

@router.post("/trigger", response_model=TaskResponse)
def trigger_task(
    request: TaskTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """Manually trigger a scraping/processing task"""
    import asyncio
    
    from app.workers.tasks import (
        scrape_uzex_etender,
        scrape_xarid_uzex,
        scrape_tender_mc,
        scrape_e_auksion,
        process_winners,
        enrich_companies
    )
    
    task_map = {
        "scrape_uzex_etender": scrape_uzex_etender,
        "scrape_xarid_uzex": scrape_xarid_uzex,
        "scrape_tender_mc": scrape_tender_mc,
        "scrape_e_auksion": scrape_e_auksion,
        "process_winners": process_winners,
        "enrich_companies": enrich_companies,
    }
    
    if request.task_name == "all":
        async def run_all():
            # Allow Uvicorn to fully flush the HTTP response and close connection with cron-job.org
            await asyncio.sleep(2)
            print("🔄 Running all scrapers in sequence...")
            for name, func in task_map.items():
                try:
                    print(f"Executing background task in thread: {name}")
                    await asyncio.to_thread(func)
                except Exception as e:
                    print(f"Error executing background task {name}: {e}")
            print("✅ All scrapers finished background execution.")
            
        if request.immediate:
            # Sync execution for manual debug
            print("🔄 Running all scrapers in sequence synchronously...")
            for name, func in task_map.items():
                try:
                    func()
                except Exception as e:
                    print(f"Error: {e}")
            return TaskResponse(
                task_id="all_sync",
                status="completed",
                message="All scraper tasks executed synchronously."
            )
        else:
            background_tasks.add_task(run_all)
            return TaskResponse(
                task_id="all_async",
                status="queued",
                message="All scraper tasks queued in sequence as a FastAPI BackgroundTask."
            )
            
    elif request.task_name in task_map:
        task_func = task_map[request.task_name]
        
        async def run_single():
            # Allow Uvicorn to fully flush the HTTP response first
            await asyncio.sleep(2)
            try:
                print(f"Executing background task in thread: {request.task_name}")
                await asyncio.to_thread(task_func)
            except Exception as e:
                print(f"Error executing background task {request.task_name}: {e}")
        
        if request.immediate:
            try:
                result = task_func()
                return TaskResponse(
                    task_id="sync",
                    status="completed",
                    message=f"Task {request.task_name} completed immediately. Result: {result}"
                )
            except Exception as e:
                return TaskResponse(
                    task_id="sync",
                    status="failed",
                    message=f"Task failed: {str(e)}"
                )
        else:
            background_tasks.add_task(run_single)
            return TaskResponse(
                task_id="async",
                status="queued",
                message=f"Task {request.task_name} queued as a FastAPI BackgroundTask."
            )
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown task: {request.task_name}. Available tasks: {list(task_map.keys())} or 'all'"
        )


@router.get("/status/{task_id}")
def get_task_status(task_id: str) -> dict:
    """Get status of a Celery task"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.state,
            "result": result.result if result.state == "SUCCESS" else None,
            "error": str(result.result) if result.state == "FAILURE" else None
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/logs", response_model=List[LogResponse])
def get_task_logs(
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[ParserLog]:
    """Get recent task logs with optional status filter"""
    query = db.query(ParserLog).order_by(ParserLog.started_at.desc())
    if status_filter:
        query = query.filter(ParserLog.status == status_filter)
    return query.limit(limit).all()


@router.get("/logs/stats")
def get_task_statistics(days: int = 7, db: Session = Depends(get_db)) -> dict:
    """Get task execution statistics for the last N days"""
    return LoggingService.get_task_statistics(days)


@router.post("/test-keywords")
def test_keyword_matching(db: Session = Depends(get_db)) -> dict:
    """Test keyword matching on current database contents"""
    from app.services.keyword_filter import KeywordFilterService
    from app.clients.uzex_etender_api import UzexEtenderApiClient
    
    try:
        # Load keywords
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        keyword_dtos = [{"id": str(k.id), "phrase": k.phrase} for k in keywords]
        keyword_filter = KeywordFilterService()
        
        # Get sample tenders from database
        sample_tenders = db.query(Tender).limit(20).all()
        
        matches_count = 0
        matches_details = []
        
        for tender in sample_tenders:
            text_to_match = f"{tender.title} {tender.region or ''}"
            matched_ids = keyword_filter.match(text_to_match, keyword_dtos)
            
            if matched_ids:
                matches_count += 1
                matched_keywords = [k.phrase for k in keywords if str(k.id) in matched_ids]
                matches_details.append({
                    "tender_title": tender.title,
                    "matched_keywords": matched_keywords
                })
        
        coverage_percentage = (matches_count / len(sample_tenders)) * 100 if sample_tenders else 0
        
        return {
            "total_keywords": len(keywords),
            "sample_tenders_tested": len(sample_tenders),
            "tenders_with_matches": matches_count,
            "coverage_percentage": round(coverage_percentage, 2),
            "sample_matches": matches_details[:5]  # Return first 5 matches
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword matching test failed: {str(e)}")


@router.get("/health")
def get_system_health(db: Session = Depends(get_db)) -> dict:
    """Get overall system health status"""
    try:
        # Check database connectivity
        tender_count = db.query(Tender).count()
        keyword_count = db.query(Keyword).count()
        
        # Check recent logs for errors
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_errors = db.query(ParserLog).filter(
            ParserLog.started_at >= recent_cutoff,
            ParserLog.status == "failed"
        ).count()
        
        # Check Celery worker status
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            worker_status = "healthy" if active_tasks else "idle"
        except:
            worker_status = "disconnected"
        
        return {
            "database": "connected",
            "tender_count": tender_count,
            "keyword_count": keyword_count,
            "celery_worker": worker_status,
            "recent_errors_24h": recent_errors,
            "system_status": "healthy" if recent_errors < 5 else "degraded"
        }
        
    except Exception as e:
        return {
            "database": "disconnected",
            "error": str(e),
            "system_status": "unhealthy"
        }
