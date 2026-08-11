import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    url = "https://e-auksion.uz/lot-view?lot_id=23686628"
    print(f"Opening browser for URL: {url}")
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True, args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ])
    context = await browser.new_context(viewport={"width": 1366, "height": 768}, locale="uz-UZ")
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        # Wait a bit more for dynamic content
        await page.wait_for_timeout(5000)
        
        # Take a screenshot
        screenshot_path = "scratch/detail_page.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save HTML
        html = await page.content()
        with open("scratch/detail_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML saved to scratch/detail_page.html")
        
        # Print some interesting info
        title_el = await page.query_selector('.lot-title, .title, h1, .text-h6')
        if title_el:
            print("Found title element. Text:", await title_el.inner_text())
        else:
            print("No title element found via primary selectors.")
            
        silver_els = await page.query_selector_all(".text-silver2")
        print(f"Found {len(silver_els)} text-silver2 elements.")
        for el in silver_els[:10]:
            txt = await el.inner_text()
            print(" - silver text:", txt)
            
    finally:
        await browser.close()
        await pw.stop()

if __name__ == '__main__':
    asyncio.run(main())
