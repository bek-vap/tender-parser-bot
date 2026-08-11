import asyncio
import sys
import io
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_e_auksion_home():
    url = "https://e-auksion.uz/"
    print(f"Testing E-Auksion Home: {url}")
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
    )
    context = await browser.new_context(viewport={"width": 1366, "height": 768}, locale="ru-RU")
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    # Listen to requests/responses
    page.on("request", lambda req: print(f"-> Request: {req.method} {req.url}"))
    page.on("response", lambda res: print(f"<- Response: {res.status} {res.url}"))
    page.on("console", lambda msg: print(f"[Console] {msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"[PageError] {err}"))
    
    try:
        response = await page.goto(url, wait_until="load", timeout=60000)
        print(f"Response Status: {response.status if response else 'No Response'}")
        
        # Wait 10 seconds for content to load
        await page.wait_for_timeout(10000)
        
        # Save screenshot
        screenshot_path = "scratch/e_auksion_home.png"
        await page.screenshot(path=screenshot_path)
        print(f"Home Screenshot saved to {screenshot_path}")
        
        body_text = await page.inner_text("body")
        print(f"Body text length: {len(body_text)}")
        print(f"Body text sample:\n{body_text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(test_e_auksion_home())
