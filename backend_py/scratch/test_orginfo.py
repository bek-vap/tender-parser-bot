import asyncio
from playwright.async_api import async_playwright
import re

async def test_orginfo():
    inn = "305886617"
    print(f"Testing orginfo for {inn}...")
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            url = f"https://orginfo.uz/ru/search/organizations/?q={inn}"
            print(f"Going to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Look for the first search result link
            print("Checking search results...")
            
            # The search results on orginfo usually have a link to /ru/organization/...
            # Let's just grab the whole page text to see if anything loaded
            content = await page.content()
            
            with open("scratch/orginfo_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Try to find a link to the company
            company_link = await page.evaluate('''() => {
                const links = document.querySelectorAll('a[href*="/organization/"]');
                for (const a of links) {
                    if (a.innerText.trim().length > 0) return a.href;
                }
                return null;
            }''')
            
            if company_link:
                print(f"Found company link: {company_link}")
                await page.goto(company_link, wait_until="networkidle")
                content = await page.content()
                
                # Try to extract director and address using regex
                director_match = re.search(r'Руководитель:?[\s\S]*?<div[^>]*>([^<]+)</div>', content)
                if not director_match:
                    director_match = re.search(r'Директор:?[\s\S]*?<div[^>]*>([^<]+)</div>', content)
                
                if director_match:
                    print(f"Director: {director_match.group(1).strip()}")
                else:
                    print("Director not found via regex.")
                    
                # Let's extract all text to see what we have
                text = await page.evaluate("() => document.body.innerText")
                print("--- Page Text Extract ---")
                print(text[:1000])
                
            else:
                print("No company link found in search results. Maybe blocked or no results.")
                text = await page.evaluate("() => document.body.innerText")
                print(text[:500])
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_orginfo())
