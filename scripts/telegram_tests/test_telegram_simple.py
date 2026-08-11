import sys
import os

# Add backend directory to Python path
backend_path = r"C:\Users\asadi\Desktop\tender\TENDER-INTELLIGENCE-PLATFORM\backend_py"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("📱 Telegram Bot Test - Tender Intelligence Platform")
print("=" * 60)

try:
    from app.core.config import settings
    from app.services.telegram_alerts import TelegramAlertService
    import asyncio
    
    print("🔧 Configuration Check:")
    print(f"   Bot Token: {'✅' if settings.TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"   Alert Chat ID: {'✅' if settings.TELEGRAM_ALERT_CHAT_ID else '❌'}")
    print(f"   API ID: {'✅' if settings.TELEGRAM_API_ID else '❌'}")
    print(f"   API Hash: {'✅' if settings.TELEGRAM_API_HASH else '❌'}")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("\n❌ TELEGRAM_BOT_TOKEN not configured!")
        print("Please set your bot token in .env file")
        sys.exit(1)
    
    if not settings.TELEGRAM_ALERT_CHAT_ID:
        print("\n❌ TELEGRAM_ALERT_CHAT_ID not configured!")
        print("Please set your alert chat ID in .env file")
        sys.exit(1)
    
    print("\n🤖 Testing Telegram Bot Connection...")
    
    async def test_bot():
        bot = TelegramAlertService()
        
        # Test bot info
        try:
            bot_info = await bot.bot.get_me()
            print(f"✅ Bot connected successfully!")
            print(f"   Bot Name: {bot_info.first_name}")
            print(f"   Bot Username: @{bot_info.username}")
            print(f"   Bot ID: {bot_info.id}")
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            return False
        
        # Test sending message
        try:
            print(f"\n📤 Sending test message to {settings.TELEGRAM_ALERT_CHAT_ID}...")
            
            test_message = (
                "🧪 *Tender Intelligence Platform Test* 🧪\n\n"
                "✅ **System Status**: Working\n"
                "🤖 **Bot Connection**: Successful\n"
                "📊 **API Server**: Ready\n"
                "🎯 **Current Time**: " + str(asyncio.get_event_loop().time())[:10] + "\n\n"
                "🎉 **Platform is ready for production!**"
            )
            
            await bot.bot.send_message(
                chat_id=settings.TELEGRAM_ALERT_CHAT_ID,
                text=test_message,
                parse_mode="Markdown"
            )
            
            print("✅ Test message sent successfully!")
            print(f"📱 Check your Telegram chat/channel: {settings.TELEGRAM_ALERT_CHAT_ID}")
            
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            return False
        
        return True
    
    # Run the test
    result = asyncio.run(test_bot())
    
    if result:
        print("\n🎉 Telegram integration test completed successfully!")
        print("\n📋 Real-time Testing Instructions:")
        print("1. Start API server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("2. Monitor logs for real-time updates")
        print("3. Test manual scraping: POST http://localhost:8000/api/tasks/trigger")
        print("4. Check Telegram for automatic alerts")
        print("\n🔗 API Documentation: http://localhost:8000/docs")
    else:
        print("\n❌ Telegram integration test failed!")
        print("Please check your bot configuration")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "=" * 60)
