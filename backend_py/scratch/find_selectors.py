import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    url = "https://e-auksion.uz/lot-view?lot_id=23686628"
    print(f"Connecting to: {url}")
    
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
        await page.wait_for_timeout(3000)
        
        # Try to find the title using multiple approaches
        print("\n=== TITLE SEARCH ===")
        title_selectors = [
            '.lot-card-title', '.lot-title', '.card-title', 
            '.lot-name', '.lot-card-name', 'h1', 'h2', 'h3',
            '.text-h5', '.text-h6', '.text-h4',
            '.lot-card-basic-inf h1', '.lot-card-basic-inf h2',
            '.lot-card-basic-inf h3',
            '[class*="title"]',
        ]
        for sel in title_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    txt = (await el.inner_text()).strip()[:100]
                    cls = await el.get_attribute('class')
                    print(f"  FOUND '{sel}': class='{cls}' text='{txt}'")
            except:
                pass

        print("\n=== PRICE SEARCH ===")
        # Look for the price text
        price_text = await page.evaluate("""
            () => {
                // Find elements containing Boshlang'ich narxi
                const all = document.querySelectorAll('*');
                const results = [];
                for (const el of all) {
                    if (el.children.length === 0 && el.textContent.includes("Boshlang")) {
                        results.push({
                            tag: el.tagName,
                            class: el.className,
                            text: el.textContent.trim().substring(0, 100),
                            parentClass: el.parentElement ? el.parentElement.className : ''
                        });
                        if (results.length >= 5) break;
                    }
                }
                return results;
            }
        """)
        for r in price_text:
            print(f"  Tag={r['tag']}, class='{r['class']}', parentClass='{r['parentClass']}', text='{r['text']}'")

        print("\n=== PRICE VALUE SEARCH ===")
        price_val = await page.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                const results = [];
                for (const el of all) {
                    if (el.children.length === 0 && (
                        el.textContent.includes("1 089") || 
                        el.textContent.includes("UZS") ||
                        el.textContent.includes("сум")
                    )) {
                        results.push({
                            tag: el.tagName,
                            class: el.className,
                            text: el.textContent.trim().substring(0, 100),
                            parentClass: el.parentElement ? el.parentElement.className : ''
                        });
                        if (results.length >= 5) break;
                    }
                }
                return results;
            }
        """)
        for r in price_val:
            print(f"  Tag={r['tag']}, class='{r['class']}', parentClass='{r['parentClass']}', text='{r['text']}'")
        
        print("\n=== TITLE TEXT SEARCH ===")
        title_search = await page.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    if (el.children.length === 0 && el.textContent.includes("Тошкент")) {
                        return {
                            tag: el.tagName,
                            class: el.className,
                            text: el.textContent.trim().substring(0, 200),
                            parentTag: el.parentElement ? el.parentElement.tagName : '',
                            parentClass: el.parentElement ? el.parentElement.className : '',
                            grandParentClass: el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement.className : ''
                        };
                    }
                }
                return null;
            }
        """)
        if title_search:
            print(f"  Title element: tag={title_search['tag']}, class='{title_search['class']}'")
            print(f"  Parent: tag={title_search['parentTag']}, class='{title_search['parentClass']}'")
            print(f"  Grandparent class='{title_search['grandParentClass']}'")
            print(f"  Text: {title_search['text']}")
        else:
            print("  Title text 'Тошкент' NOT FOUND in DOM!")
            
        print("\n=== LOT CARD CLASSES ===")
        lot_classes = await page.evaluate("""
            () => {
                const el = document.querySelector('.lot-card-content, .lot-card-section, .lot-card-basic-inf');
                if (!el) return 'Not found';
                return el.className + ' :: children classes: ' + 
                    Array.from(el.children).map(c => c.className).join(', ');
            }
        """)
        print(f"  {lot_classes}")
        
        print("\n=== RIGHT SIDE INFO ===")
        right_info = await page.evaluate("""
            () => {
                const el = document.querySelector('.lot-card-content-right, .lot-card-right, .card-right');
                if (el) return { class: el.className, text: el.innerText.substring(0, 300) };
                // Try finding all divs inside lot-card-content
                const content = document.querySelector('.lot-card-content');
                if (content) {
                    return { 
                        class: 'lot-card-content found', 
                        children: Array.from(content.children).map(c => ({ class: c.className, text: c.innerText?.substring(0, 100) }))
                    };
                }
                return 'Nothing found';
            }
        """)
        print(f"  {right_info}")
        
    finally:
        await browser.close()
        await pw.stop()

if __name__ == '__main__':
    asyncio.run(main())
