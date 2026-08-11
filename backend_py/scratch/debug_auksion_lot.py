import asyncio
import sys
import io
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    url = "https://e-auksion.uz/lot-view?lot_id=23686628"
    print(f"Fetching: {url}")
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
    
    try:
        try:
            # Using wait_until="load" and shorter timeout of 25 seconds
            await page.goto(url, wait_until="load", timeout=25000)
        except Exception as ge:
            print(f"Navigation timed out/failed (continuing anyway): {ge}")
            
        # Wait extra time for SPA content to load
        await page.wait_for_timeout(10000)
        
        # Save screenshot
        screenshot_path = "scratch/e_auksion_lot_23686628.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Save HTML
        html = await page.content()
        with open("scratch/e_auksion_lot_23686628.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML saved to scratch/e_auksion_lot_23686628.html")
        
        # Check all paragraphs and labels to find where organizer and region are
        texts = await page.evaluate("""
            () => {
                const results = [];
                // Find all elements containing text
                const elements = document.querySelectorAll('p, span, div, label, h1, h2, h3, h4, h5, h6, td, th');
                for (const el of elements) {
                    const text = el.textContent ? el.textContent.trim() : '';
                    if (text.length > 0 && text.length < 200 && !el.children.length) {
                        results.push({
                            tag: el.tagName,
                            class: el.className,
                            text: text
                        });
                    }
                }
                return results;
            }
        """)
        import json
        with open("scratch/e_auksion_lot_23686628_elements.json", "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
        print("Wrote elements to scratch/e_auksion_lot_23686628_elements.json")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
