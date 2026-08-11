import json
import traceback
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.log import ParserLog


class LoggingService:
    """Comprehensive logging service for parsing tasks"""
    
    @staticmethod
    def log_task_start(task_name: str, source: str, message: Optional[str] = None, details: Optional[dict] = None) -> ParserLog:
        """Log the start of a parsing task"""
        db = SessionLocal()
        try:
            log_entry = ParserLog(
                task_name=task_name,
                source=source,
                status="started",
                message=message,
                details=json.dumps(details) if details else None,
                started_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        finally:
            db.close()
    
    @staticmethod
    def log_task_complete(
        log_id: str, 
        items_processed: int = 0, 
        items_found: int = 0,
        items_skipped: int = 0,
        captcha_detected: bool = False,
        message: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """Log the completion of a parsing task"""
        db = SessionLocal()
        try:
            log_entry = db.query(ParserLog).filter(ParserLog.id == log_id).first()
            if log_entry:
                log_entry.status = "completed"
                log_entry.completed_at = datetime.utcnow()
                log_entry.duration_seconds = int((log_entry.completed_at - log_entry.started_at).total_seconds())
                log_entry.items_processed = items_processed
                log_entry.items_found = items_found
                log_entry.items_skipped = items_skipped
                log_entry.captcha_detected = captcha_detected
                log_entry.message = message
                log_entry.details = json.dumps(details) if details else None
                db.commit()
                
                # Notify admins about results
                if log_entry.source != "SYSTEM":
                    LoggingService._notify_admins_task_result(db, log_entry.source, items_found, items_processed, items_skipped)
        finally:
            db.close()
            
    @staticmethod
    def _notify_admins_task_result(db: Session, source: str, found: int, processed: int, skipped: int):
        """Send a summary report to all registered admins"""
        try:
            from app.models.admin import Admin
            from app.models.tender import SystemSetting
            from app.core.config import settings
            import requests
            
            admins = db.query(Admin).all()
            if not admins:
                return
            
            # Get system language
            lang_setting = db.query(SystemSetting).filter(SystemSetting.key == "system_language").first()
            lang = lang_setting.value if lang_setting else "ru"
            
            # Localization strings
            texts = {
                "ru": {
                    "title": "✅ <b>ОТЧЕТ О ПРОВЕРКЕ</b>",
                    "source": "🌐 <b>Источник:</b>",
                    "found": "📥 Найдено новых:",
                    "skipped": "⏩ Пропущено (дубли):",
                    "total": "📦 Всего проверено:",
                    "time": "🕒 Время:"
                },
                "uz": {
                    "title": "✅ <b>TEKSHIRUV HISOBOTI</b>",
                    "source": "🌐 <b>Manba:</b>",
                    "found": "📥 Yangi topildi:",
                    "skipped": "⏩ O'tkazib yuborildi (dublikat):",
                    "total": "📦 Jami tekshirildi:",
                    "time": "🕒 Vaqt:"
                }
            }
            
            t = texts.get(lang, texts["ru"])
            
            msg = (
                f"{t['title']}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{t['source']} <b>{source}</b>\n"
                f"{t['found']} <b>{found}</b>\n"
                f"{t['skipped']} {skipped}\n"
                f"{t['total']} {processed}\n"
                f"{t['time']} {datetime.now().strftime('%H:%M:%S')}"
            )
            
            bot_token = settings.TELEGRAM_BOT_TOKEN
            if not bot_token:
                return
                
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            for admin in admins:
                if admin.telegram_id:
                    try:
                        requests.post(url, json={
                            "chat_id": admin.telegram_id,
                            "text": msg,
                            "parse_mode": "HTML"
                        }, timeout=5)
                    except:
                        pass
        except Exception as e:
            print(f"Failed to notify admins: {e}")
    
    @staticmethod
    def log_task_failed(
        log_id: str, 
        error: Exception, 
        message: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """Log the failure of a parsing task and alert if necessary"""
        db = SessionLocal()
        try:
            log_entry = db.query(ParserLog).filter(ParserLog.id == log_id).first()
            if log_entry:
                log_entry.status = "failed"
                log_entry.completed_at = datetime.utcnow()
                log_entry.duration_seconds = int((log_entry.completed_at - log_entry.started_at).total_seconds())
                log_entry.message = message or str(error)
                log_entry.error_traceback = traceback.format_exc()
                log_entry.details = json.dumps(details) if details else None
                db.commit()
                
                # Check for consecutive failures to alert admin
                LoggingService._check_and_alert_failures(db, log_entry.source)
        finally:
            db.close()
    
    @staticmethod
    def _check_and_alert_failures(db: Session, source: str):
        """Internal method to check for repeated failures and send alert"""
        try:
            # Get last 3 logs for this source
            recent_logs = db.query(ParserLog).filter(
                ParserLog.source == source
            ).order_by(ParserLog.started_at.desc()).limit(3).all()
            
            # If all last 3 are failed, send alert
            if len(recent_logs) >= 3 and all(l.status in ["failed", "captcha_detected"] for l in recent_logs):
                from app.core.config import settings
                import requests
                
                # Send emergency alert via Telegram Bot API (direct request to avoid circular imports)
                bot_token = settings.TELEGRAM_BOT_TOKEN
                chat_id = settings.TELEGRAM_ALERT_CHAT_ID
                
                if bot_token and chat_id:
                    alert_text = (
                        f"⚠️ <b>КРИТИЧЕСКИЙ СБОЙ ПАРСЕРА</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🌐 <b>Источник:</b> {source}\n"
                        f"❌ <b>Статус:</b> 3 ошибки подряд\n"
                        f"⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
                        f"<i>Система требует проверки!</i>"
                    )
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(url, json={
                        "chat_id": chat_id,
                        "text": alert_text,
                        "parse_mode": "HTML"
                    }, timeout=5)
        except Exception as e:
            print(f"Failed to send emergency alert: {e}")

    @staticmethod
    def log_captcha_detected(task_name: str, source: str, message: Optional[str] = None) -> ParserLog:
        """Log captcha detection and alert if frequent"""
        db = SessionLocal()
        try:
            log_entry = ParserLog(
                task_name=task_name,
                source=source,
                status="captcha_detected",
                message=message or "CAPTCHA detected during parsing",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            # Check for repeated captchas
            LoggingService._check_and_alert_failures(db, source)
            
            return log_entry
        finally:
            db.close()
    
    @staticmethod
    def log_new_tender_found(
        task_name: str, 
        source: str, 
        tender_title: str,
        keywords: list[str],
        message: Optional[str] = None
    ) -> ParserLog:
        """Log when a new tender with keyword matches is found"""
        db = SessionLocal()
        try:
            log_entry = ParserLog(
                task_name=task_name,
                source=source,
                status="new_tender_found",
                message=message or f"New tender found: {tender_title}",
                details=json.dumps({"tender_title": tender_title, "matched_keywords": keywords}),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        finally:
            db.close()
    
    @staticmethod
    def log_duplicate_skipped(
        task_name: str, 
        source: str, 
        tender_title: str,
        message: Optional[str] = None
    ) -> ParserLog:
        """Log when a duplicate tender is skipped"""
        db = SessionLocal()
        try:
            log_entry = ParserLog(
                task_name=task_name,
                source=source,
                status="duplicate_skipped",
                message=message or f"Duplicate tender skipped: {tender_title}",
                details=json.dumps({"tender_title": tender_title}),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        finally:
            db.close()
    
    @staticmethod
    def get_recent_logs(limit: int = 100, status_filter: Optional[str] = None) -> list[ParserLog]:
        """Get recent parsing logs with optional status filter"""
        db = SessionLocal()
        try:
            query = db.query(ParserLog).order_by(ParserLog.started_at.desc())
            if status_filter:
                query = query.filter(ParserLog.status == status_filter)
            return query.limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_task_statistics(days: int = 7) -> dict:
        """Get parsing statistics for the last N days"""
        db = SessionLocal()
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            logs = db.query(ParserLog).filter(ParserLog.started_at >= cutoff_date).all()
            
            stats = {
                "total_tasks": len(logs),
                "completed": len([l for l in logs if l.status == "completed"]),
                "failed": len([l for l in logs if l.status == "failed"]),
                "captcha_detected": len([l for l in logs if l.status == "captcha_detected"]),
                "new_tenders_found": len([l for l in logs if l.status == "new_tender_found"]),
                "duplicates_skipped": len([l for l in logs if l.status == "duplicate_skipped"]),
                "total_items_processed": sum([l.items_processed or 0 for l in logs]),
                "total_items_found": sum([l.items_found or 0 for l in logs]),
                "average_duration_seconds": sum([l.duration_seconds or 0 for l in logs]) / len(logs) if logs else 0
            }
            
            return stats
        finally:
            db.close()
