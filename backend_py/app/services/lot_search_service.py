import asyncio
from typing import Optional, Dict, Any
from app.clients.uzex_etender_api import UzexEtenderApiClient
from app.utils.uzex_trade_id import resolve_uzex_trade_id
from app.scrapers.uzex_lot_scraper import UzexLotScraper

class LotSearchService:
    def __init__(self):
        self.uzex_client = UzexEtenderApiClient()

    async def search_lot_everywhere(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """Search for a lot ID (short, internal, or 14-digit display_no) — same as /check_inn."""
        print(f"[*] Searching for Lot: {lot_id}...")

        trade_id = resolve_uzex_trade_id(lot_id)
        if trade_id is None:
            return None

        try:
            details = await self.uzex_client.trade_details(trade_id)

            if details and (details.get('id') or details.get('display_no')):
                print(f"[+] Found on UZEX API!")

                title = None
                budget_products_raw = details.get("budget_products")
                if budget_products_raw:
                    try:
                        import json
                        products_list = json.loads(budget_products_raw)
                        if isinstance(products_list, list) and len(products_list) > 0:
                            first_prod = products_list[0]
                            title = first_prod.get("Product_Name") or first_prod.get("Description")
                    except Exception:
                        pass
                if not title:
                    title = details.get("addon_description") or details.get("technical_description") or f"Loyiha №{trade_id}"

                region = details.get("delivering_region_name")
                distr = details.get("delivering_district_name")
                region_str = f"{region}, {distr}" if (region and distr) else (region or distr)

                amount_str = "0.00 UZS"
                cost = details.get("start_cost")
                if cost is not None:
                    curr = details.get("currency_codeabc") or details.get("currency_name") or "UZS"
                    amount_str = f"{float(cost):,.2f} {curr}"

                langs_str = None
                langs_raw = details.get("languages")
                if langs_raw:
                    try:
                        import json
                        langs_list = json.loads(langs_raw) if isinstance(langs_raw, str) else langs_raw
                        if isinstance(langs_list, list):
                            langs_str = ", ".join([l.get("Name") for l in langs_list if l.get("Name")])
                    except Exception:
                        pass

                result = {
                    "source": "UZEX",
                    "id": details.get("display_no") or lot_id,
                    "title": title,
                    "amount": amount_str,
                    "region": region_str,
                    "organizer": details.get("customer_name"),
                    "organizer_inn": details.get("customer_tin"),
                    "phone": details.get("delivering_phone") or details.get("phone") or details.get("mobile"),
                    "email": details.get("email") or details.get("delivering_email"),
                    "payment_terms": details.get("payment_type_name") or "Oldindan to'lov",
                    "deposit": f"{details.get('pledge_value', '1')}%" if details.get('pledge_value') is not None else "1%",
                    "languages": langs_str,
                    "status": details.get("status_name"),
                    "status_id": details.get("status_id"),
                    "deal_status": details.get("deal_status"),
                    "registration_order": details.get("consider_procedure"),
                    "placement_deadline": details.get("end_date"),
                    "extra_info": details.get("addon_description") or details.get("technical_description"),
                    "organizer_address": details.get("delivering_address") or details.get("customer_street"),
                    "url": f"https://etender.uzex.uz/lot/{trade_id}",
                }

                return result
        except Exception as e:
            print(f"[-] UZEX API search failed: {e}")

        try:
            scraper = UzexLotScraper()
            scraped_data = await scraper.scrape_lot_details(str(trade_id))
            await scraper.close()
            if scraped_data.get('title'):
                print(f"[+] Found on UZEX Scraper!")
                scraped_data["source"] = "UZEX (Scraped)"
                return scraped_data
        except Exception as e:
            print(f"[-] UZEX Scraper failed: {e}")

        return None

    async def get_detailed_lot_info(self, lot_id: str) -> Optional[Dict[str, Any]]:
        """Deep scrape of lot info for the /check_inn command"""
        trade_id = resolve_uzex_trade_id(lot_id) or lot_id
        scraper = UzexLotScraper()
        try:
            return await scraper.scrape_lot_details(str(trade_id))
        finally:
            await scraper.close()

    async def close(self):
        await self.uzex_client.close()

# Global instance
_lot_search_service = None

def get_lot_search_service() -> LotSearchService:
    global _lot_search_service
    if _lot_search_service is None:
        _lot_search_service = LotSearchService()
    return _lot_search_service
