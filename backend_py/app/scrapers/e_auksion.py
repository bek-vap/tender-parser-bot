from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Dict, Any
import re

from app.scrapers.base import BaseScraper, ScraperOptions
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

@dataclass
class EAuksionItem:
    external_id: str
    title: str
    amount: str
    region: str
    url: str
    organizer_name: str | None = None
    organizer_phone: str | None = None
    source: str = "E_AUKSION"

class EAuksionScraper(BaseScraper):
    """
    Scraper for e-auksion.uz (Investment and Auction lots)
    """
    
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        super().__init__(opts)
        self.base_url = "https://e-auksion.uz"
        self.search_url = f"{self.base_url}/lots"
        self.rate = RateLimiter(min_interval_ms=3000)

    async def scrape_lots(self) -> List[EAuksionItem]:
        """Scrape investment lots from E-Auksion"""
        await self.init()
        lots = []
        try:
            logger.info(f"Navigating to {self.search_url}")
            await self.page.goto(self.search_url, wait_until="networkidle", timeout=60000)
            
            if await self.detect_captcha("E_AUKSION"):
                return []
            
            # Wait for lots container (prefer .lot-card, fallback to .q-card)
            await self.page.wait_for_selector("a[href*='lot-view']", timeout=20000, state="attached")

            items = await self.page.query_selector_all("a[href*='lot-view']")
            if not items:
                logger.warning("No lot-view items found, falling back to generic selectors.")
                items = await self.page.query_selector_all(".lot-card, .q-card")
                
            # Extract URLs and deduplicate
            unique_urls = []
            for item in items:
                link = await item.get_attribute("href")
                if not link:
                    continue
                full_url = f"{self.base_url}{link}" if link.startswith("/") else link
                if full_url not in unique_urls:
                    unique_urls.append(full_url)
                    
            logger.info(f"Found {len(unique_urls)} unique lot URLs on e-auksion.uz")

            for full_url in unique_urls[:10]:
                try:
                    match = re.search(r"lot[_-]?id=([0-9]+)", full_url)
                    ext_id = match.group(1) if match else "unknown"

                    # Open detail page for reliable extraction
                    detail_page = await self.context.new_page()
                    await self.block_resources(detail_page)
                    from playwright_stealth import Stealth
                    await Stealth().apply_stealth_async(detail_page)
                    
                    title = ext_id
                    amount = "0"
                    region = "Uzbekistan"
                    organizer_name = None
                    organizer_phone = None
                    
                    try:
                        await detail_page.goto(full_url, wait_until="networkidle", timeout=60000)
                        # Extra wait for Vue SPA to fully render
                        await detail_page.wait_for_timeout(2000)

                        # ── Title ──────────────────────────────────────────────────
                        # The title is in the og/meta description tag as:
                        # "Mulk ma'lumotlari || «Company Name» MChJ"
                        title = await detail_page.evaluate("""
                            () => {
                                const meta = document.querySelector(
                                    'meta[data-vmid="ac:description"], meta[name="description"]'
                                );
                                if (meta) {
                                    const content = meta.getAttribute('content') || '';
                                    const parts = content.split('||');
                                    if (parts.length > 1) return parts[1].trim();
                                    if (content.trim()) return content.trim();
                                }
                                // Fallback: look for lot card title area
                                const titleEl = document.querySelector(
                                    '.lot-card-name, .lot-name, h1.lot-title, ' +
                                    '.lot-card-basic-inf h3, .lot-card-basic-inf h4'
                                );
                                return titleEl ? titleEl.textContent.trim() : '';
                            }
                        """) or ext_id

                        # ── Universal attribute extractor ──────────────────────────
                        # Two strategies:
                        #  1. Classic lot-card layout (.lot-card-attribute-title-div > p/label → col > .lot-card-attribute-value)
                        #  2. Table layout (td[short text label] → next td value)
                        async def get_attribute_by_label(keywords: list) -> str:
                            """Find value by scanning lot-card labels or table attribute titles."""
                            kw_js = ", ".join(f'"{k}"' for k in keywords)
                            return await detail_page.evaluate(f"""
                                () => {{
                                    const keywords = [{kw_js}];

                                    // Strategy 1: Classic lot card (.lot-card-attribute-title-div p/label)
                                    const classicLabels = document.querySelectorAll(
                                        '.lot-card-attribute-title-div p, .lot-card-attribute-title-div label'
                                    );
                                    for (const label of classicLabels) {{
                                        const text = label.textContent.trim().toLowerCase();
                                        if (keywords.some(k => text.includes(k.toLowerCase()))) {{
                                            const col = label.closest('[class*="col-"]');
                                            if (col) {{
                                                const valueDiv = col.querySelector('.lot-card-attribute-value');
                                                if (valueDiv) {{
                                                    // Get direct text nodes only (skip .sale strikethrough etc.)
                                                    const direct = Array.from(valueDiv.childNodes)
                                                        .filter(n => n.nodeType === 3)
                                                        .map(n => n.textContent.trim())
                                                        .join(' ').trim();
                                                    if (direct) return direct;
                                                    // Fallback: clone and remove .sale
                                                    const clone = valueDiv.cloneNode(true);
                                                    const saleEl = clone.querySelector('.sale');
                                                    if (saleEl) saleEl.remove();
                                                    return clone.textContent.trim();
                                                }}
                                            }}
                                        }}
                                    }}

                                    // Strategy 2: Table layout (td label → sibling td value)
                                    const tds = document.querySelectorAll('td');
                                    for (const td of tds) {{
                                        const text = td.textContent.trim();
                                        // Skip table rows containing "majburiyat" (obligations) to avoid wrong organizer matching
                                        if (text.toLowerCase().includes('majburiyat')) continue;
                                        // Only consider short-text td cells (labels, not data blocks)
                                        if (text.length > 0 && text.length < 150 &&
                                            keywords.some(k => text.toLowerCase().includes(k.toLowerCase()))) {{
                                            const next = td.nextElementSibling;
                                            if (next && next.tagName === 'TD') {{
                                                const val = next.textContent.trim();
                                                if (val && val.length < 500) return val;
                                            }}
                                        }}
                                    }}

                                    return '';
                                }}
                            """) or ""

                        # ── Amount ─────────────────────────────────────────────────
                        amount = await get_attribute_by_label([
                            "boshlang'ich narxi", "boshlang", "narxi", "start price",
                            "initial price", "начальная цена", "цена"
                        ])
                        if not amount:
                            amount = await detail_page.evaluate("""
                                () => {
                                    const el = document.querySelector('.lot-card-attribute-value');
                                    if (el) {
                                        const direct = Array.from(el.childNodes)
                                            .filter(n => n.nodeType === 3)
                                            .map(n => n.textContent.trim()).join(' ').trim();
                                        return direct || el.textContent.trim();
                                    }
                                    return '';
                                }
                            """) or "0"

                        # ── Region ─────────────────────────────────────────────────
                        # "Viloyat" label in the "Mulk ma'lumotlari" table section
                        region = await get_attribute_by_label([
                            "viloyat", "hudud", "region", "location", "joylashuv"
                        ])
                        if not region:
                            region = await detail_page.evaluate("""
                                () => {
                                    const el = document.querySelector('.lot-card-location, .location-text');
                                    return el ? el.textContent.trim() : '';
                                }
                            """) or "Uzbekistan"

                        # ── Organizer ──────────────────────────────────────────────
                        # "Buyurtmachi nomi" label in the Buyurtmachi ma'lumotlari table
                        organizer_name = await get_attribute_by_label([
                            "buyurtmachi nomi", "tashkilotchi", "organizer", "организатор",
                            "sotuvchi", "seller", "egasi"
                        ])
                        organizer_phone = await get_attribute_by_label([
                            "telefon", "phone", "контактный телефон", "aloqa"
                        ])
                    finally:
                        await detail_page.close()

                    # Ensure amount is not empty
                    if not amount or amount.strip() == "0":
                        # As final fallback, keep amount as "0" but log
                        logger.warning(f"Amount still missing or zero for lot {ext_id}")

                    lots.append(EAuksionItem(
                        external_id=ext_id,
                        title=title.strip(),
                        amount=amount.strip(),
                        region=region.strip(),
                        url=full_url,
                        organizer_name=organizer_name.strip(" '\"`‘“’”)").strip() if organizer_name else None,
                        organizer_phone=organizer_phone.strip() if organizer_phone else None,
                    ))
                    # Small random delay to mimic human interaction
                    await self.random_delay(0.5, 1.5)
                except Exception as e:
                    logger.error(f"Error parsing item on E-Auksion: {e}")
            
            # Substantial delay after scraping a page
            await self.random_delay(3.0, 6.0)
            
            return lots
        finally:
            await self.close()

    async def run(self) -> List[EAuksionItem]:
        return await self.scrape_lots()
