from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from app.scrapers.base import BaseScraper, ScraperOptions
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

@dataclass
class TenderMcItem:
    external_id: str
    title: str
    amount: str
    region: str
    url: str
    organizer_name: str | None = None
    source: str = "TENDER_MC"

class TenderMcScraper(BaseScraper):
    """
    Scraper for tender.mc.uz (Ministry of Construction Tenders)
    """
    
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        super().__init__(opts)
        self.base_url = "https://tender.mc.uz"
        self.search_url = f"{self.base_url}/tender-list"
        self.rate = RateLimiter(min_interval_ms=2500)

    async def scrape_tenders(self) -> List[TenderMcItem]:
        """Scrape the tender list from Ministry of Construction"""
        await self.init()
        tenders = []
        try:
            logger.info(f"Navigating to {self.search_url}")
            await self.page.goto(self.search_url, wait_until="networkidle", timeout=60000)
                # Dismiss initial modal if present
            modal_btn = await self.page.query_selector("button:has-text('Yopish'), .btn:has-text('Yopish')")
            if modal_btn:
                await modal_btn.click()
                await self.page.wait_for_timeout(1000)
            
            if await self.detect_captcha("TENDER_MC"):
                return []
            
            # Wait for real content to load (bypass skeleton overlays)
            logger.info("Waiting for actual tender list to load (bypassing skeleton)...")
            await self.page.wait_for_function("""() => {
                const items = document.querySelectorAll('.tender-item, a.tender-item');
                if (items.length === 0) return false;
                return Array.from(items).some(item => (item.innerText || '').includes('№'));
            }""", timeout=30000)
            
            # Extract items using robust JS evaluation
            items_data = await self.page.evaluate('''() => {
                const items = document.querySelectorAll('.tender-item');
                return Array.from(items).slice(0, 10).map(item => {
                    const text = item.innerText || '';
                    
                    // Extract ID using Regex
                    const idMatch = text.match(/№\\s*(\\d+)/);
                    const external_id = idMatch ? idMatch[1] : 'unknown';
                    
                    // Extract Title (usually in a div next to 'Tender nomi')
                    let title = 'Unknown';
                    const titleLabel = Array.from(item.querySelectorAll('div')).find(el => el.innerText && el.innerText.trim() === 'Tender nomi');
                    if (titleLabel && titleLabel.nextElementSibling) {
                        title = titleLabel.nextElementSibling.innerText.trim();
                    }
                    
                    // Extract Organizer (usually in a div next to 'Buyurtmachi')
                    let organizer_name = null;
                    const organizerLabel = Array.from(item.querySelectorAll('div')).find(el => el.innerText && el.innerText.trim() === 'Buyurtmachi');
                    if (organizerLabel && organizerLabel.nextElementSibling) {
                        organizer_name = organizerLabel.nextElementSibling.innerText.trim();
                    }
                    
                    // Extract Region (usually in a div next to 'Hudud')
                    let region = 'Uzbekistan';
                    const regionLabel = Array.from(item.querySelectorAll('div')).find(el => el.innerText && el.innerText.trim() === 'Hudud');
                    if (regionLabel && regionLabel.nextElementSibling) {
                        region = regionLabel.nextElementSibling.innerText.trim();
                    }
                    
                    // Extract Price (find the Boshlang'ich narx block)
                    let amount = '0';
                    const priceLabel = Array.from(item.querySelectorAll('div')).find(el => el.innerText && el.innerText.includes('Boshlang'));
                    if (priceLabel && priceLabel.nextElementSibling) {
                        amount = priceLabel.nextElementSibling.innerText.trim();
                    } else {
                        // Fallback Regex
                        const priceMatch = text.match(/QQS\\s*bilan\\)?\\s*\\n+([\\d\\s]+)/i);
                        if (priceMatch) amount = priceMatch[1].trim();
                    }
                    
                    // Extract Url
                    const url = item.href || '';
                    
                    return { external_id, title, amount, region, url, organizer_name };
                });
            }''')
            
            logger.info(f"Extracted {len(items_data)} items from JS evaluation")
            
            for data in items_data:
                try:
                    tenders.append(TenderMcItem(
                        external_id=data['external_id'],
                        title=data['title'],
                        amount=data['amount'],
                        region=data['region'] or "Uzbekistan",
                        url=data['url'] or f"{self.base_url}/tender/{data['external_id']}",
                        organizer_name=data['organizer_name']
                    ))
                except Exception as e:
                    logger.error(f"Error parsing item on Tender MC: {e}")
            
            # Rate limiting after list processing
            await self.random_delay(2.5, 5.0)
            
            return tenders
        finally:
            await self.close()

    async def run(self) -> List[TenderMcItem]:
        return await self.scrape_tenders()
