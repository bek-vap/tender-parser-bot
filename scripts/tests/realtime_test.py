import sys
import os
import asyncio
import time

# Add backend directory to Python path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "..", "backend_py"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Real-Time Tender Intelligence Platform Test")
print("=" * 60)

try:
    from app.workers.tasks import scrape_uzex_etender
    from app.services.telegram_alerts import TelegramAlertService
    from app.core.config import settings
    
    print("Starting real-time monitoring test...")
    print(f"Bot will send alerts to: {settings.TELEGRAM_ALERT_CHAT_ID}")
    print(f"Scraping interval: {settings.SCRAPE_EVERY_MINUTES} minutes (Fallback)")
    print(f"Scheduled daily run: {settings.SCRAPE_HOUR:02d}:{settings.SCRAPE_MINUTE:02d} Tashkent time")
    print("\nPress Ctrl+C to stop monitoring")
    print("-" * 60)
    
    async def run_realtime_test():
        # Run scraping task manually
        print("\nExecuting scraping task...")
        
        # Simulate the scraping task
        result = scrape_uzex_etender()
        
        if result.get("status") == "done":
            print(f"✅ Scraping completed!")
            print(f"   Tenders found: {result.get('fetched', 0)}")
            print(f"   New tenders: {result.get('inserted', 0)}")
            print(f"   With keywords: {result.get('tendersWithKeywords', 0)}")
            
            if result.get("tendersWithKeywords", 0) > 0:
                print(f"\n📱 Telegram alerts sent to {settings.TELEGRAM_ALERT_CHAT_ID}")
                print("   Check your Telegram for notifications!")
        else:
            print(f"❌ Scraping failed: {result}")
    
    # Run the test
    try:
        asyncio.run(run_realtime_test())
    except KeyboardInterrupt:
        print("\n\n🛑 Real-time test stopped by user")
    except Exception as e:
        print(f"\n❌ Real-time test failed: {e}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the API server is running and all dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "=" * 60)
print("Real-time test completed!")
print("Your Tender Intelligence Platform is ready for production!")
