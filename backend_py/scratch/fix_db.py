import sys
import os

# Добавляем корневую папку в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import engine
from app.models.log import ParserLog

def main():
    print("Удаляем старую таблицу parser_logs...")
    ParserLog.__table__.drop(engine, checkfirst=True)
    
    print("Создаем новую таблицу parser_logs с правильными колонками...")
    ParserLog.__table__.create(engine)
    
    print("✅ База данных успешно обновлена! Теперь парсеры будут работать.")

if __name__ == "__main__":
    main()
