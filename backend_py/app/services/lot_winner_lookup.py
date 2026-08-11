"""Winner lookup for /check_inn lot view."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

from app.utils.inn import normalize_inn, is_placeholder_company_name
from app.utils.format_money import format_uzs_total, parse_amount_number

# etender.uzex.uz status_id: 9=winner, 10=protocol, 11=completed
_FINALIZED_STATUS_IDS = {9, 10, 11}

_FINALIZED_STATUS_KEYWORDS = (
    "bayonnoma",
    "shakllantirilgan",
    "amalga oshgan",
    "g'olib",
    "golib",
    "imzolan",
    "подписан",
    "победител",
    "yakunlangan",
    "tugallangan",
    "winner",
)


def is_lot_finalized(
    status_name: str | None,
    status_id: int | None = None,
) -> bool:
    """True when tender is finished / has a winner stage."""
    if status_id in _FINALIZED_STATUS_IDS:
        return True
    if not status_name:
        return False
    s = status_name.lower()
    return any(kw in s for kw in _FINALIZED_STATUS_KEYWORDS)


def _winner_from_deal(deal: dict[str, Any]) -> dict[str, Any] | None:
    name = (deal.get("provider_name") or "").strip()
    if not name or is_placeholder_company_name(name):
        return None
    phone = deal.get("provider_phone") or deal.get("phone") or deal.get("mobile")
    amount = deal.get("deal_cost") or deal.get("start_cost")
    return {
        "company_name": name,
        "inn": normalize_inn(deal.get("provider_inn")) or None,
        "phone": str(phone).strip() if phone else None,
        "amount": str(amount) if amount is not None else None,
    }


async def lookup_winner_for_trade(
    trade_id: int,
    tender: Any | None = None,
) -> dict[str, Any] | None:
    """Winner company from DealsList or GetTrade (provider_name)."""
    from app.clients.uzex_etender_api import UzexEtenderApiClient
    from app.services.winner_parser_service import get_winner_parser_service

    api = UzexEtenderApiClient()
    try:
        deal = await api.find_deal_by_trade_id(trade_id, max_pages=50)
        if deal:
            hit = _winner_from_deal(deal)
            if hit:
                return hit

        if tender is None:
            tender = SimpleNamespace(
                id="lot-check",
                source="UZEX",
                external_id=str(trade_id),
                url=f"https://etender.uzex.uz/lot/{trade_id}",
                title="",
                created_at=datetime.utcnow(),
            )

        parser = get_winner_parser_service()
        info = await parser.parse_tender_winner(tender, api)
        if not info:
            return None
        return {
            "company_name": info.company_name,
            "inn": info.company_inn,
            "phone": info.company_phone,
            "amount": info.tender_amount,
        }
    finally:
        await api.close()


def format_winner_amount(amount_raw: str | float | None) -> str:
    val = parse_amount_number(amount_raw)
    if val:
        return format_uzs_total(val)
    return str(amount_raw) if amount_raw else "—"
