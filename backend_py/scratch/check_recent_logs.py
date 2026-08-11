import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.log import ParserLog

db = SessionLocal()
try:
    logs = db.query(ParserLog).order_by(ParserLog.started_at.desc()).limit(20).all()
    print(f"{'Started At':<20} | {'Source':<12} | {'Status':<10} | {'Processed':<10} | {'Found':<6} | {'Message':<30}")
    print("-" * 100)
    for log in logs:
        started = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "N/A"
        print(f"{started:<20} | {log.source or 'N/A':<12} | {log.status or 'N/A':<10} | {log.items_processed or 0:<10} | {log.items_found or 0:<6} | {str(log.message)[:30]}")
finally:
    db.close()
