#!/usr/bin/env python3
"""
Ручной запуск проверки победителей (все UZEX-тендеры без записи в winners).
"""
import argparse
import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверка победителей UZEX etender")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Сколько дней назад смотреть (0 = вся база). По умолчанию из .env WINNER_DAYS_BACK",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Макс. тендеров за запуск (0 = без лимита). По умолчанию WINNER_BATCH_LIMIT",
    )
    args = parser.parse_args()

    from app.core.config import settings
    from app.services.winner_parser_service import get_winner_parser_service

    days_back = args.days if args.days is not None else settings.WINNER_DAYS_BACK
    batch_limit = args.limit if args.limit is not None else settings.WINNER_BATCH_LIMIT

    print("=" * 60)
    print("🏆 Проверка победителей UZEX etender")
    print(f"   days_back={days_back}, limit={batch_limit or 'нет'}")
    print("=" * 60)

    service = get_winner_parser_service()
    result = asyncio.run(
        service.parse_completed_tenders(
            days_back=days_back,
            batch_limit=batch_limit,
            api_delay=settings.WINNER_API_DELAY_SECONDS,
        )
    )

    print("\n✅ Готово")
    print(f"   Проверено: {result.get('tenders_checked', 0)}")
    print(f"   Победителей добавлено: {result.get('winners_parsed', 0)}")
    print(f"   Ещё без победителя: {result.get('still_open', 0)}")
    print(f"   Ошибок: {result.get('errors', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
