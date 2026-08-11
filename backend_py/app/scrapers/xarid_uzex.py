from __future__ import annotations
import logging
import httpx
from dataclasses import dataclass
from typing import List, Dict, Any

from app.scrapers.base import BaseScraper, ScraperOptions
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

@dataclass
class XaridTender:
    external_id: str
    title: str
    amount: str
    region: str
    url: str
    organizer_name: str | None = None
    organizer_inn: str | None = None
    organizer_phone: str | None = None
    organizer_email: str | None = None
    source: str = "XARID_UZEX"

class XaridUzexScraper(BaseScraper):
    """
    Scraper for xarid.uzex.uz (State Procurement Portal)
    """
    
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        super().__init__(opts)
        self.base_url = "https://new-xarid.uzex.uz"
        self.api_url = "https://xarid-api-purchase.uzex.uz/Common/GetDirectPurchases"
        self.rate = RateLimiter(min_interval_ms=1000)

    async def scrape_tenders(self) -> List[XaridTender]:
        """Scrape direct purchase list from Xarid Uzex API"""
        logger.info(f"Fetching direct purchases from Xarid API: {self.api_url}")
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "language": "uz",
            "referer": "https://new-xarid.uzex.uz/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        payload = {
            "region_ids": [],
            "Is_On_Discussion": 0,
            "from": 1,
            "to": 50 # Increase to 50 items for 100% coverage
        }
        
        tenders = []
        try:
            # Use httpx.AsyncClient to make a direct POST call (asynchronous)
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self.api_url, headers=headers, json=payload)
            if resp.status_code == 200:
                items = resp.json()
                logger.info(f"Xarid API returned {len(items)} direct purchases")
                
                for item in items:
                    try:
                        ext_id = str(item.get("display_id") or item.get("id"))
                        category = item.get("category_name") or "Без категории"
                        contract_num = item.get("contract_num") or "Б/Н"
                        title = f"{category} (Прямой договор №{contract_num})"
                        
                        amount_val = item.get("contract_sum")
                        currency = item.get("currency_name") or "UZS"
                        amount = f"{float(amount_val):,.2f} {currency}" if amount_val is not None else "0 UZS"
                        
                        tenders.append(XaridTender(
                            external_id=ext_id,
                            title=title,
                            amount=amount,
                            region="Uzbekistan",
                            url=f"https://new-xarid.uzex.uz/detail/direct-purchase/{ext_id}",
                            organizer_name=item.get("customer_name"),
                            organizer_inn=str(item.get("customer_inn")) if item.get("customer_inn") else None
                        ))
                    except Exception as e:
                        logger.error(f"Error parsing direct purchase item: {e}")
            else:
                logger.error(f"Xarid API returned status code {resp.status_code}: {resp.text}")
                
            return tenders
        except Exception as e:
            logger.error(f"Error calling Xarid API: {e}")
            return []

    async def run(self) -> List[XaridTender]:
        return await self.scrape_tenders()
