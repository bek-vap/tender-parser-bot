import asyncio
from playwright.async_api import async_playwright

async def test_orginfo_real():
    inn = "313003526" 
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = f"https://orginfo.uz/ru/search/organizations/?q={inn}"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        company_link = await page.evaluate('''() => {
            const links = document.querySelectorAll('a[href*="/organization/"]');
            for (const a of links) {
                if (a.innerText.trim().length > 0) return a.href;
            }
            return null;
        }''')
        
        if company_link:
            print(f"Found link: {company_link}")
            await page.goto(company_link, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            data = await page.evaluate('''() => {
                const results = {};
                const items = document.querySelectorAll('div, p, span, li, tr');
                for (const el of items) {
                    const text = el.innerText ? el.innerText.trim() : '';
                    if (text.includes('Руководитель') || text.includes('Директор')) {
                        results.director_raw = text;
                    }
                    if (text.includes('Адрес')) {
                        results.address_raw = text;
                    }
                }
                return results;
            }''')
            print("Extracted via JS:", data)
            
            # also save HTML
            with open("scratch/orginfo_company.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
        else:
            print("No link found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_orginfo_real())
