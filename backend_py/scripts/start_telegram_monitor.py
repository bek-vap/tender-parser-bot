import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from app.services.telegram_monitor_service import get_telegram_monitor_service

async def main():
    print("🚀 Запуск мониторинга Telegram каналов...")
    print("При первом запуске потребуется авторизация в Telegram (ввод номера телефона и кода).")
    
    monitor_service = get_telegram_monitor_service()
    try:
        await monitor_service.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен пользователем.")
        await monitor_service.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Ошибка мониторинга: {e}")

if __name__ == "__main__":
    asyncio.run(main())
