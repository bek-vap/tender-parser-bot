from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import logging

from app.core.config import settings
import asyncio
from app.scrapers.base import BaseScraper, ScraperOptions
import json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TradeListItem:
    id: int
    display_no: str | None
    name: str
    start_date: str | None
    end_date: str | None
    cost: float | None
    seller_name: str | None
    seller_tin: str | None
    region_name: str | None
    district_name: str | None
    currency_name: str | None


class UzexEtenderApiClient:
    BASE_URL = "https://apietender.uzex.uz"
    TRADE_LIST_PATH = "/api/common/TradeList"

    def __init__(self) -> None:
        # Lazy init: don't create AsyncClient here — it must be created
        # inside an active event loop (i.e. inside an async function).
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return (and lazily create) the shared async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def trade_list(self, *, type_id: int, from_: int, to: int, system_id: int = 0) -> list[TradeListItem]:
        url = f"{self.BASE_URL}{self.TRADE_LIST_PATH}"

        headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://etender.uzex.uz",
            "referer": "https://etender.uzex.uz/",
            "language": "uzb",
            "user-agent": settings.UZEX_USER_AGENT,
        }

        if settings.UZEX_VALIDATION:
            headers["validation"] = settings.UZEX_VALIDATION

        payload = {
            "TypeId": type_id,
            "From": from_,
            "To": to,
            "System_Id": system_id,
        }

        resp = await self._get_client().post(url, headers=headers, json=payload)
        resp.raise_for_status()

        data: Any = resp.json()
        if not isinstance(data, list):
            raise ValueError(f"Unexpected response type: {type(data)}")

        items: list[TradeListItem] = []
        for x in data:
            if not isinstance(x, dict):
                continue
            items.append(
                TradeListItem(
                    id=int(x.get("id")),
                    display_no=(x.get("display_no") or None),
                    name=str(x.get("name") or ""),
                    start_date=(x.get("start_date") or None),
                    end_date=(x.get("end_date") or None),
                    cost=(float(x["cost"]) if x.get("cost") is not None else None),
                    seller_name=(x.get("seller_name") or None),
                    seller_tin=(str(x.get("seller_tin")) if x.get("seller_tin") is not None else None),
                    region_name=(x.get("region_name") or None),
                    district_name=(x.get("district_name") or None),
                    currency_name=(x.get("currency_name") or None),
                )
            )

        return items

    async def trade_details(self, trade_id: int) -> dict[str, Any]:
        """Fetch full details for a specific trade, including winner info if available"""
        url = f"{self.BASE_URL}/api/common/GetTrade/{trade_id}/0"
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://etender.uzex.uz",
            "referer": "https://etender.uzex.uz/",
            "language": "uzb",
            "user-agent": settings.UZEX_USER_AGENT,
        }
        
        resp = await self._get_client().get(url, headers=headers)
        resp.raise_for_status()
        
        return resp.json()

    async def trade_winners(self, trade_id: int) -> list[dict[str, Any]]:
        """Fetch winner information for a specific trade.
        NOTE: This endpoint returns 404 for most trades. Use get_deal_winner() instead."""
        url = f"{self.BASE_URL}/api/common/GetWinners"
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://etender.uzex.uz",
            "referer": "https://etender.uzex.uz/",
            "language": "uzb",
            "user-agent": settings.UZEX_USER_AGENT,
        }
        
        params = {"tradeId": trade_id}
        
        resp = await self._get_client().get(url, headers=headers, params=params)
        resp.raise_for_status()
        
        data = resp.json()
        return data if isinstance(data, list) else []

    async def deals_list(self, from_: int = 1, to: int = 200) -> list[dict[str, Any]]:
        """Fetch list of completed deals from DealsList API.
        Each item has: trade_id, provider_name, provider_inn, deal_cost, customer_name, etc.
        This is the endpoint the frontend uses for 'Amalga oshgan bitimlar'."""
        url = f"{self.BASE_URL}/api/common/DealsList"

        headers = {
            "accept": "application/json",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://etender.uzex.uz",
            "referer": "https://etender.uzex.uz/",
            "language": "uzb",
            "user-agent": settings.UZEX_USER_AGENT,
        }

        payload = {
            "From": from_,
            "To": to,
            "currencyId": None,
            "System_Id": 0,
        }

        resp = await self._get_client().post(url, headers=headers, json=payload)
        resp.raise_for_status()

        data = resp.json()
        return data if isinstance(data, list) else []

    async def build_deals_index(
        self,
        *,
        page_size: int = 500,
        max_pages: int = 50,
    ) -> dict[int, dict[str, Any]]:
        """Load DealsList pages once and index by trade_id (provider_name, inn, cost)."""
        index: dict[int, dict[str, Any]] = {}
        for page in range(max_pages):
            from_ = page * page_size + 1
            to_ = from_ + page_size - 1
            try:
                deals = await self.deals_list(from_=from_, to=to_)
            except Exception as e:
                logger.warning("DealsList page %s failed: %s", page + 1, e)
                break
            if not deals:
                break
            for deal in deals:
                if not isinstance(deal, dict):
                    continue
                tid = deal.get("trade_id")
                if tid is not None:
                    index[int(tid)] = deal
            if len(deals) < page_size:
                break
        logger.info("DealsList index: %s trades", len(index))
        return index

    async def get_deal_winner(
        self,
        trade_id: int,
        deals_index: dict[int, dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """Winner row from DealsList (provider_name, provider_inn, deal_cost)."""
        if deals_index is not None:
            hit = deals_index.get(trade_id)
            if hit is not None:
                return hit
        return await self.find_deal_by_trade_id(trade_id)

    async def find_deal_by_trade_id(
        self,
        trade_id: int,
        *,
        page_size: int = 500,
        max_pages: int = 40,
    ) -> dict[str, Any] | None:
        """Scan DealsList pages until trade_id is found."""
        for page in range(max_pages):
            from_ = page * page_size + 1
            to_ = from_ + page_size - 1
            try:
                deals = await self.deals_list(from_=from_, to=to_)
            except Exception as e:
                logger.warning("DealsList lookup page %s failed: %s", page + 1, e)
                break
            if not deals:
                break
            for deal in deals:
                if isinstance(deal, dict) and deal.get("trade_id") == trade_id:
                    return deal
            if len(deals) < page_size:
                break
        return None


class UzexEtenderBrowserClient(BaseScraper):
    """
    Stable browser-based client for Uzex Etender.
    Used when direct API requests are blocked by Cloudflare/Anti-bot.
    """
    
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        super().__init__(opts)
        self.base_url = "https://etender.uzex.uz"

    async def fetch_trade_list(self, type_id: int = 1, page_size: int = 200) -> list[TradeListItem]:
        """Fetch trade list using Playwright by intercepting API responses or simulating UI"""
        await self.init()
        try:
            # We use the public URL where the tenders are listed
            # type_id 1 = Tender, 2 = Selection
            target_url = f"{self.base_url}/ru/lots/category/{type_id}"
            
            logger.info(f"Navigating to {target_url} using stealth browser")
            
            # Setup response interception to capture API data
            trade_data = []
            
            async def handle_response(response):
                if "TradeList" in response.url and response.status == 200:
                    try:
                        text = await response.text()
                        if text:
                            trade_data.extend(json.loads(text))
                    except Exception as e:
                        logger.debug(f"Error parsing intercepted response: {e}")

            self.page.on("response", handle_response)
            
            await self.page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Wait a bit for JS to populate the list and API to be called
            await self.random_delay(3, 5)
            
            if not trade_data:
                logger.warning("No TradeList data intercepted. System might be using a different API or blocking.")
            
            items: list[TradeListItem] = []
            for x in trade_data:
                if not isinstance(x, dict): continue
                try:
                    items.append(TradeListItem(
                        id=int(x.get("id")),
                        display_no=x.get("display_no"),
                        name=str(x.get("name") or ""),
                        start_date=x.get("start_date"),
                        end_date=x.get("end_date"),
                        cost=float(x["cost"]) if x.get("cost") is not None else None,
                        seller_name=x.get("seller_name"),
                        seller_tin=str(x.get("seller_tin")) if x.get("seller_tin") is not None else None,
                        region_name=x.get("region_name"),
                        district_name=x.get("district_name"),
                        currency_name=x.get("currency_name"),
                    ))
                except Exception: continue
                
            return items
        finally:
            await self.close()
