import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.excel_export_service import ExcelExportService

router = APIRouter(prefix="/export", tags=["excel-export"])


class CustomExportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    with_keywords_only: bool = True
    limit: Optional[int] = None


@router.get("/daily")
def export_daily_excel(
    date: Optional[datetime] = Query(None, description="Date for daily export (YYYY-MM-DD format)")
) -> StreamingResponse:
    """Export daily tenders to Excel format"""
    try:
        excel_data = ExcelExportService.get_daily_export(date)
        
        filename = f"tenders_daily_{date.strftime('%Y%m%d') if date else datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Daily export failed: {str(e)}")


@router.get("/weekly")
def export_weekly_excel(
    date: Optional[datetime] = Query(None, description="Date for weekly export (YYYY-MM-DD format)")
) -> StreamingResponse:
    """Export weekly tenders to Excel format"""
    try:
        excel_data = ExcelExportService.get_weekly_export(date)
        
        filename = f"tenders_weekly_{date.strftime('%Y%m%d') if date else datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weekly export failed: {str(e)}")


@router.get("/monthly")
def export_monthly_excel(
    date: Optional[datetime] = Query(None, description="Date for monthly export (YYYY-MM-DD format)")
) -> StreamingResponse:
    """Export monthly tenders to Excel format"""
    try:
        excel_data = ExcelExportService.get_monthly_export(date)
        
        filename = f"tenders_monthly_{date.strftime('%Y%m') if date else datetime.now().strftime('%Y%m')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monthly export failed: {str(e)}")


@router.post("/custom")
def export_custom_excel(request: CustomExportRequest) -> StreamingResponse:
    """Export tenders for custom date range to Excel format"""
    try:
        excel_data = ExcelExportService.get_custom_export(
            start_date=request.start_date,
            end_date=request.end_date,
            with_keywords_only=request.with_keywords_only,
            limit=request.limit
        )
        
        filename = f"tenders_custom_{request.start_date.strftime('%Y%m%d')}_to_{request.end_date.strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom export failed: {str(e)}")


@router.get("/statistics")
def get_export_statistics() -> dict:
    """Get export statistics for different time periods"""
    try:
        stats = ExcelExportService.get_export_statistics()
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/preview")
def preview_export_data(
    period: str = Query(..., pattern="^(daily|weekly|monthly)$"),
    date: Optional[datetime] = Query(None, description="Date for preview (YYYY-MM-DD format)"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to preview")
) -> dict:
    """Preview export data without downloading"""
    try:
        # Get date ranges based on period
        if date is None:
            date = datetime.now()
        
        if period == "daily":
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif period == "weekly":
            start_date = date - timedelta(days=date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        else:  # monthly
            start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end_date = date.replace(year=date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                end_date = date.replace(month=date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get tenders for preview
        tenders = ExcelExportService.get_tenders_with_keywords(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            with_keywords_only=False  # Show all for preview
        )
        
        # Format for response
        preview_data = []
        for tender in tenders:
            preview_data.append({
                'id': tender['id'],
                'title': tender['title'][:100] + '...' if len(tender['title']) > 100 else tender['title'],
                'amount': tender['amount'],
                'region': tender['region'],
                'source': tender['source'],
                'created_at': tender['created_at'].isoformat() if tender['created_at'] else None,
                'keywords_count': len(tender['keywords']),
                'keywords': tender['keywords'][:5]  # Show first 5 keywords
            })
        
        return {
            "success": True,
            "period": period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_available": len(tenders),
            "preview": preview_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/download-info")
def get_download_info() -> dict:
    """Get information about available export options"""
    now = datetime.now()
    
    # Calculate date ranges
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
    
    return {
        "export_options": {
            "daily": {
                "description": "Export tenders from today (00:00 to 23:59)",
                "date_range": f"{daily_start.strftime('%Y-%m-%d %H:%M')} to {daily_end.strftime('%Y-%m-%d %H:%M')}",
                "endpoint": "/export/daily"
            },
            "weekly": {
                "description": "Export tenders from current week (Monday to Sunday)",
                "date_range": f"{weekly_start.strftime('%Y-%m-%d %H:%M')} to {weekly_end.strftime('%Y-%m-%d %H:%M')}",
                "endpoint": "/export/weekly"
            },
            "monthly": {
                "description": "Export tenders from current month",
                "date_range": f"{monthly_start.strftime('%Y-%m-%d %H:%M')} to {monthly_end.strftime('%Y-%m-%d %H:%M')}",
                "endpoint": "/export/monthly"
            },
            "custom": {
                "description": "Export tenders for custom date range",
                "endpoint": "/export/custom",
                "method": "POST"
            }
        },
        "file_format": "Excel (.xlsx)",
        "features": [
            "Multiple sheets (Tenders, Summary, Keywords Analysis)",
            "Auto-adjusted column widths",
            "Keyword matching statistics",
            "Date range filtering",
            "Custom export options"
        ]
    }
