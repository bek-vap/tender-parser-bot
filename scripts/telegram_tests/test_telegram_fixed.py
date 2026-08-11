import sys
import os

# Add backend directory to Python path
backend_path = r"C:\Users\asadi\Desktop\tender\TENDER-INTELLIGENCE-PLATFORM\backend_py"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Telegram Bot Real-Time Test")
print("=" * 50)

try:
    from app.core.config import settings
    from app.services.telegram_alerts import TelegramAlertService
    import asyncio
    
    print("Configuration Check:")
    print(f"   Bot Token: {'Configured' if settings.TELEGRAM_BOT_TOKEN else 'Not configured'}")
    print(f"   Alert Chat ID: {'Configured' if settings.TELEGRAM_ALERT_CHAT_ID else 'Not configured'}")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("\nTELEGRAM_BOT_TOKEN not configured!")
        print("Please set your bot token in .env file")
        input("Press Enter to exit...")
        sys.exit(1)
    
    if not settings.TELEGRAM_ALERT_CHAT_ID:
        print("\nTELEGRAM_ALERT_CHAT_ID not configured!")
        print("Please set your alert chat ID in .env file")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("\nTesting Telegram Bot Connection...")
    
    async def test_telegram():
        bot = TelegramAlertService()
        
        # Test bot info
        try:
            bot_info = await bot.bot.get_me()
            print("Bot connected successfully!")
            print(f"   Bot Name: {bot_info.first_name}")
            print(f"   Bot Username: @{bot_info.username}")
            print(f"   Bot ID: {bot_info.id}")
        except Exception as e:
            print(f"Bot connection failed: {e}")
            return False
        
        # Test sending message
        try:
            print(f"\nSending test message to {settings.TELEGRAM_ALERT_CHAT_ID}...")
            
            test_message = (
                "*Tender Intelligence Platform - Real-Time Test*\n\n"
                "**System Status**: Working\n"
                "**Bot Connection**: Successful\n"
                "**API Server**: Ready\n"
                "**Platform is ready for real-time monitoring!**\n\n"
                "**Next Steps**:\n"
                "1. Start API server: uvicorn app.main:app --host 0.0.0.0 --port 8000\n"
                "2. Monitor logs for real-time updates\n"
                "3. Test manual scraping: POST http://localhost:8000/api/tasks/trigger\n"
                "4. Check Telegram for automatic alerts\n"
                "5. View API docs: http://localhost:8000/docs"
            )
            
            await bot.bot.send_message(
                chat_id=settings.TELEGRAM_ALERT_CHAT_ID,
                text=test_message,
                parse_mode="Markdown"
            )
            
            print("Test message sent successfully!")
            print(f"Check your Telegram chat/channel: {settings.TELEGRAM_ALERT_CHAT_ID}")
            
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
        
        return True
    
    # Run the test
    result = asyncio.run(test_telegram())
    
    if result:
        print("\nTelegram integration test completed successfully!")
        print("\nReal-Time Testing Instructions:")
        print("1. Start API server:")
        print("   cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\n2. Test manual scraping:")
        print("   curl -X POST http://localhost:8000/api/tasks/trigger")
        print("\n3. Monitor for automatic alerts:")
        print("   - Check your Telegram chat/channel")
        print("   - Monitor API server logs")
        print("   - Check Google Sheets for exports")
        print("\n4. View API documentation:")
        print("   http://localhost:8000/docs")
        print("\nYour bot will send real-time notifications when:")
        print("   - New tenders are found")
        print("   - Keyword matches occur")
        print("   - System events happen")
    else:
        print("\nTelegram integration test failed!")
        print("Please check your bot configuration")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
except Exception as e:
    print(f"Unexpected error: {e}")

print("\n" + "=" * 50)
input("Press Enter to exit...")
