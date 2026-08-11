import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    url = "https://tender.mc.uz/tender-list"
    print(f"Connecting to: {url}")
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True, args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox"
    ])
    context = await browser.new_context(viewport={"width": 1366, "height": 768})
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Take a screenshot to see what it looks like
        await page.screenshot(path="scratch/tender_mc.png", full_page=True)
        
        print("Saved screenshot")
        
        # Extract items using JS to bypass encoding issues
        items_data = await page.evaluate('''() => {
            const items = document.querySelectorAll('.tender-item');
            return Array.from(items).map(item => {
                return {
                    id: item.querySelector('.tender-id')?.innerText || '',
                    html: item.innerHTML.substring(0, 500)
                };
            });
        }''')
        
        import json
        with open("scratch/tender_mc_dump.json", "w", encoding="utf-8") as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)
            
        print("Saved dump")
        
    except Exception as e:
        print("Error:", e)
    finally:
        await browser.close()
        await pw.stop()

if __name__ == '__main__':
    asyncio.run(main())
