import asyncio
from playwright.async_api import async_playwright
import re

async def test_google_enrich():
    company_name = "Қишлоқ хўжалигида билим ва инновациялар миллий маркази"
    inn = "305886617"
    
    query = f"{company_name} {inn} телефон"
    print(f"Searching google for: {query}")
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            
            # Extract phones
            phone_pattern = r'\+998\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}'
            phones = re.findall(phone_pattern, content)
            
            # Additional simple pattern for Uzbek phones without +998 like (71) 200-00-00
            local_phone_pattern = r'\(?\d{2}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
            local_phones = re.findall(local_phone_pattern, content)
            
            print("Found +998 phones:", set(phones))
            print("Found local phones:", set(local_phones))
            
            text = await page.evaluate("() => document.body.innerText")
            print("--- Text ---")
            print(text[:1000])
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_google_enrich())
