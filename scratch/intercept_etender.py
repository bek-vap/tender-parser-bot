import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    print("Starting Playwright interception...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept network requests
        async def handle_request(request):
            if "uzex.uz" in request.url:
                print(f"Request: {request.method} {request.url}")
                if request.post_data:
                    print(f"  Payload: {request.post_data}")
                    
        async def handle_response(response):
            if "uzex.uz" in response.url:
                print(f"Response: {response.status} {response.url}")
                try:
                    text = await response.text()
                    print(f"  Body: {text[:400]}")
                except Exception as e:
                    print(f"  Failed to get body: {e}")

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Navigate to successful lot page
        for trade_id in [486901]:
            url = "https://etender.uzex.uz/deals-list"
            print(f"\nNavigating to {url}...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(5) # Wait for extra API calls
                html = await page.content()
                print("HTML length:", len(html))
                with open("scratch/page_content.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                print(f"Navigation failed for {trade_id}: {e}")
                try:
                    html = await page.content()
                    print("HTML length on failure:", len(html))
                    with open("scratch/page_content_fail.html", "w", encoding="utf-8") as f:
                        f.write(html)
                except:
                    pass
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
