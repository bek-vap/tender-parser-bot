import asyncio
import sys
import io
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_e_auksion():
    url = "https://e-auksion.uz/lots"
    print(f"Testing E-Auksion: {url}")
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
    
    # Listen to console messages and page errors
    page.on("console", lambda msg: print(f"[E-Auksion Console] {msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"[E-Auksion PageError] {err}"))
    
    try:
        response = await page.goto(url, wait_until="load", timeout=60000)
        print(f"Response Status: {response.status if response else 'No Response'}")
        
        # Wait 15 seconds for SPA content to render
        await page.wait_for_timeout(15000)
        
        # Save screenshot
        screenshot_path = "scratch/e_auksion_loaded.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save HTML content
        html_content = await page.content()
        with open("scratch/e_auksion_loaded.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        body_text = await page.inner_text("body")
        print(f"Body text length: {len(body_text)}")
        print(f"Body text sample (first 500 chars):\n{body_text[:500]}")
        
    except Exception as e:
        print(f"Error testing E-Auksion: {e}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

async def test_tender_mc():
    # Test /tender-list instead of /tenders
    url = "https://tender.mc.uz/tender-list"
    print(f"\nTesting Tender MC (tender-list): {url}")
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
    
    # Listen to console messages and page errors
    page.on("console", lambda msg: print(f"[TenderMC Console] {msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"[TenderMC PageError] {err}"))
    
    try:
        response = await page.goto(url, wait_until="load", timeout=60000)
        print(f"Response Status: {response.status if response else 'No Response'}")
        
        # Wait 10 seconds for SPA content to load
        await page.wait_for_timeout(10000)
        
        # Check if there is a modal with "Yopish" button and click it to clear overlays
        try:
            # Let's search for "Yopish" button
            yopish_btn = await page.query_selector("button:has-text('Yopish'), .btn:has-text('Yopish')")
            if yopish_btn:
                print("Found 'Yopish' modal button! Clicking it...")
                await yopish_btn.click()
                await page.wait_for_timeout(2000)
        except Exception as modal_err:
            print(f"No modal clicked: {modal_err}")
            
        # Save screenshot
        screenshot_path = "scratch/tender_mc_loaded.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save HTML content
        html_content = await page.content()
        with open("scratch/tender_mc_loaded.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Check classes of page elements
        classes = await page.evaluate("""() => {
            const allEls = document.querySelectorAll('*');
            const classSet = new Set();
            allEls.forEach(el => {
                if (el.className && typeof el.className === 'string') {
                    el.className.split(/\\s+/).forEach(c => classSet.add(c));
                }
            });
            return Array.from(classSet).slice(0, 100);
        }""")
        print("CSS classes found on tender-list page:")
        print(classes)
        
        body_text = await page.inner_text("body")
        print(f"Body text length: {len(body_text)}")
        print(f"Body text sample (first 1000 chars):\n{body_text[:1000]}")
        
    except Exception as e:
        print(f"Error testing Tender MC: {e}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

async def main():
    await test_e_auksion()
    await test_tender_mc()

if __name__ == "__main__":
    asyncio.run(main())
