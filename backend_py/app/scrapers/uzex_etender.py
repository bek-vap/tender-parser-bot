from __future__ import annotations

from dataclasses import dataclass

from app.scrapers.base import BaseScraper
from app.utils.rate_limit import RateLimiter


@dataclass
class ScrapedTender:
    source: str
    external_id: str | None
    title: str
    url: str


class UzexEtenderScraper(BaseScraper):
    def __init__(self, start_url: str) -> None:
        super().__init__()
        self.start_url = start_url
        self.rate = RateLimiter(min_interval_ms=1200)

    async def run(self) -> None:
        await self.init()
        try:
            assert self.page
            await self.page.goto(self.start_url, wait_until="domcontentloaded", timeout=60_000)
            # TODO: В боевой версии: либо парс DOM после рендера, либо лучше дергать API (TradeList)
            await self.rate.wait()
        finally:
            await self.close()
