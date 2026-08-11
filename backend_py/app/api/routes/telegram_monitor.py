from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.telegram_monitor_service import get_telegram_monitor_service
from app.core.config import settings

router = APIRouter(prefix="/telegram-monitor", tags=["telegram-monitor"])


class ChannelAddRequest(BaseModel):
    channel_username: str
    channel_name: str


class ChannelTestRequest(BaseModel):
    test_message: str = "Test tender post: строительство склада 1000м²"


@router.get("/status")
def get_telegram_monitor_status() -> Dict[str, Any]:
    """Get Telegram monitoring status"""
    try:
        monitor_service = get_telegram_monitor_service()
        
        status = {
            "enabled": settings.TELEGRAM_MONITOR_ENABLED,
            "configured": bool(settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH),
            "running": monitor_service.is_running,
            "api_id_set": bool(settings.TELEGRAM_API_ID),
            "api_hash_set": bool(settings.TELEGRAM_API_HASH),
            "monitored_channels_count": len(monitor_service.monitored_channels) if monitor_service.monitored_channels else 0
        }
        
        return status
        
    except Exception as e:
        return {
            "enabled": False,
            "configured": False,
            "running": False,
            "error": str(e)
        }


@router.get("/channels")
async def get_monitored_channels() -> Dict[str, Any]:
    """Get list of monitored channels"""
    try:
        monitor_service = get_telegram_monitor_service()
        channels = await monitor_service.get_monitored_channels()
        
        return {
            "success": True,
            "channels": channels,
            "total_count": len(channels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@router.post("/channels")
async def add_monitored_channel(
    request: ChannelAddRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Add a new channel to monitor"""
    try:
        if not settings.TELEGRAM_MONITOR_ENABLED:
            raise HTTPException(status_code=400, detail="Telegram monitoring is disabled")
        
        monitor_service = get_telegram_monitor_service()
        
        # Add channel
        success = await monitor_service.add_channel(
            channel_username=request.channel_username,
            channel_name=request.channel_name
        )
        
        if success:
            return {
                "success": True,
                "message": f"Channel {request.channel_name} added successfully",
                "channel_username": request.channel_username,
                "channel_name": request.channel_name
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add channel")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add channel: {str(e)}")


@router.delete("/channels/{channel_username}")
async def remove_monitored_channel(channel_username: str) -> Dict[str, Any]:
    """Remove a channel from monitoring"""
    try:
        monitor_service = get_telegram_monitor_service()
        
        success = await monitor_service.remove_channel(channel_username)
        
        if success:
            return {
                "success": True,
                "message": f"Channel {channel_username} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Channel not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove channel: {str(e)}")


@router.post("/test")
async def test_telegram_monitoring(request: ChannelTestRequest) -> Dict[str, Any]:
    """Test keyword matching with Telegram monitoring"""
    try:
        monitor_service = get_telegram_monitor_service()
        result = await monitor_service.test_monitoring(request.test_message)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/start")
async def start_telegram_monitoring(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start Telegram channel monitoring"""
    try:
        if not settings.TELEGRAM_MONITOR_ENABLED:
            raise HTTPException(status_code=400, detail="Telegram monitoring is disabled")
        
        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            raise HTTPException(status_code=400, detail="Telegram API credentials not configured")
        
        monitor_service = get_telegram_monitor_service()
        
        if monitor_service.is_running:
            return {
                "success": True,
                "message": "Telegram monitoring is already running"
            }
        
        # Start monitoring in background
        background_tasks.add_task(monitor_service.start_monitoring)
        
        return {
            "success": True,
            "message": "Telegram monitoring started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/stop")
async def stop_telegram_monitoring() -> Dict[str, Any]:
    """Stop Telegram channel monitoring"""
    try:
        monitor_service = get_telegram_monitor_service()
        
        if not monitor_service.is_running:
            return {
                "success": True,
                "message": "Telegram monitoring is not running"
            }
        
        await monitor_service.stop_monitoring()
        
        return {
            "success": True,
            "message": "Telegram monitoring stopped successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.get("/settings")
def get_telegram_monitor_settings() -> Dict[str, Any]:
    """Get Telegram monitoring settings"""
    return {
        "enabled": settings.TELEGRAM_MONITOR_ENABLED,
        "api_id_configured": bool(settings.TELEGRAM_API_ID),
        "api_hash_configured": bool(settings.TELEGRAM_API_HASH),
        "channels_configured": bool(settings.TELEGRAM_MONITOR_CHANNELS),
        "bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "alert_chat_configured": bool(settings.TELEGRAM_ALERT_CHAT_ID)
    }


@router.post("/settings")
def update_telegram_monitor_settings(
    enabled: Optional[bool] = None,
    channels_json: Optional[str] = None
) -> Dict[str, Any]:
    """Update Telegram monitoring settings"""
    try:
        updated_settings = {}
        
        if enabled is not None:
            settings.TELEGRAM_MONITOR_ENABLED = enabled
            updated_settings["enabled"] = enabled
        
        if channels_json is not None:
            settings.TELEGRAM_MONITOR_CHANNELS = channels_json
            updated_settings["channels_configured"] = True
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "updated_settings": updated_settings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/help")
def get_telegram_monitor_help() -> Dict[str, Any]:
    """Get help information for Telegram monitoring setup"""
    return {
        "setup_instructions": {
            "1_get_api_credentials": {
                "description": "Get API ID and Hash from my.telegram.org",
                "url": "https://my.telegram.org",
                "steps": [
                    "Sign in with your phone number",
                    "Go to API development tools",
                    "Create a new application",
                    "Copy API ID and API Hash"
                ]
            },
            "2_configure_environment": {
                "description": "Set environment variables",
                "variables": [
                    "TELEGRAM_API_ID",
                    "TELEGRAM_API_HASH",
                    "TELEGRAM_MONITOR_ENABLED=true"
                ]
            },
            "3_add_channels": {
                "description": "Add channels to monitor using API",
                "endpoint": "POST /api/telegram-monitor/channels",
                "example": {
                    "channel_username": "@uzex_official",
                    "channel_name": "UZEX Official"
                }
            },
            "4_start_monitoring": {
                "description": "Start the monitoring service",
                "endpoint": "POST /api/telegram-monitor/start"
            }
        },
        "channel_categories": [
            "qurilish",
            "agroklaster", 
            "investitsiya",
            "tender",
            "logistika",
            "sklad",
            "zavod",
            "fermalar",
            "hokimlik",
            "modernizatsiya",
            "rekonstruksiya"
        ],
        "channel_examples": [
            "@uzex_official",
            "@xarid_uz",
            "@tender_mc_uz",
            "@invest_uzb",
            "@qurilish_uz"
        ],
        "monitoring_features": [
            "Real-time message monitoring",
            "Keyword matching",
            "Automatic alerts",
            "Multiple channel support",
            "Duplicate detection",
            "Message filtering"
        ]
    }
