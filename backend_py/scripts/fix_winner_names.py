#!/usr/bin/env python3
"""Backfill winner company_name and INN from DealsList; remove placeholder rows."""
import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.db.session import SessionLocal
from app.models.tender import Tender
from app.models.winner import Winner
from app.clients.uzex_etender_api import UzexEtenderApiClient
from app.utils.inn import normalize_inn, is_placeholder_company_name
from app.utils.uzex_trade_id import resolve_uzex_trade_id


async def main() -> None:
    db = SessionLocal()
    api = UzexEtenderApiClient()
    try:
        print("Loading DealsList index...")
        index = await api.build_deals_index()
        print(f"Indexed {len(index)} deals")

        winners = db.query(Winner).all()
        updated = 0
        deleted = 0

        for w in winners:
            tender = db.query(Tender).filter(Tender.id == w.tender_id).first()
            trade_id = None
            if tender:
                trade_id = resolve_uzex_trade_id(tender.external_id, tender.url)

            deal = index.get(trade_id) if trade_id else None
            pname = (deal.get("provider_name") or "").strip() if deal else ""
            pinn = normalize_inn(deal.get("provider_inn")) if deal else ""

            if is_placeholder_company_name(w.company_name):
                if pname:
                    w.company_name = pname
                    if pinn:
                        w.company_inn = pinn
                    updated += 1
                    print(f"  fixed: {pname} (trade {trade_id})")
                else:
                    db.delete(w)
                    deleted += 1
                    print(f"  deleted placeholder trade {trade_id}")
            elif pinn and not w.company_inn:
                w.company_inn = pinn
                updated += 1
            elif w.company_inn:
                norm = normalize_inn(w.company_inn)
                if norm != w.company_inn:
                    w.company_inn = norm
                    updated += 1

        db.commit()
        print(f"\nDone: updated={updated}, deleted={deleted}")
    finally:
        await api.close()
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
