import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telegram_alerts import TelegramAlertService
from app.models.tender import Tender, Keyword

async def test_alert():
    print("Starting Telegram Alert Test...")
    alert_service = TelegramAlertService()
    
    # Create a mock tender object with organizer info
    mock_tender = Tender(
        id="test-123",
        external_id="481569",
        title="Engineering services for selecting best offers",
        source="ETENDER.UZEX.UZ",
        amount="14500000000",
        region="Sirdaryo",
        url="https://etender.uzex.uz/lot/481569",
        description="Engineering services for selecting best offers for Sirdaryo Prosecutor Office.",
        organizer_phone="+998-75-552-40-22",
        organizer_email="competition@sgcc.uz"
    )
    
    # Create mock keywords
    mock_keywords = [
        Keyword(phrase="greenhouse"),
        Keyword(phrase="construction")
    ]
    
    try:
        await alert_service.send_tender_alert(mock_tender, mock_keywords)
        print("Success: Test alert sent successfully! Check your Telegram channel.")
    except Exception as e:
        print(f"Error: Failed to send test alert: {e}")
    finally:
        await alert_service.close()

if __name__ == "__main__":
    asyncio.run(test_alert())
