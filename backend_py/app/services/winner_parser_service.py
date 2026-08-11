"""
Winner parser service for Tender Intelligence Platform
Extracts winner information from completed tenders and builds company profiles
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.tender import Tender
from app.models.winner import Winner, CompanyProfile
from app.services.logging_service import LoggingService
from app.utils.inn import normalize_inn, is_placeholder_company_name
from app.utils.uzex_trade_id import resolve_uzex_trade_id

# All UZEX etender source labels used in DB over time
UZEX_WINNER_SOURCES = ("UZEX", "UZEX_ETENDER", "ETENDER.UZEX.UZ")

# status_id on etender.uzex.uz: 9=winner, 10=contract, 11=completed
WINNER_STATUS_IDS = {9, 10, 11}

DEAL_STATUS_WINNER_KEYWORDS = (
    "g'olib",
    "golib",
    "amalga oshgan",
    "имзолан",
    "подписан",
    "победител",
    "winner",
)


@dataclass
class WinnerInfo:
    """Data structure for parsed winner information"""
    tender_id: str
    tender_url: str
    source: str
    company_name: str
    company_inn: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_website: Optional[str] = None
    tender_amount: Optional[str] = None
    tender_date: Optional[datetime] = None
    winner_announcement_date: Optional[datetime] = None
    contract_details: Optional[str] = None
    competition_type: Optional[str] = None


class WinnerParserService:
    """Service for parsing tender winners"""

    def _query_tenders_without_winners(
        self,
        db: Session,
        *,
        days_back: int,
        batch_limit: int,
    ) -> List[Tender]:
        """All UZEX tenders that have no Winner row yet."""
        q = (
            db.query(Tender)
            .filter(Tender.source.in_(UZEX_WINNER_SOURCES))
            .outerjoin(Winner, Winner.tender_id == Tender.id)
            .filter(Winner.id.is_(None))
            .filter(Tender.external_id.isnot(None))
            .order_by(Tender.created_at.desc())
        )

        if days_back > 0:
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            q = q.filter(Tender.created_at >= cutoff)

        if batch_limit > 0:
            q = q.limit(batch_limit)

        return q.all()

    async def parse_completed_tenders(
        self,
        days_back: int = 365,
        batch_limit: int = 0,
        api_delay: float = 0.15,
    ) -> Dict[str, Any]:
        """Check every pending UZEX tender against etender API; save winners."""
        from app.clients.uzex_etender_api import UzexEtenderApiClient

        db = SessionLocal()
        api = None
        try:
            tenders_to_check = self._query_tenders_without_winners(
                db,
                days_back=days_back,
                batch_limit=batch_limit,
            )

            print(
                f"🔍 Winner check: {len(tenders_to_check)} tenders "
                f"(days_back={days_back or 'all'}, limit={batch_limit or 'none'})"
            )

            winners_parsed = 0
            still_open = 0
            errors = 0

            api = UzexEtenderApiClient()
            print("📥 Loading DealsList index (completed deals with provider names)...")
            deals_index = await api.build_deals_index()
            print(f"📥 DealsList: {len(deals_index)} trades indexed")

            for i, tender in enumerate(tenders_to_check, 1):
                try:
                    winner_info = await self.parse_tender_winner(
                        tender, api, deals_index=deals_index
                    )
                    if winner_info:
                        saved = await self.save_winner(winner_info)
                        if saved:
                            winners_parsed += 1
                            print(
                                f"✅ [{i}/{len(tenders_to_check)}] "
                                f"{winner_info.company_name} "
                                f"(trade {tender.external_id})"
                            )
                    else:
                        still_open += 1

                except Exception as e:
                    errors += 1
                    print(f"❌ [{i}/{len(tenders_to_check)}] {tender.id}: {e}")
                    LoggingService.log_task_failed(
                        log_id="winner_parser",
                        error=e,
                        message=f"Failed to parse winner for tender {tender.id}",
                        details={
                            "tender_id": tender.id,
                            "external_id": tender.external_id,
                            "tender_title": tender.title,
                        },
                    )

                if api_delay > 0 and i < len(tenders_to_check):
                    await asyncio.sleep(api_delay)

            result = {
                "tenders_checked": len(tenders_to_check),
                "winners_parsed": winners_parsed,
                "still_open": still_open,
                "errors": errors,
                "days_back": days_back,
                "success_rate": (
                    (winners_parsed / len(tenders_to_check)) * 100
                    if tenders_to_check
                    else 0
                ),
            }

            print(f"📊 Winner parsing completed: {result}")
            return result

        finally:
            if api:
                try:
                    await api.close()
                except Exception:
                    pass
            db.close()

    @staticmethod
    def _trade_has_winner(trade_data: dict[str, Any], deal: Optional[dict[str, Any]] = None) -> bool:
        """True if trade has a confirmed winner (DealsList or final status on GetTrade)."""
        if deal and (deal.get("provider_name") or deal.get("provider_inn")):
            return True

        status_id = trade_data.get("status_id")
        deal_status = (trade_data.get("deal_status") or "").lower()
        has_winner_status = status_id in WINNER_STATUS_IDS
        has_winner_deal_text = any(kw in deal_status for kw in DEAL_STATUS_WINNER_KEYWORDS)

        if has_winner_status and (has_winner_deal_text or trade_data.get("seller_id")):
            return True
        if trade_data.get("seller_id") and has_winner_deal_text:
            return True

        return False

    @staticmethod
    def _winner_fields_from_deal(deal: dict[str, Any]) -> dict[str, Any]:
        return {
            "company_name": (
                deal.get("provider_name")
                or deal.get("seller_name")
                or deal.get("company_name")
            ),
            "company_inn": normalize_inn(
                deal.get("provider_inn")
                or deal.get("seller_tin")
                or deal.get("tin")
            ) or None,
            "company_phone": (
                deal.get("provider_phone")
                or deal.get("phone")
                or deal.get("mobile")
            ),
            "winner_amount": str(
                deal.get("deal_cost")
                or deal.get("amount")
                or deal.get("cost")
                or ""
            ) or None,
        }

    @staticmethod
    def winner_info_from_deal(tender: Tender, deal: dict[str, Any]) -> Optional[WinnerInfo]:
        """Winner name / INN / phone straight from DealsList (no GetTrade)."""
        fields = WinnerParserService._winner_fields_from_deal(deal)
        company_name = (fields.get("company_name") or "").strip()
        if not company_name or is_placeholder_company_name(company_name):
            return None

        company_inn = fields.get("company_inn")
        phone = fields.get("company_phone")
        if phone:
            phone = str(phone).strip()

        return WinnerInfo(
            tender_id=tender.id,
            tender_url=tender.url,
            source=tender.source,
            company_name=company_name,
            company_inn=company_inn,
            company_phone=phone,
            tender_amount=fields.get("winner_amount"),
            tender_date=tender.created_at,
            winner_announcement_date=datetime.utcnow(),
            competition_type="Uzex Etender",
        )

    @staticmethod
    def _winner_fields_from_trade(trade_data: dict[str, Any]) -> dict[str, Any]:
        parts = [
            trade_data.get("delivering_region_name"),
            trade_data.get("delivering_district_name"),
            trade_data.get("delivering_address"),
        ]
        addr = ", ".join(p for p in parts if p) or None

        return {
            "company_name": (
                trade_data.get("seller_name")
                or trade_data.get("winner_name")
                or trade_data.get("participant_name")
            ),
            "company_inn": normalize_inn(trade_data.get("seller_tin")) or None,
            "company_phone": trade_data.get("delivering_phone"),
            "company_address": addr,
            "winner_amount": str(
                trade_data.get("deal_cost")
                or trade_data.get("start_cost")
                or ""
            ) or None,
        }

    @staticmethod
    def _winner_fields_from_winners_list(winners_list: list) -> dict[str, Any]:
        if not winners_list or not isinstance(winners_list[0], dict):
            return {}
        w = winners_list[0]
        return {
            "company_name": (
                w.get("company_name")
                or w.get("name")
                or w.get("seller_name")
            ),
            "company_inn": normalize_inn(w.get("tin") or w.get("seller_tin")) or None,
            "company_phone": w.get("phone") or w.get("mobile"),
            "company_address": w.get("address"),
            "winner_amount": str(w.get("amount") or w.get("cost") or "") or None,
        }

    async def parse_tender_winner(
        self,
        tender: Tender,
        api=None,
        *,
        deals_index: dict[int, dict[str, Any]] | None = None,
    ) -> Optional[WinnerInfo]:
        """Parse winner from GetTrade + DealsList (provider_name lives in DealsList)."""
        from app.clients.uzex_etender_api import UzexEtenderApiClient

        close_api = False
        try:
            trade_id = resolve_uzex_trade_id(tender.external_id, tender.url)
            if trade_id is None:
                return None

            if api is None:
                api = UzexEtenderApiClient()
                close_api = True

            deal = await api.get_deal_winner(trade_id, deals_index=deals_index)

            trade_data = await api.trade_details(trade_id)

            if not self._trade_has_winner(trade_data, deal):
                return None

            fields: dict[str, Any] = {}

            if deal:
                fields.update(self._winner_fields_from_deal(deal))

            try:
                winners_list = await api.trade_winners(trade_id)
                for k, v in self._winner_fields_from_winners_list(winners_list).items():
                    if v and not fields.get(k):
                        fields[k] = v
            except Exception:
                pass

            for k, v in self._winner_fields_from_trade(trade_data).items():
                if v and not fields.get(k):
                    fields[k] = v

            company_name = (fields.get("company_name") or "").strip()
            company_inn = normalize_inn(
                fields.get("company_inn") or trade_data.get("seller_tin")
            ) or None

            if not company_name or is_placeholder_company_name(company_name):
                print(
                    f"ℹ️  Skip trade {trade_id}: winner status OK but no company name in DealsList/API"
                )
                return None

            return WinnerInfo(
                tender_id=tender.id,
                tender_url=tender.url,
                source=tender.source,
                company_name=company_name,
                company_inn=company_inn,
                company_address=fields.get("company_address"),
                company_phone=fields.get("company_phone"),
                company_email=None,
                tender_amount=fields.get("winner_amount"),
                tender_date=tender.created_at,
                winner_announcement_date=datetime.utcnow(),
                competition_type=trade_data.get("type_name") or "Uzex Etender",
            )

        except Exception as e:
            print(f"❌ Real winner parsing failed for tender {tender.id}: {e}")
            return None
        finally:
            if close_api and api:
                try:
                    await api.close()
                except Exception:
                    pass

    async def save_winner(self, winner_info: WinnerInfo) -> bool:
        """Save winner information to database"""
        db = SessionLocal()
        try:
            existing = db.query(Winner).filter(
                Winner.source == winner_info.source,
                Winner.tender_id == winner_info.tender_id
            ).first()

            if existing:
                print(f"⚠️  Winner already exists for tender {winner_info.tender_id}")
                return False

            winner = Winner(
                source=winner_info.source,
                tender_id=winner_info.tender_id,
                tender_url=winner_info.tender_url,
                company_name=winner_info.company_name,
                company_inn=winner_info.company_inn,
                company_address=winner_info.company_address,
                company_phone=winner_info.company_phone,
                company_email=winner_info.company_email,
                company_website=winner_info.company_website,
                tender_amount=winner_info.tender_amount,
                tender_date=winner_info.tender_date,
                winner_announcement_date=winner_info.winner_announcement_date,
                contract_details=winner_info.contract_details,
                competition_type=winner_info.competition_type
            )

            db.add(winner)
            db.flush()

            await self.update_company_profile(winner_info, db)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"❌ Error saving winner: {e}")
            return False
        finally:
            db.close()

    async def update_company_profile(self, winner_info: WinnerInfo, db: Session) -> None:
        """Update or create company profile based on winner information"""
        try:
            profile = None

            if winner_info.company_inn:
                profile = db.query(CompanyProfile).filter(
                    CompanyProfile.company_inn == winner_info.company_inn
                ).first()

            if not profile:
                profile = db.query(CompanyProfile).filter(
                    CompanyProfile.company_name == winner_info.company_name
                ).first()

            if profile:
                profile.total_wins += 1

                if winner_info.company_phone and not profile.phone:
                    profile.phone = winner_info.company_phone
                if winner_info.company_email and not profile.email:
                    profile.email = winner_info.company_email
                if winner_info.company_website and not profile.website:
                    profile.website = winner_info.company_website
                if winner_info.company_address and not profile.address:
                    profile.address = winner_info.company_address

                profile.last_win_date = winner_info.winner_announcement_date or datetime.utcnow()

                if not profile.first_win_date:
                    profile.first_win_date = profile.last_win_date

            else:
                profile = CompanyProfile(
                    company_name=winner_info.company_name,
                    company_inn=winner_info.company_inn,
                    phone=winner_info.company_phone,
                    email=winner_info.company_email,
                    website=winner_info.company_website,
                    address=winner_info.company_address,
                    total_wins=1,
                    first_win_date=winner_info.winner_announcement_date or datetime.utcnow(),
                    last_win_date=winner_info.winner_announcement_date or datetime.utcnow()
                )
                db.add(profile)

            print(f"📝 Updated company profile: {winner_info.company_name}")

        except Exception as e:
            print(f"❌ Error updating company profile: {e}")

    def get_top_companies(self, limit: int = 20, days_back: int = 90) -> List[Dict[str, Any]]:
        """Get top companies by number of wins"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            top_companies = (
                db.query(Winner)
                .filter(Winner.winner_announcement_date >= cutoff_date)
                .group_by(Winner.company_name, Winner.company_inn)
                .all()
            )

            company_stats = {}
            for winner in top_companies:
                key = (winner.company_name, winner.company_inn)
                if key not in company_stats:
                    company_stats[key] = {
                        'company_name': winner.company_name,
                        'company_inn': winner.company_inn,
                        'wins': 0,
                        'total_amount': 0,
                        'last_win': None,
                        'first_win': None
                    }

                stats = company_stats[key]
                stats['wins'] += 1

                if winner.tender_amount:
                    try:
                        amount = self._parse_amount(winner.tender_amount)
                        stats['total_amount'] += amount
                    except Exception:
                        pass

                if winner.winner_announcement_date:
                    if not stats['last_win'] or winner.winner_announcement_date > stats['last_win']:
                        stats['last_win'] = winner.winner_announcement_date
                    if not stats['first_win'] or winner.winner_announcement_date < stats['first_win']:
                        stats['first_win'] = winner.winner_announcement_date

            sorted_companies = sorted(
                company_stats.values(),
                key=lambda x: x['wins'],
                reverse=True
            )[:limit]

            return sorted_companies

        finally:
            db.close()

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0

        cleaned = re.sub(r'[^\d.]', '', amount_str)

        try:
            return float(cleaned)
        except Exception:
            return 0.0

    def get_winner_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get winner parsing statistics"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            total_winners = (
                db.query(Winner)
                .filter(Winner.winner_announcement_date >= cutoff_date)
                .count()
            )

            unique_companies = (
                db.query(Winner.company_inn)
                .filter(Winner.winner_announcement_date >= cutoff_date)
                .filter(Winner.company_inn.isnot(None))
                .distinct()
                .count()
            )

            competition_types = (
                db.query(Winner.competition_type,
                         func.count(Winner.id).label('count'))
                .filter(Winner.winner_announcement_date >= cutoff_date)
                .filter(Winner.competition_type.isnot(None))
                .group_by(Winner.competition_type)
                .all()
            )

            pending = self._query_tenders_without_winners(
                db, days_back=days_back, batch_limit=0
            )

            return {
                "total_winners": total_winners,
                "unique_companies": unique_companies,
                "period_days": days_back,
                "pending_checks": len(pending),
                "competition_types": [
                    {"type": ct[0], "count": ct[1]}
                    for ct in competition_types
                ],
                "average_wins_per_company": (
                    total_winners / unique_companies
                    if unique_companies > 0 else 0
                )
            }

        finally:
            db.close()


_winner_parser_service = None


def get_winner_parser_service() -> WinnerParserService:
    """Get or create winner parser service instance"""
    global _winner_parser_service
    if _winner_parser_service is None:
        _winner_parser_service = WinnerParserService()
    return _winner_parser_service
