from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from app.scrapers.base import BaseScraper, ScraperOptions

logger = logging.getLogger(__name__)

class UzexLotScraper(BaseScraper):
    """
    Scraper for detailed lot information from etender.uzex.uz
    """
    
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        super().__init__(opts)
        self.base_url = "https://etender.uzex.uz"

    async def scrape_lot_details(self, lot_id: str) -> Dict[str, Any]:
        """
        Scrapes detailed information for a specific lot from etender.uzex.uz
        """
        await self.init()
        url = f"{self.base_url}/lot/{lot_id}"
        data = {
            "id": lot_id,
            "url": url,
            "languages": None,
            "extra_info": None,
            "phone": None,
            "delivery_time": None,
            "payment_terms": None,
            "title": None,
            "organizer": None,
            "amount": None,
            "organizer_inn": None,
            "organizer_address": None
        }
        
        try:
            logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for any relevant content
            await self.page.wait_for_selector(".lot-details, .content, body", timeout=15000)
            
            # Click "Lot haqida ma'lumot" tab to ensure data is visible
            try:
                tab_selector = "text=Lot haqida ma'lumot"
                tab = self.page.locator(tab_selector).first
                if await tab.count() > 0:
                    await tab.click()
                    await self.page.wait_for_timeout(2000)
            except Exception:
                pass  # Tab might already be active or page structure different
            
            # Extract content using improved JS matching based on real UZEX HTML structure
            # The page uses Bootstrap grid: div.row > [div.col-md-6 (label), div.col-md-6 (value)]
            extracted = await self.page.evaluate("""() => {
                const results = {};
                
                // Helper to find an element containing specific text
                function findElementByText(textOptions) {
                    const allEls = document.querySelectorAll('p, span, div, strong, h6, th, td');
                    for (const el of allEls) {
                        const text = el.innerText ? el.innerText.trim().toLowerCase() : '';
                        for (const opt of textOptions) {
                            if (text === opt.toLowerCase() || text === opt.toLowerCase() + ':') {
                                return el;
                            }
                        }
                    }
                    return null;
                }
                
                // Helper to extract value given a label element
                function extractValue(labelEl) {
                    if (!labelEl) return null;
                    
                    // 1. Check if the value is in the next sibling of the label itself
                    let nextSib = labelEl.nextElementSibling;
                    if (nextSib && nextSib.innerText && nextSib.innerText.trim() !== '') {
                        return nextSib.innerText.trim();
                    }
                    
                    // 2. Check if the label is inside a column, and the value is in the next column
                    // e.g. <div class="col-md-5"><p>Label</p></div> <div class="col-md-7"><p>Value</p></div>
                    let parent = labelEl.parentElement;
                    if (parent) {
                        let parentNext = parent.nextElementSibling;
                        if (parentNext && parentNext.innerText && parentNext.innerText.trim() !== '') {
                             return parentNext.innerText.trim();
                        }
                    }
                    
                    return null;
                }
                
                function getValue(textOptions) {
                    const el = findElementByText(textOptions);
                    return extractValue(el);
                }
                
                results.organizer = getValue(["buyurtmachi nomi", "наименование заказчика", "заказчик"]);
                results.organizer_inn = getValue(["buyurtmachi stiri", "stir", "инн заказчика", "инн"]);
                results.organizer_address = getValue(["buyurtmachi manzili", "yetkazib berish manzili", "адрес заказчика", "адрес доставки"]);
                results.phone = getValue(["aloqa raqami", "контактный номер", "телефон", "telefonlar"]);
                results.payment_terms = getValue(["to'lov tartibi", "условия оплаты", "to'lov shartlari"]);
                results.languages = getValue(["belgilangan tillar", "язык", "тиллар"]);
                results.status = getValue(["holat", "статус"]);
                results.registration_order = getValue(["rasmiylashtirish tartibi", "порядок оформления"]);
                results.placement_deadline = getValue(["joylashtirish muddati", "срок размещения"]);
                results.delivery_time = getValue(["yetkazib berish muddati", "срок поставки"]);
                results.deposit = getValue(["zakalat miqdori", "размер залога"]);
                results.extra_info = getValue(["texnik tavsif", "qo'shimcha ma'lumotlar", "дополнительная информация", "qo'shimcha maʼlumotlar"]);
                results.opening_date = getValue(["ochilish sanasi", "дата открытия"]);
                
                // Amount - try from the top header area first
                const amountEl = document.querySelector('.lot-price, [class*="price"]');
                if (amountEl) {
                    results.amount = amountEl.innerText.trim();
                }
                if (!results.amount) {
                    results.amount = getValue(["jami boshlang'ich narx", "общая стартовая стоимость", "начальная цена"]);
                }
                
                // Title
                results.title = getValue(["batafsil ma'lumot", "подробное описание", "название лота", "batafsil maʼlumot"]);
                if (!results.title) {
                    const h3 = document.querySelector('h3.lot-name, .lot-title, h3');
                    if (h3) results.title = h3.innerText.trim();
                }
                
                return results;
            }""")
            
            data.update(extracted)
            return data
            
        except Exception as e:
            logger.error(f"Error scraping lot details for {lot_id}: {e}")
            return data
        finally:
            await self.close()

    async def run(self, lot_id: str) -> Dict[str, Any]:
        return await self.scrape_lot_details(lot_id)
