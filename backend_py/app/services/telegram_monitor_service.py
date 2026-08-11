"""
Telegram channel monitoring service for Tender Intelligence Platform
Monitors multiple Telegram channels for tender-related posts using Telethon
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Message

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.tender import Keyword
from app.models.telegram_channel import TelegramChannel
from app.services.keyword_filter import KeywordFilterService
from app.services.telegram_alerts import TelegramAlertService
from app.services.logging_service import LoggingService

@dataclass
class MonitoredChannel:
    """Configuration for a monitored Telegram channel"""
    channel_id: Optional[int]
    channel_username: str
    channel_name: str
    is_active: bool = True
    last_message_id: int = 0


class TelegramMonitorService:
    """Service for monitoring Telegram channels"""
    
    def __init__(self):
        self.client = None
        self.monitored_channels: List[MonitoredChannel] = []
        self.keyword_filter = KeywordFilterService()
        self.alert_service = TelegramAlertService()
        self.is_running = False
        self.last_reload = datetime.min
    
    async def initialize(self):
        """Initialize Telegram client"""
        try:
            # Initialize Telethon client
            self.client = TelegramClient(
                'telegram_monitor_session',
                api_id=settings.TELEGRAM_API_ID,
                api_hash=settings.TELEGRAM_API_HASH
            )
            
            await self.client.start()
            print("✅ Telegram monitor client initialized successfully")
            
            # Load monitored channels
            await self.load_monitored_channels()
            
            # Setup message handlers
            self.setup_message_handlers()
            
        except Exception as e:
            print(f"❌ Failed to initialize Telegram monitor: {e}")
            raise
    
    async def load_monitored_channels(self):
        """Load monitored channels from database"""
        db = SessionLocal()
        try:
            db_channels = db.query(TelegramChannel).filter(TelegramChannel.is_active == True).all()
            
            new_monitored = []
            for db_chan in db_channels:
                new_monitored.append(MonitoredChannel(
                    channel_id=None,  # Will be resolved below
                    channel_username=db_chan.username,
                    channel_name=db_chan.title or db_chan.username
                ))
            
            self.monitored_channels = new_monitored
            self.last_reload = datetime.now()
            
            # Get actual channel info from Telegram
            for channel in self.monitored_channels:
                try:
                    entity = await self.client.get_entity(channel.channel_username)
                    channel.channel_id = entity.id
                    if not channel.channel_name or channel.channel_name == channel.channel_username:
                        channel.channel_name = getattr(entity, 'title', channel.channel_username)
                    print(f"📡 Loaded channel from DB: {channel.channel_name} ({channel.channel_username})")
                except Exception as e:
                    print(f"⚠️  Could not load channel {channel.channel_username}: {e}")
                    channel.is_active = False
        finally:
            db.close()
    
    def setup_message_handlers(self):
        """Setup event handlers for new messages"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self.process_message(event)
    
    async def process_message(self, event):
        """Process a new message from monitored channels"""
        try:
            # Periodically reload channels (every 10 minutes)
            if (datetime.now() - self.last_reload).total_seconds() > 600:
                await self.load_monitored_channels()

            # Check if message is from a monitored channel
            if not event.is_channel:
                return
            
            # Get channel info
            channel = await event.get_chat()
            if not isinstance(channel, Channel):
                return
            
            # Check if this channel is being monitored
            monitored_channel = None
            for mc in self.monitored_channels:
                if mc.channel_id == channel.id or mc.channel_username == f"@{channel.username}":
                    monitored_channel = mc
                    break
            
            if not monitored_channel or not monitored_channel.is_active:
                return
            
            # Process message for keyword matching
            await self.check_message_for_keywords(event.message, monitored_channel)
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def check_message_for_keywords(self, message: Message, channel: MonitoredChannel):
        """Check if message contains tender-related keywords"""
        try:
            # Get current keywords from database
            db = SessionLocal()
            try:
                keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
                keyword_dtos = [{"id": str(k.id), "phrase": k.phrase} for k in keywords]
            finally:
                db.close()
            
            if not keywords:
                return
            
            # Extract text from message
            text = message.text or ""
            if message.media:
                # Try to extract text from media captions
                if hasattr(message.media, 'caption'):
                    text += " " + (message.media.caption or "")
            
            text = text.strip()
            if not text:
                return
            
            # Check for keyword matches
            matched_ids = self.keyword_filter.match(text, keyword_dtos)
            
            if matched_ids:
                matched_keywords = [k.phrase for k in keywords if str(k.id) in matched_ids]
                
                # Log the finding
                LoggingService.log_new_tender_found(
                    task_name="telegram_monitor",
                    source=f"Telegram: {channel.channel_name}",
                    tender_title=text[:100],  # First 100 chars as title
                    keywords=matched_keywords,
                    message=f"Telegram post with keywords found in {channel.channel_name}"
                )
                
                # Send alert
                await self.send_telegram_channel_alert(message, channel, matched_keywords)
                
                print(f"🔍 Found keywords {matched_keywords} in {channel.channel_name}: {text[:50]}...")
            
        except Exception as e:
            print(f"❌ Error checking message for keywords: {e}")
    
    async def send_telegram_channel_alert(self, message: Message, channel: MonitoredChannel, keywords: List[str]):
        """Send alert for Telegram channel post with keywords"""
        try:
            text = message.text or message.caption or ""
            
            # Format alert message
            alert_text = (
                f"🚨 Tender-related post found in Telegram channel\n\n"
                f"📱 Channel: {channel.channel_name}\n"
                f"🔑 Keywords: {', '.join(keywords)}\n\n"
                f"📄 Message:\n{text[:300]}{'...' if len(text) > 300 else ''}\n\n"
                f"🔗 Channel: {channel.channel_username}\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Send to alert chat
            await self.alert_service.bot.send_message(
                chat_id=settings.TELEGRAM_ALERT_CHAT_ID,
                text=alert_text
            )
            
            print(f"📤 Sent Telegram alert for channel post in {channel.channel_name}")
            
        except Exception as e:
            print(f"❌ Failed to send Telegram channel alert: {e}")
    
    async def start_monitoring(self):
        """Start monitoring Telegram channels"""
        if self.is_running:
            print("⚠️  Telegram monitoring is already running")
            return
        
        try:
            await self.initialize()
            
            self.is_running = True
            print("🚀 Telegram channel monitoring started")
            
            # Keep the client running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            print(f"❌ Failed to start Telegram monitoring: {e}")
            self.is_running = False
            raise
    
    async def stop_monitoring(self):
        """Stop monitoring Telegram channels"""
        if not self.is_running:
            return
        
        try:
            if self.client:
                await self.client.disconnect()
            
            self.is_running = False
            print("🛑 Telegram channel monitoring stopped")
            
        except Exception as e:
            print(f"❌ Error stopping Telegram monitoring: {e}")
    
    async def add_channel(self, channel_username: str, channel_name: str) -> bool:
        """Add a new channel to monitor"""
        try:
            # Get channel info
            entity = await self.client.get_entity(channel_username)
            
            new_channel = MonitoredChannel(
                channel_id=entity.id,
                channel_username=channel_username,
                channel_name=channel_name,
                is_active=True
            )
            
            self.monitored_channels.append(new_channel)
            print(f"➕ Added channel to monitoring: {channel_name} ({channel_username})")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add channel {channel_username}: {e}")
            return False
    
    async def remove_channel(self, channel_username: str) -> bool:
        """Remove a channel from monitoring"""
        try:
            self.monitored_channels = [
                ch for ch in self.monitored_channels 
                if ch.channel_username != channel_username
            ]
            print(f"➖ Removed channel from monitoring: {channel_username}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove channel {channel_username}: {e}")
            return False
    
    async def get_monitored_channels(self) -> List[Dict[str, Any]]:
        """Get list of monitored channels"""
        channels_info = []
        for channel in self.monitored_channels:
            channels_info.append({
                "channel_id": channel.channel_id,
                "channel_username": channel.channel_username,
                "channel_name": channel.channel_name,
                "is_active": channel.is_active,
                "last_message_id": channel.last_message_id
            })
        
        return channels_info
    
    async def test_monitoring(self, test_message: str = "Test tender post: строительство склада 1000м²") -> Dict[str, Any]:
        """Test keyword matching with a test message"""
        try:
            # Get current keywords
            db = SessionLocal()
            try:
                keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
                keyword_dtos = [{"id": str(k.id), "phrase": k.phrase} for k in keywords]
            finally:
                db.close()
            
            # Test keyword matching
            matched_ids = self.keyword_filter.match(test_message, keyword_dtos)
            matched_keywords = [k.phrase for k in keywords if str(k.id) in matched_ids]
            
            return {
                "success": True,
                "test_message": test_message,
                "matched_keywords": matched_keywords,
                "total_keywords": len(keywords),
                "match_count": len(matched_keywords)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance for reuse
_telegram_monitor_service = None

def get_telegram_monitor_service() -> TelegramMonitorService:
    """Get or create Telegram monitor service instance"""
    global _telegram_monitor_service
    if _telegram_monitor_service is None:
        _telegram_monitor_service = TelegramMonitorService()
    return _telegram_monitor_service


# Celery task for running Telegram monitoring
async def run_telegram_monitoring():
    """Run Telegram monitoring as a background task"""
    monitor_service = get_telegram_monitor_service()
    try:
        await monitor_service.start_monitoring()
    except Exception as e:
        print(f"❌ Telegram monitoring crashed: {e}")
        # Log the error
        LoggingService.log_task_failed(
            log_id="telegram_monitor",
            error=e,
            message="Telegram monitoring service crashed"
        )
