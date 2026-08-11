import asyncio
import httpx
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_ddg():
    query = "Қишлоқ хўжалигида билим ва инновациялар миллий маркази 305886617"
    url = "https://html.duckduckgo.com/html/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    data = {'q': query}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data, headers=headers)
        print(f"Status: {resp.status_code}")
        
        content = resp.text
        # print(content[:500])
        
        phone_pattern = r'\+998\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}'
        phones = re.findall(phone_pattern, content)
        
        local_phone_pattern = r'\(?\d{2}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        local_phones = re.findall(local_phone_pattern, content)
        
        print("Found +998:", set(phones))
        print("Found local:", set(local_phones))

if __name__ == "__main__":
    asyncio.run(test_ddg())
