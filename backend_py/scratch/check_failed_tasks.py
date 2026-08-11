import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.log import ParserLog

db = SessionLocal()
try:
    failed_logs = db.query(ParserLog).filter(ParserLog.status == "failed").order_by(ParserLog.started_at.desc()).limit(5).all()
    print(f"Found {len(failed_logs)} failed logs:")
    for log in failed_logs:
        started = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "N/A"
        print("=" * 80)
        print(f"Task: {log.task_name} | Source: {log.source} | Started: {started}")
        print(f"Error Message: {log.message}")
        print("Traceback:")
        print(log.error_traceback or "No traceback logged")
finally:
    db.close()
