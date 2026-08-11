import asyncio
import sys
import os

# Ensure backend_py is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telegram_alerts import TelegramAlertService
from app.models.tender import Tender, Keyword

async def main():
    print("Testing Telegram Alerts...")
    service = TelegramAlertService()
    
    # Create a mock tender (UZEX style)
    tender_uzex = Tender(
        source="https://etender.uzex.uz/",
        external_id="123456",
        title="Тестовый тендер (UZEX) с <кавычками> и «ёлочками»",
        organizer_name="OOO 'Test Organizer'",
        organizer_inn="123456789",
        amount="1 500 000.00",
        region="Tashkent",
        url="https://etender.uzex.uz/lot/123456"
    )
    
    # Create a mock tender (E-Auksion style)
    tender_auksion = Tender(
        source="https://e-auksion.uz",
        external_id="987654",
        title="Тестовый лот (E-Auksion) для проверки",
        organizer_name=None,
        organizer_inn=None,
        amount="9 999 999.00 UZS",
        region="Samarkand",
        url="https://e-auksion.uz/lot-view?lot_id=987654"
    )
    
    # Mock keywords
    kw1 = Keyword(phrase="test")
    kw2 = Keyword(phrase="check")
    
    print("Sending UZEX alert...")
    await service.send_tender_alert(tender_uzex, [kw1])
    
    print("Sending E-Auksion alert...")
    await service.send_tender_alert(tender_auksion, [kw2])
    
    print("Test completed!")

if __name__ == '__main__':
    asyncio.run(main())
