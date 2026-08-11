#!/usr/bin/env python3
"""
Simple test script for Tender Intelligence Platform
Bypasses PowerShell issues by running Python directly
"""

import sys
import os

# Add the backend directory to Python path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "..", "backend_py"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Testing Tender Intelligence Platform...")
print(f"Python path: {sys.path[0]}")

# Test 1: Check if we can import the app
try:
    from app.models.tender import Keyword
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    keyword_count = db.query(Keyword).count()
    db.close()
    
    print(f"✅ Database connection successful!")
    print(f"✅ Found {keyword_count} keywords in database")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 2: Test keyword matching
try:
    from app.services.keyword_filter import KeywordFilterService
    
    filter_service = KeywordFilterService()
    test_text = "строительство склада 1000м²"
    keywords = [{"id": "1", "phrase": "строительство"}, {"id": "2", "phrase": "склад"}]
    
    matches = filter_service.match(test_text, keywords)
    print(f"✅ Keyword matching test: {len(matches)} matches found")
    
except Exception as e:
    print(f"❌ Keyword filter error: {e}")

# Test 3: Test configuration
try:
    from app.core.config import settings
    
    print(f"✅ Configuration loaded:")
    print(f"   - Database URL: {settings.DATABASE_URL[:50]}...")
    print(f"   - Redis URL: {settings.REDIS_URL}")
    print(f"   - Telegram Bot: {'✅' if settings.TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"   - Scrape Interval (Fallback): {settings.SCRAPE_EVERY_MINUTES} minutes")
    print(f"   - Scrape Daily Run Time: {settings.SCRAPE_HOUR:02d}:{settings.SCRAPE_MINUTE:02d} Tashkent time")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")

print("\n🎉 Platform test completed!")
print("📋 Next steps:")
print("1. Start the API server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
print("2. Test endpoints: curl http://localhost:8000/health")
print("3. Check API docs: http://localhost:8000/docs")
