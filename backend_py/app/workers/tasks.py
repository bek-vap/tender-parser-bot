import asyncio
import uuid
import difflib
from datetime import datetime, timedelta
from sqlalchemy import or_

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.clients.uzex_etender_api import UzexEtenderApiClient, UzexEtenderBrowserClient
from app.db.session import SessionLocal
from app.models.tender import Tender, Keyword, TenderKeywordMatch, SystemSetting
from app.services.keyword_filter import KeywordFilterService
from app.services.telegram_alerts import TelegramAlertService
from app.services.logging_service import LoggingService
from app.services.google_sheets_service import get_google_sheets_service
from app.services.crm_service import get_crm_service
from app.services.winner_parser_service import get_winner_parser_service
from app.services.company_enrichment_service import get_company_enrichment_service
from app.scrapers.xarid_uzex import XaridUzexScraper
from app.scrapers.tender_mc import TenderMcScraper
from app.scrapers.e_auksion import EAuksionScraper
from app.utils.hashing import normalize_text, sha256
from app.workers.celery_app import celery_app
from app.services.keyword_filter import KeywordFilterService, KeywordDTO


def is_duplicate(db, source: str, external_id: str, url: str, title: str, title_hash: str, compound_hash: str) -> bool:
    """
    Check if a tender is a duplicate based on:
    - compound_hash (external_id + source + title_hash)
    - url (direct link)
    """
    # Exact matches by compound hash or URL (fastest and most reliable)
    existing = db.query(Tender).filter(
        or_(
            Tender.compound_hash == compound_hash,
            Tender.url == url
        )
    ).first()
    
    if existing:
        return True
            
    return False



def is_source_enabled(db, source_key: str) -> bool:
    """Check if a specific source is enabled in system settings"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == f"source_{source_key.lower()}").first()
    if setting:
        return setting.value.lower() == "true"
    return True  # Enabled by default


def is_google_sheets_enabled(db) -> bool:
    """Check if Google Sheets export is enabled in system settings"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == "export_google_sheets").first()
    if setting:
        return setting.value.lower() == "true"
    return settings.GOOGLE_SHEETS_AUTO_EXPORT # Fallback to .env


async def _scrape_uzex_etender_impl() -> dict:
    """Main scraping task implementation for etender.uzex.uz"""
    task_name = "scrape_uzex_etender"
    source = "UZEX"
    
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    api = UzexEtenderApiClient()
    db = SessionLocal()
    
    inserted = 0
    skipped_dup = 0
    skipped_no_match = 0

    try:
        if not is_source_enabled(db, source):
            print(f"Source {source} is disabled in settings. Skipping.")
            db.close()
            return {"status": "skipped", "message": "Source disabled"}

        print("Loading keywords...")
        try:
            # Load active keywords including blacklist ones
            keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
            keyword_dtos = [KeywordDTO(id=str(k.id), phrase=k.phrase, is_blacklist=k.is_blacklist) for k in keywords]
            
            keyword_filter = KeywordFilterService()
            print(f"Loaded {len(keywords)} keywords (Blacklist: {len([k for k in keywords if k.is_blacklist])})")

            LoggingService.log_new_tender_found(
                task_name=task_name,
                source=source,
                tender_title="Keywords loaded",
                keywords=[k.phrase for k in keywords],
                message=f"Loaded {len(keywords)} keywords for matching"
            )
        except Exception as e:
            print(f"Error loading keywords: {e}")
            LoggingService.log_task_failed(
                log_id=log_entry.id,
                error=e,
                message="Failed to load keywords from database"
            )
            raise
        
        # Initialize Telegram alert service
        alert_service = TelegramAlertService()
        keyword_filter = KeywordFilterService()

        print("Calling TradeList API...")
        # type_id mapping for etender.uzex.uz tabs:
        # 1 = Горящие тендеры (Tender)
        # 2 = Горящие отборы (Selection)
        # 3 = Рамочный договор (Framework Agreement)
        # 4 = Мастер план (Master Plan)
        # 5 = Обсуждение документа (Document Discussion)
        TYPE_ID_NAMES = {
            1: "Горящие тендеры",
            2: "Горящие отборы",
            3: "Рамочный договор",
            4: "Мастер план",
            5: "Обсуждение документа",
        }
        items = []
        for type_id in [1, 2, 3, 4, 5]:
            type_name = TYPE_ID_NAMES.get(type_id, f"Type-{type_id}")
            print(f"Fetching type_id={type_id} ({type_name})...")
            type_items = []
            try:
                # Step 1: Direct API Client
                type_items = await api.trade_list(type_id=type_id, from_=1, to=100, system_id=0)
                print(f"API returned {len(type_items)} items for {type_name}")
            except Exception as e:
                # Step 2: Fallback to Browser Interception Client
                print(f"[-] UZEX direct API failed for {type_name}: {e}. Falling back to browser emulation...")
                try:
                    browser_client = UzexEtenderBrowserClient()
                    type_items = await browser_client.fetch_trade_list(type_id=type_id, page_size=100)
                    print(f"Browser emulation succeeded, intercepted {len(type_items)} items for {type_name}")
                except Exception as ex:
                    print(f"[-] Browser emulation also failed for {type_name}: {ex}")
                    # Don't fail the entire scraping task if only one type fails
                    continue
            items.extend(type_items)

        for it in reversed(items):
            title_norm = normalize_text(it.name)
            title_hash = sha256(title_norm)
            compound_hash = sha256(f"{source}:{it.id}:{title_norm}")
            url = f"https://etender.uzex.uz/lot/{it.id}"

            # Enhanced duplicate check
            if is_duplicate(db, source, str(it.id), url, it.name, title_hash, compound_hash):
                skipped_dup += 1
                LoggingService.log_duplicate_skipped(
                    task_name=task_name,
                    source=source,
                    tender_title=it.name,
                    message=f"Duplicate tender skipped: {it.name}"
                )
                continue

            # Keyword matching BEFORE DB insert — only save tenders with keyword matches
            matched_ids = keyword_filter.match(it.name + " " + (it.region_name or ""), keyword_dtos)
            matched_kws = [k for k in keywords if str(k.id) in matched_ids]

            if not matched_ids:
                skipped_no_match += 1
                continue

            tender = Tender(
                source=source,
                external_id=str(it.id),
                title=it.name,
                description=None,
                amount=str(it.cost) if it.cost is not None else None,
                region=it.region_name,
                url=url,
                organizer_name=it.seller_name,
                organizer_inn=str(it.seller_tin) if it.seller_tin else None,
                title_hash=title_hash,
                compound_hash=compound_hash,
            )

            try:
                db.add(tender)
                db.flush()

                print(f"\u2705 Tender MATCHED: {it.name}")
                for kw_id in matched_ids:
                    db.add(TenderKeywordMatch(tender_id=tender.id, keyword_id=kw_id))

                db.commit()
                inserted += 1

                LoggingService.log_new_tender_found(
                    task_name=task_name,
                    source=source,
                    tender_title=it.name,
                    keywords=[k.phrase for k in matched_kws],
                    message=f"New tender with keyword matches: {it.name}"
                )

                # Send Telegram alert (only for matched tenders)
                try:
                    await alert_service.send_tender_alert(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send Telegram alert: {e}")

                # Send to CRM
                try:
                    crm_service = get_crm_service()
                    await crm_service.send_lead(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send CRM lead: {e}")
            except Exception as insert_error:
                db.rollback()
                skipped_dup += 1
                print(f"Failed to insert/commit tender due to DB error (likely duplicate): {insert_error}")
                LoggingService.log_duplicate_skipped(
                    task_name=task_name,
                    source=source,
                    tender_title=it.name,
                    message=f"Duplicate skipped due to database constraint: {insert_error}"
                )

        # Export to Google Sheets if enabled
        google_sheets_exported = 0
        if is_google_sheets_enabled(db) and inserted > 0:
            try:
                sheets_service = get_google_sheets_service()
                export_result = sheets_service.export_new_tenders(limit=50)
                google_sheets_exported = export_result.get('exported', 0)
                print(f"📊 Google Sheets export: {export_result}")
            except Exception as e:
                print(f"❌ Google Sheets export failed: {e}")

        # Log task completion
        LoggingService.log_task_complete(
            log_id=log_entry.id,
            items_processed=len(items),
            items_found=inserted,
            items_skipped=skipped_dup + skipped_no_match,
            message=f"Task completed. Processed {len(items)}, Matched & Saved {inserted}, Skipped dup {skipped_dup}, No match {skipped_no_match}"
        )

        print(f"[SUCCESS] [UZEX etender] Processed: {len(items)}, Matched & Saved: {inserted}, Skipped dup: {skipped_dup}, No match: {skipped_no_match}")
        return {
            "status": "done", 
            "fetched": len(items), 
            "inserted": inserted,
            "skippedDuplicate": skipped_dup,
            "skippedNoMatch": skipped_no_match,
        }
    except Exception as e:
        print(f"Task failed: {e}")
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise
    finally:
        await api.close()
        if 'alert_service' in locals():
            await alert_service.close()
        db.close()


@celery_app.task(name="app.workers.tasks.scrape_uzex_etender")
def scrape_uzex_etender() -> dict:
    """Main scraping task for etender.uzex.uz"""
    return asyncio.run(_scrape_uzex_etender_impl())


async def _scrape_xarid_uzex_impl() -> dict:
    """Scrape tenders from xarid.uzex.uz (Async Implementation)"""
    task_name = "scrape_xarid_uzex"
    source = "XARID_UZEX"
    
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    db = SessionLocal()
    
    try:
        if not is_source_enabled(db, source):
            db.close()
            return {"status": "skipped", "message": "Source disabled"}

        scraper = XaridUzexScraper()
        items = await scraper.run()
        
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        keyword_dtos = [KeywordDTO(id=str(k.id), phrase=k.phrase, is_blacklist=k.is_blacklist) for k in keywords]
        
        keyword_filter = KeywordFilterService()
        alert_service = TelegramAlertService()
        crm_service = get_crm_service()
        
        inserted = 0
        skipped_dup = 0
        skipped_no_match = 0
        for it in reversed(items[:100]): # Up to 100
            title_hash = sha256(normalize_text(it.title))
            compound_hash = sha256(f"{source}:{it.external_id}:{title_hash}")
            
            if is_duplicate(db, source, it.external_id, it.url, it.title, title_hash, compound_hash):
                skipped_dup += 1
                continue

            # Keyword matching BEFORE DB insert — only save matched tenders
            matched_ids = keyword_filter.match(it.title, keyword_dtos)
            matched_kws = [k for k in keywords if str(k.id) in matched_ids]

            if not matched_ids:
                skipped_no_match += 1
                continue

            tender = Tender(
                source=source,
                external_id=it.external_id,
                organizer_name=it.organizer_name,
                organizer_inn=getattr(it, 'organizer_inn', None),
                title=it.title,
                amount=it.amount,
                region=it.region,
                url=it.url,
                title_hash=title_hash,
                compound_hash=compound_hash
            )
            try:
                db.add(tender)
                db.flush()

                for kw_id in matched_ids:
                    db.add(TenderKeywordMatch(tender_id=tender.id, keyword_id=kw_id))

                db.commit()
                inserted += 1

                try:
                    await alert_service.send_tender_alert(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send Telegram alert: {e}")

                try:
                    await crm_service.send_lead(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send CRM lead: {e}")
            except Exception as insert_error:
                db.rollback()
                skipped_dup += 1
                print(f"Failed to insert/commit tender due to DB error (likely duplicate): {insert_error}")
                LoggingService.log_duplicate_skipped(
                    task_name=task_name,
                    source=source,
                    tender_title=it.title,
                    message=f"Duplicate skipped due to database constraint: {insert_error}"
                )
        
        if is_google_sheets_enabled(db) and inserted > 0:
            try:
                get_google_sheets_service().export_new_tenders(limit=50)
            except Exception: pass
        
        print(f"[SUCCESS] [XARID UZEX] Processed: {len(items)}, Matched & Saved: {inserted}, Skipped dup: {skipped_dup}, No match: {skipped_no_match}")
        LoggingService.log_task_complete(log_id=log_entry.id, items_processed=len(items), items_found=inserted, items_skipped=skipped_dup + skipped_no_match)
        return {"status": "done", "fetched": len(items), "inserted": inserted, "skipped": skipped_dup, "skippedNoMatch": skipped_no_match}
    except Exception as e:
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise
    finally:
        if 'alert_service' in locals():
            await alert_service.close()
        db.close()


@celery_app.task(name="app.workers.tasks.scrape_xarid_uzex")
def scrape_xarid_uzex() -> dict:
    """Scrape tenders from xarid.uzex.uz"""
    return asyncio.run(_scrape_xarid_uzex_impl())


async def _scrape_tender_mc_impl() -> dict:
    """Scrape tenders from tender.mc.uz (Async Implementation)"""
    task_name = "scrape_tender_mc"
    source = "TENDER_MC"
    
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    db = SessionLocal()
    
    try:
        if not is_source_enabled(db, source):
            db.close()
            return {"status": "skipped", "message": "Source disabled"}

        scraper = TenderMcScraper()
        items = await scraper.run()
        
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        keyword_dtos = [KeywordDTO(id=str(k.id), phrase=k.phrase, is_blacklist=k.is_blacklist) for k in keywords]
        
        keyword_filter = KeywordFilterService()
        alert_service = TelegramAlertService()
        crm_service = get_crm_service()
        
        inserted = 0
        skipped_dup = 0
        skipped_no_match = 0
        for it in reversed(items[:100]):
            title_hash = sha256(normalize_text(it.title))
            compound_hash = sha256(f"{source}:{it.external_id}:{title_hash}")
            
            if is_duplicate(db, source, it.external_id, it.url, it.title, title_hash, compound_hash):
                skipped_dup += 1
                continue

            # Keyword matching BEFORE DB insert — only save matched tenders
            matched_ids = keyword_filter.match(f"{it.title} {it.region or ''}", keyword_dtos)
            matched_kws = [k for k in keywords if str(k.id) in matched_ids]

            if not matched_ids:
                skipped_no_match += 1
                continue

            tender = Tender(
                source=source,
                external_id=it.external_id,
                organizer_name=getattr(it, 'organizer_name', None),
                title=it.title,
                amount=it.amount,
                region=it.region,
                url=it.url,
                title_hash=title_hash,
                compound_hash=compound_hash
            )
            try:
                db.add(tender)
                db.flush()

                for kw_id in matched_ids:
                    db.add(TenderKeywordMatch(tender_id=tender.id, keyword_id=kw_id))

                db.commit()
                inserted += 1

                try:
                    await alert_service.send_tender_alert(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send Telegram alert: {e}")

                try:
                    await crm_service.send_lead(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send CRM lead: {e}")
            except Exception as insert_error:
                db.rollback()
                skipped_dup += 1
                print(f"Failed to insert/commit tender due to DB error (likely duplicate): {insert_error}")
                LoggingService.log_duplicate_skipped(
                    task_name=task_name,
                    source=source,
                    tender_title=it.title,
                    message=f"Duplicate skipped due to database constraint: {insert_error}"
                )
        
        if is_google_sheets_enabled(db) and inserted > 0:
            try:
                get_google_sheets_service().export_new_tenders(limit=50)
            except Exception: pass
        
        print(f"[SUCCESS] [TENDER MC] Processed: {len(items)}, Matched & Saved: {inserted}, Skipped dup: {skipped_dup}, No match: {skipped_no_match}")
        LoggingService.log_task_complete(log_id=log_entry.id, items_processed=len(items), items_found=inserted, items_skipped=skipped_dup + skipped_no_match)
        return {"status": "done", "fetched": len(items), "inserted": inserted, "skipped": skipped_dup, "skippedNoMatch": skipped_no_match}
    except Exception as e:
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise
    finally:
        if 'alert_service' in locals():
            await alert_service.close()
        db.close()


@celery_app.task(name="app.workers.tasks.scrape_tender_mc")
def scrape_tender_mc() -> dict:
    """Scrape tenders from tender.mc.uz"""
    return asyncio.run(_scrape_tender_mc_impl())


async def _scrape_e_auksion_impl() -> dict:
    """Scrape investment lots from e-auksion.uz (Async Implementation)"""
    task_name = "scrape_e_auksion"
    source = "E_AUKSION"
    
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    db = SessionLocal()
    
    try:
        if not is_source_enabled(db, source):
            db.close()
            return {"status": "skipped", "message": "Source disabled"}

        scraper = EAuksionScraper()
        items = await scraper.run()
        
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        keyword_dtos = [KeywordDTO(id=str(k.id), phrase=k.phrase, is_blacklist=k.is_blacklist) for k in keywords]
        
        keyword_filter = KeywordFilterService()
        alert_service = TelegramAlertService()
        crm_service = get_crm_service()
        
        inserted = 0
        skipped_dup = 0
        skipped_no_match = 0
        for it in reversed(items[:100]):
            title_hash = sha256(normalize_text(it.title))
            compound_hash = sha256(f"{source}:{it.external_id}:{title_hash}")
            
            if is_duplicate(db, source, it.external_id, it.url, it.title, title_hash, compound_hash):
                skipped_dup += 1
                continue

            # Keyword matching BEFORE DB insert — only save matched tenders
            matched_ids = keyword_filter.match(it.title, keyword_dtos)
            matched_kws = [k for k in keywords if str(k.id) in matched_ids]

            if not matched_ids:
                skipped_no_match += 1
                continue

            tender = Tender(
                source=source,
                external_id=it.external_id,
                title=it.title,
                amount=it.amount,
                region=it.region,
                url=it.url,
                organizer_name=it.organizer_name,
                organizer_phone=it.organizer_phone,
                title_hash=title_hash,
                compound_hash=compound_hash
            )
            try:
                db.add(tender)
                db.flush()

                for kw_id in matched_ids:
                    db.add(TenderKeywordMatch(tender_id=tender.id, keyword_id=kw_id))

                db.commit()
                inserted += 1

                try:
                    await alert_service.send_tender_alert(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send Telegram alert: {e}")

                try:
                    await crm_service.send_lead(tender, matched_kws)
                except Exception as e:
                    print(f"Failed to send CRM lead: {e}")
            except Exception as insert_error:
                db.rollback()
                skipped_dup += 1
                print(f"Failed to insert/commit tender due to DB error (likely duplicate): {insert_error}")
                LoggingService.log_duplicate_skipped(
                    task_name=task_name,
                    source=source,
                    tender_title=it.title,
                    message=f"Duplicate skipped due to database constraint: {insert_error}"
                )
        
        if is_google_sheets_enabled(db) and inserted > 0:
            try:
                get_google_sheets_service().export_new_tenders(limit=50)
            except Exception: pass
        
        print(f"[SUCCESS] [E-AUKSION] Processed: {len(items)}, Matched & Saved: {inserted}, Skipped dup: {skipped_dup}, No match: {skipped_no_match}")
        LoggingService.log_task_complete(log_id=log_entry.id, items_processed=len(items), items_found=inserted, items_skipped=skipped_dup + skipped_no_match)
        return {"status": "done", "fetched": len(items), "inserted": inserted, "skipped": skipped_dup, "skippedNoMatch": skipped_no_match}
    except Exception as e:
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise
    finally:
        if 'alert_service' in locals():
            await alert_service.close()
        db.close()


@celery_app.task(name="app.workers.tasks.scrape_e_auksion")
def scrape_e_auksion() -> dict:
    """Scrape investment lots from e-auksion.uz"""
    return asyncio.run(_scrape_e_auksion_impl())


@celery_app.task(name="app.workers.tasks.process_winners")
def process_winners() -> dict:
    """Check recently finished tenders and extract winners"""
    task_name = "process_winners"
    source = "SYSTEM"
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    try:
        service = get_winner_parser_service()
        result = asyncio.run(
            service.parse_completed_tenders(
                days_back=settings.WINNER_DAYS_BACK,
                batch_limit=settings.WINNER_BATCH_LIMIT,
                api_delay=settings.WINNER_API_DELAY_SECONDS,
            )
        )
        LoggingService.log_task_complete(
            log_id=log_entry.id, 
            items_processed=result.get("tenders_checked", 0), 
            items_found=result.get("winners_parsed", 0)
        )
        return result
    except Exception as e:
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise


@celery_app.task(name="app.workers.tasks.enrich_companies")
def enrich_companies() -> dict:
    """Find contacts for companies found in winner parser"""
    task_name = "enrich_companies"
    source = "SYSTEM"
    log_entry = LoggingService.log_task_start(task_name=task_name, source=source)
    try:
        service = get_company_enrichment_service()
        result = asyncio.run(service.enrich_multiple_companies(limit=10))
        LoggingService.log_task_complete(
            log_id=log_entry.id, 
            items_processed=result.get("companies_processed", 0), 
            items_found=result.get("enriched_successfully", 0)
        )
        return result
    except Exception as e:
        LoggingService.log_task_failed(log_id=log_entry.id, error=e)
        raise
