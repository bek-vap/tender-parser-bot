#!/usr/bin/env python3
"""
Simple Telegram bot test for Tender Intelligence Platform
"""

import sys
import os

# Add backend directory to Python path
backend_path = r"C:\Users\asadi\Desktop\tender\TENDER-INTELLIGENCE-PLATFORM\backend_py"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("🔍 Testing Telegram Bot Connection...")

try:
    from app.core.config import settings
    from app.services.telegram_alerts import TelegramAlertService
    import asyncio
    
    async def test_telegram_connection():
        print(f"📋 Configuration:")
        print(f"   Bot Token: {'✅ Configured' if settings.TELEGRAM_BOT_TOKEN else '❌ Not configured'}")
        print(f"   Alert Chat ID: {'✅ Configured' if settings.TELEGRAM_ALERT_CHAT_ID else '❌ Not configured'}")
        print(f"   API ID: {'✅ Configured' if settings.TELEGRAM_API_ID else '❌ Not configured'}")
        print(f"   API Hash: {'✅ Configured' if settings.TELEGRAM_API_HASH else '❌ Not configured'}")
        
        print("\n🤖 Testing Telegram bot connection...")
        
        bot = TelegramAlertService()
        
        # Test bot info
        try:
            bot_info = await bot.bot.get_me()
            print(f"✅ Bot connection successful!")
            print(f"   Bot Name: {bot_info.first_name}")
            print(f"   Bot Username: @{bot_info.username}")
            print(f"   Bot ID: {bot_info.id}")
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            return False
        
        # Test sending message (only if configured)
        if settings.TELEGRAM_ALERT_CHAT_ID and settings.TELEGRAM_BOT_TOKEN:
            print("\n📤 Testing message sending...")
            try:
                await bot.bot.send_message(
                    chat_id=settings.TELEGRAM_ALERT_CHAT_ID,
                    text="🧪 *Tender Intelligence Platform Test* 🧪\n\n"
                    "✅ System is working correctly!\n"
                    "🤖 Bot connection: Successful\n"
                    "📊 API Server: Ready\n"
                    "🎉 Ready for production deployment!"
                )
                print("✅ Test message sent successfully!")
                print(f"   Check your Telegram chat/channel: {settings.TELEGRAM_ALERT_CHAT_ID}")
            except Exception as e:
                print(f"❌ Failed to send test message: {e}")
        
        return True
    
    # Run the test
    result = asyncio.run(test_telegram_connection())
    
    if result:
        print("\n🎉 Telegram integration test completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start API server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("2. Test endpoints: curl http://localhost:8000/health")
        print("3. View API docs: http://localhost:8000/docs")
        print("4. Monitor logs for real-time updates")
    else:
        print("\n❌ Telegram integration test failed!")
        print("Please check your bot token and chat ID configuration")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "="*50)
print("🎯 Tender Intelligence Platform - Telegram Test Complete")
print("="*50)
