import asyncio
import sys, os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def test_e_auksion_parsing():
    url = "https://e-auksion.uz/lots"
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"])
    context = await browser.new_context(viewport={"width": 1366, "height": 768}, locale="uz-UZ")
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    await page.goto(url, wait_until="networkidle", timeout=60000)
    # wait for SPA content
    await page.wait_for_timeout(15000)
    # count lot cards using possible selectors
    selectors = [".lot-card", ".q-card", ".lot-item", ".item", "a[href*='lot-view']"]
    for sel in selectors:
        count = await page.eval_on_selector_all(sel, "els => els.length")
        print(f"Selector {sel}: {count} elements")
        # Get the first lot-view element
        lot_view_el = await page.query_selector("a[href*='lot-view']")
        if lot_view_el:
            # Try to extract possible title from this element
            title_el = await lot_view_el.query_selector('.lot-title')
            if title_el:
                title_text = await title_el.inner_text()
                print(f"Title found via .lot-title: {title_text}")
            else:
                # fallback selectors
                found = False
                for sel in ['.title', 'h4', '.text-h6', '.q-item__section--main .text-h6']:
                    el = await lot_view_el.query_selector(sel)
                    if el:
                        txt = await el.inner_text()
                        print(f"Title found via {sel}: {txt}")
                        found = True
                        break
                if not found:
                    print("No title element found inside lot-view.")
            # Dump HTML snippet for reference
            inner_text = await lot_view_el.inner_text()
            print(f"Lot-view inner text snippet:\n{inner_text[:500]}")
            print(f"Lot-view element HTML snippet:\n{html[:500]}")
        else:
            print("No lot-view element found for HTML dump.")
    await browser.close()
    await pw.stop()

asyncio.run(test_e_auksion_parsing())
