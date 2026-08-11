import os
import re

file_path = r'd:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py\app\bot\bot.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update bot initialization to support proxy
if 'settings.TELEGRAM_PROXY_URL' not in content:
    content = content.replace(
        'bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)',
        '''    if settings.TELEGRAM_PROXY_URL:
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)
    else:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)'''
    )

# 2. Fix utcnow deprecation warnings
# datetime.utcnow() -> datetime.now(datetime.UTC)
# However, many projects use datetime.utcnow() without the timezone object.
# The warning suggests: datetime.now(datetime.UTC)
# But we need to make sure 'timezone' or 'UTC' is imported if we use them.
# Let's use a simpler fix that is compatible: datetime.now(timezone.utc)
# First, check imports
if 'from datetime import datetime, timedelta' in content:
    content = content.replace('from datetime import datetime, timedelta', 'from datetime import datetime, timedelta, timezone')

# Replace all occurrences of datetime.utcnow()
content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated bot.py with proxy support and fixed utcnow warnings")
