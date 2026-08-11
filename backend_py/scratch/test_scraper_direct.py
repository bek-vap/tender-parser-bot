"""Debug: dump all elements from the lot page to understand structure"""
import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def debug_scraper():
    lot_id = "484088"
    url = f"https://etender.uzex.uz/lot/{lot_id}"
    
    print(f"Debugging lot page: {url}")
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1366, "height": 768}, locale="uz-UZ")
    page = await context.new_page()
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Try clicking the tab
        try:
            tabs = await page.query_selector_all("a, button")
            for t in tabs:
                txt = (await t.inner_text()).strip()
                if "lot haqida" in txt.lower():
                    await t.click()
                    await page.wait_for_timeout(2000)
                    print(f"Clicked tab: {txt}")
                    break
        except Exception as e:
            print(f"Tab click error: {e}")
        
        # Extract all key-value pairs
        debug_data = await page.evaluate("""() => {
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
            
            return { extracted: results };
        }""")
        
        # Save to JSON file to avoid encoding issues
        with open("scratch/debug_output.json", "w", encoding="utf-8") as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved debug data to scratch/debug_output.json")
        print(f"Found {len(debug_data.get('colonElements', []))} colon elements")
        print(f"Found {len(debug_data.get('tabPanes', []))} tab panes")
        
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(debug_scraper())
