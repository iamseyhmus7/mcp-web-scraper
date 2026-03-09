import asyncio
import random
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright


async def _apply_stealth(page) -> None:
    """
    playwright-stealth paketi yerine manuel stealth.
    WebDriver flag'ini gizler, gerçek tarayıcı gibi davranır.
    """
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr', 'en-US'] });
        window.chrome = { runtime: {} };
    """)


class BrowserPool:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._lock = None

    async def _init_browser(self):
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

    async def get_browser(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            if not self._browser:
                await self._init_browser()
            return self._browser

    @asynccontextmanager
    async def acquire(self):
        browser = await self.get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="tr-TR",
        )
        page = await context.new_page()

        # Manuel stealth — webdriver flag gizle
        await _apply_stealth(page)

        # İnsan gibi davran
        await page.mouse.move(
            random.randint(100, 300),
            random.randint(100, 300),
        )

        try:
            yield page
        finally:
            await context.close()

    async def close(self):
        if self._lock is None:
            return
        async with self._lock:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._browser = None
            self._playwright = None


# Global singleton
browser_pool = BrowserPool()