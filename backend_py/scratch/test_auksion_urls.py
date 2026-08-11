import asyncio
import sys
import io
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_url(url, name):
    print(f"\n--- Testing {name}: {url} ---")
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1366, "height": 768}, locale="ru-RU")
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        response = await page.goto(url, wait_until="load", timeout=60000)
        print(f"Response Status: {response.status if response else 'No Response'}")
        
        await page.wait_for_timeout(10000)
        
        # Save screenshot
        screenshot_path = f"scratch/{name}.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        body_text = await page.inner_text("body")
        print(f"Body text length: {len(body_text)}")
        print(f"Body text sample:\n{body_text[:300]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

async def main():
    # Test without language prefix
    await test_url("https://e-auksion.uz/lots", "e_auksion_lots_direct")
    # Test with /uz/lots
    await test_url("https://e-auksion.uz/uz/lots", "e_auksion_lots_uz")

if __name__ == "__main__":
    asyncio.run(main())
