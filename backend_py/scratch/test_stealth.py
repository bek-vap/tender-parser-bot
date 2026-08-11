import asyncio
from app.scrapers.base import BaseScraper, ScraperOptions
from playwright_stealth import Stealth

async def test_stealth():
    scraper = BaseScraper(ScraperOptions(headless=True))
    await scraper.init()
    try:
        url = "https://bot.sannysoft.com/"
        print(f"Navigating to {url}...")
        await scraper.page.goto(url, wait_until="networkidle")
        
        webdriver = await scraper.page.evaluate("() => navigator.webdriver")
        print(f"navigator.webdriver: {webdriver}")
        
        screenshot_path = "stealth_test.png"
        await scraper.page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        if webdriver is False:
            print("OK: Stealth mode is working! navigator.webdriver is False.")
        else:
            print("FAIL: Stealth mode FAILED! navigator.webdriver is True.")
            
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_stealth())
