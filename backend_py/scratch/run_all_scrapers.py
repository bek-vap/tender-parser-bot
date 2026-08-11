import sys
import os

# Добавляем корневую папку в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.workers.tasks import (
    scrape_uzex_etender,
    scrape_xarid_uzex,
    scrape_tender_mc,
    scrape_e_auksion
)

def main():
    print("🚀 Отправляем задачу парсинга UZEX в очередь...")
    scrape_uzex_etender.delay()
    
    print("🚀 Отправляем задачу парсинга XARID в очередь...")
    scrape_xarid_uzex.delay()
    
    print("🚀 Отправляем задачу парсинга TENDER_MC в очередь...")
    scrape_tender_mc.delay()
    
    print("🚀 Отправляем задачу парсинга E-AUKSION в очередь...")
    scrape_e_auksion.delay()
    
    print("✅ Все 4 задачи успешно отправлены в очередь (Celery worker).")
    print("Бот скоро пришлет вам результаты в Telegram!")

if __name__ == "__main__":
    main()
