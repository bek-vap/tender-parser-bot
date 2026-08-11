from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import Stealth
import asyncio
import random
from app.services.logging_service import LoggingService


@dataclass
class ScraperOptions:
    headless: bool = True


class BaseScraper:
    def __init__(self, opts: ScraperOptions | None = None) -> None:
        self.opts = opts or ScraperOptions()
        self._playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def init(self) -> None:
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.opts.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="ru-RU",
        )
        self.page = await self.context.new_page()
        await self.block_resources(self.page)
        await Stealth().apply_stealth_async(self.page)

    async def block_resources(self, page: Page, types=["image", "font", "media"]):
        """Block loading of certain resource types to save CPU and network bandwidth"""
        async def block(route):
            try:
                if route.request.resource_type in types:
                    await route.abort()
                else:
                    await route.continue_()
            except Exception:
                pass
        try:
            await page.route("**/*", block)
        except Exception:
            pass

    async def random_delay(self, min_s: float = 1.0, max_s: float = 3.0):
        """Random delay to mimic human behavior and avoid rate limits"""
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def detect_captcha(self, source: str):
        """Check if captcha is present on the page and log it if found"""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            ".g-recaptcha",
            "#captcha",
            "img[src*='captcha']",
            "text=hCaptcha",
            "text=Please verify you are a human"
        ]
        for selector in captcha_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    print(f"🚨 CAPTCHA detected on {source}!")
                    LoggingService.log_captcha_detected(
                        task_name=f"scrape_{source.lower()}",
                        source=source,
                        message=f"CAPTCHA detected using selector: {selector}"
                    )
                    return True
            except Exception:
                continue
        return False

    async def close(self) -> None:
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def run(self) -> None:
        raise NotImplementedError
