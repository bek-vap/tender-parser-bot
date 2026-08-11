from aiogram import Bot
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.tender import Tender, TenderKeywordMatch, Keyword


class TelegramAlertService:
    def __init__(self):
        self.chat_id = settings.TELEGRAM_ALERT_CHAT_ID
        
        # Support proxy settings if defined in config
        if settings.TELEGRAM_PROXY_URL:
            from aiogram.client.session.aiohttp import AiohttpSession
            session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)
        else:
            self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def close(self) -> None:
        """Close the bot session cleanly"""
        if self.bot and self.bot.session:
            try:
                await self.bot.session.close()
            except Exception:
                pass

    async def send_tender_alert(self, tender: Tender, matched_keywords: list[Keyword] = None) -> None:
        if not self.chat_id:
            print("TELEGRAM_ALERT_CHAT_ID is empty, skipping alert")
            return

        if matched_keywords is None:
            matched_keywords = []

        # Formatting amount
        try:
            # Clean amount from non-numeric chars for formatting
            clean_amount = "".join(filter(lambda x: x.isdigit() or x == '.', str(tender.amount)))
            amount_val = float(clean_amount)
            amount_str = f"{amount_val:,.0f} UZS"
        except (ValueError, TypeError):
            amount_str = tender.amount or "По запросу"

        # Super Minimal Professional Style
        source_name = tender.source.replace("https://", "").replace("http://", "").split('/')[0].upper()
        lot_id = tender.external_id or "N/A"

        # Format phone
        phone = tender.organizer_phone or None
        if phone:
            if phone.isdigit() and len(phone) == 9:
                phone = f"+998 {phone}"
            elif phone.isdigit() and len(phone) == 12 and phone.startswith('998'):
                phone = f"+{phone}"

        # Build message
        if tender.source.upper().startswith('UZEX') or 'ETENDER' in tender.source.upper() or 'XARID' in tender.source.upper():
            # Detailed UZEX style
            text = (
                f"[{source_name}] | ID: {lot_id}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📍 Obyekt: {tender.title}\n"
                f"🏢 Buyurtmachi: {tender.organizer_name or source_name}\n"
                f"🆔 STIR (INN): {tender.organizer_inn or ''}\n"
                f"💰 Summa: {amount_str}\n"
                f"📍 Hudud: {tender.region or ''}\n\n"
                f"🔗 Batafsil ma'lumot saytda ({tender.url})"
            )
        else:
            # Fallback simple format (used for E_AUKSION and other sources)
            text = (
                f"[{source_name}] | ID: {lot_id}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📍 Obyekt: {tender.title}\n"
                f"🏢 Buyurtmachi: {tender.organizer_name or source_name}\n"
                f"💰 Summa: {amount_str}\n"
                f"📍 Hudud: {tender.region or ''}\n\n"
                f"🔗 Batafsil ma'lumot saytda ({tender.url})"
            )

        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔎 Tenderni ochish", url=tender.url)]
            ])
            
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=text, 
                reply_markup=kb,
                disable_web_page_preview=True
            )
            print(f"[TG] Alert sent: lot {lot_id} [{source_name}]")
        except Exception as e:
            print(f"[TG] Failed to send alert for lot {lot_id}: {e}")

    async def check_and_send_alerts_for_new_tenders(self) -> None:
        """Отправить алерты для новых тендеров с keyword matches"""
        db = SessionLocal()
        try:
            # Найти тендеры с keyword matches, для которых еще не было алертов
            # Для простоты: все тендеры с keyword matches считаем "новыми"
            tenders_with_matches = (
                db.query(Tender)
                .join(TenderKeywordMatch)
                .join(Keyword)
                .filter(Keyword.is_active == True)
                .all()
            )

            for tender in tenders_with_matches:
                # Получить keywords для этого тендера
                matched_keywords = (
                    db.query(Keyword)
                    .join(TenderKeywordMatch)
                    .filter(TenderKeywordMatch.tender_id == tender.id)
                    .all()
                )

                if matched_keywords:
                    await self.send_tender_alert(tender, matched_keywords)
        finally:
            db.close()
