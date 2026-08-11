from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.db.deps import get_db
from app.services.google_sheets_service import get_google_sheets_service
from app.core.config import settings

router = APIRouter(prefix="/google-sheets", tags=["google-sheets"])


class GoogleSheetsSetupRequest(BaseModel):
    spreadsheet_name: Optional[str] = None
    share_email: Optional[str] = None


class GoogleSheetsExportRequest(BaseModel):
    limit: int = 100
    force_all: bool = False


@router.post("/setup")
def setup_google_sheets(request: GoogleSheetsSetupRequest) -> Dict[str, Any]:
    """Setup or reconnect to Google Sheets"""
    try:
        sheets_service = get_google_sheets_service()
        
        spreadsheet_name = request.spreadsheet_name or settings.GOOGLE_SHEETS_SPREADSHEET_NAME
        share_email = request.share_email or settings.GOOGLE_SHEETS_SHARE_EMAIL
        
        # Update settings if provided
        if request.share_email:
            settings.GOOGLE_SHEETS_SHARE_EMAIL = request.share_email
        
        success = sheets_service.setup_spreadsheet(spreadsheet_name)
        
        if success:
            return {
                "success": True,
                "message": f"Google Sheets setup completed",
                "spreadsheet_url": sheets_service.get_spreadsheet_url(),
                "spreadsheet_name": spreadsheet_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to setup Google Sheets")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets setup failed: {str(e)}")


@router.get("/status")
def get_google_sheets_status() -> Dict[str, Any]:
    """Get Google Sheets connection status"""
    try:
        sheets_service = get_google_sheets_service()
        
        status = {
            "connected": sheets_service.client is not None,
            "spreadsheet_url": sheets_service.get_spreadsheet_url(),
            "auto_export_enabled": settings.GOOGLE_SHEETS_AUTO_EXPORT,
            "spreadsheet_name": settings.GOOGLE_SHEETS_SPREADSHEET_NAME
        }
        
        if sheets_service.worksheet:
            # Get worksheet info
            try:
                existing_ids = sheets_service.get_existing_tender_ids()
                status["existing_tenders_count"] = len(existing_ids)
                status["worksheet_ready"] = True
            except:
                status["worksheet_ready"] = False
        else:
            status["worksheet_ready"] = False
            status["existing_tenders_count"] = 0
        
        return status
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "auto_export_enabled": settings.GOOGLE_SHEETS_AUTO_EXPORT
        }


@router.post("/export")
def export_to_google_sheets(
    request: GoogleSheetsExportRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Export tenders to Google Sheets"""
    try:
        sheets_service = get_google_sheets_service()
        
        if request.force_all:
            # Clear existing data and export all
            sheets_service.clear_all_data()
            result = sheets_service.export_new_tenders(limit=request.limit)
        else:
            # Export only new tenders
            result = sheets_service.export_new_tenders(limit=request.limit)
        
        return {
            "success": True,
            "result": result,
            "spreadsheet_url": sheets_service.get_spreadsheet_url()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/clear")
def clear_google_sheets() -> Dict[str, Any]:
    """Clear all data from Google Sheets (for testing/reset)"""
    try:
        sheets_service = get_google_sheets_service()
        success = sheets_service.clear_all_data()
        
        return {
            "success": success,
            "message": "Google Sheets data cleared successfully" if success else "Failed to clear data"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


@router.get("/spreadsheet-url")
def get_spreadsheet_url() -> Dict[str, str]:
    """Get the URL of the Google Sheets spreadsheet"""
    try:
        sheets_service = get_google_sheets_service()
        url = sheets_service.get_spreadsheet_url()
        
        if url:
            return {"url": url}
        else:
            raise HTTPException(status_code=404, detail="Spreadsheet not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get URL: {str(e)}")


@router.post("/test-connection")
def test_google_sheets_connection() -> Dict[str, Any]:
    """Test Google Sheets connection"""
    try:
        sheets_service = get_google_sheets_service()
        
        # Test basic operations
        test_results = {
            "credentials_loaded": sheets_service.client is not None,
            "spreadsheet_accessible": False,
            "worksheet_accessible": False
        }
        
        if sheets_service.client:
            try:
                if sheets_service.spreadsheet:
                    test_results["spreadsheet_accessible"] = True
                    
                    if sheets_service.worksheet:
                        test_results["worksheet_accessible"] = True
                        # Test reading data
                        existing_ids = sheets_service.get_existing_tender_ids()
                        test_results["can_read_data"] = True
                        test_results["existing_rows"] = len(existing_ids)
            except Exception as e:
                test_results["error"] = str(e)
        
        return {
            "success": all([
                test_results["credentials_loaded"],
                test_results["spreadsheet_accessible"],
                test_results["worksheet_accessible"]
            ]),
            "test_results": test_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/settings")
def get_google_sheets_settings() -> Dict[str, Any]:
    """Get current Google Sheets settings"""
    return {
        "auto_export_enabled": settings.GOOGLE_SHEETS_AUTO_EXPORT,
        "spreadsheet_name": settings.GOOGLE_SHEETS_SPREADSHEET_NAME,
        "share_email": settings.GOOGLE_SHEETS_SHARE_EMAIL,
        "has_credentials": bool(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    }


@router.post("/settings")
def update_google_sheets_settings(
    auto_export: Optional[bool] = None,
    spreadsheet_name: Optional[str] = None,
    share_email: Optional[str] = None
) -> Dict[str, Any]:
    """Update Google Sheets settings"""
    try:
        updated_settings = {}
        
        if auto_export is not None:
            settings.GOOGLE_SHEETS_AUTO_EXPORT = auto_export
            updated_settings["auto_export_enabled"] = auto_export
        
        if spreadsheet_name is not None:
            settings.GOOGLE_SHEETS_SPREADSHEET_NAME = spreadsheet_name
            updated_settings["spreadsheet_name"] = spreadsheet_name
        
        if share_email is not None:
            settings.GOOGLE_SHEETS_SHARE_EMAIL = share_email
            updated_settings["share_email"] = share_email
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "updated_settings": updated_settings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
