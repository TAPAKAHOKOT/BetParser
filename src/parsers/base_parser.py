import asyncio
from config.parser import ParserConfig
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, PlaywrightContextManager
from playwright_stealth import stealth_async
from dataclasses import dataclass, field, asdict
from abc import abstractmethod


@dataclass
class MatchData:
    home_name: str
    away_name: str

    home_score: float
    away_score: float


@dataclass
class PageData:
    name: str = None
    selector: str = None
    page: Page = None

    matches_data: list[MatchData] = field(default_factory=list)


class BaseParser:
    use_stealth: bool = True

    _main_page: Page
    _live_page: Page
    _sports_pages: dict[str:PageData] = {}
    _mathes_pages: dict[str:PageData] = {}

    def __init__(self):
        self.config = ParserConfig()

    async def _get_browser(self, p: PlaywrightContextManager) -> Browser:
        """Создание браузер для дальнейшего парсера"""
        return await p.chromium.launch(headless=self.config.headless)

    async def _get_context(self, browser: Browser) -> BrowserContext:
        """Установка контекста для иммитации пользователя"""
        return await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Toronto",
            viewport={"width": 1280, "height": 720},
        )

    async def _wait(self, page: Page):
        """Ожидание загрузки страницы"""
        if loader_selector := self.config.selectors.get("loader"):
            await page.wait_for_selector(loader_selector, state="hidden", timeout=1_000)
        else:
            await page.wait_for_load_state("load")

    async def _open_tab_for_selector(context: BrowserContext, base_url: str, selector: str, text_selector: str = None):
        """Открытие страницы в новой вкладке по клику на селектор"""
        new_page = await context.new_page()
        await new_page.goto(base_url)

        name = None
        if text_selector is not None:
            container = await new_page.query_selector(selector)

            if container:
                text_container = await container.query_selector(text_selector)
                if text_container:
                    name = await text_container.text_content()

        await new_page.click(selector)

        return PageData(
            name=name,
            selector=selector,
            page=new_page,
        )

    async def _open_main_page(self, context: BrowserContext) -> Page:
        """Открытие главной страницы"""
        page = await context.new_page()
        if self.use_stealth:
            await stealth_async(page)

        await page.goto(
            self.config.url,
            wait_until="load",
        )
        await self._wait(page)
        return page

    async def _opex_live_page(self, page: Page) -> Page:
        """Переход к странице live"""
        if btn_selector := self.config.selectors.get("live_btn"):
            await page.click(btn_selector)
            await self._wait(page)
        return page

    @abstractmethod
    async def _collect_match_data(self, page: Page) -> MatchData:
        """Сбор данных матча, нужно переопределять для каждого сайта"""
        ...

    async def _parse_sport_matches(self, sport_page_data: PageData) -> list[MatchData]:
        """Парсинг каждого live матча нужного спорта"""
        mathces_selector = self.config.selectors.get("required_sports", {}).get(
            sport_page_data.selector,
            None,
        )

        if mathces_selector is None or sport_page_data.page is None:
            return []

        matches_data = []
        for match in await sport_page_data.page.query_selector_all(mathces_selector):
            await match.click()

            matches_data.append(self._collect_match_data())

            async with sport_page_data.page.expect_navigation():
                await sport_page_data.page.go_back()

    async def parse_live(self):
        """Парсинг live"""
        if self.config.url is None:
            raise AttributeError("Site url is not set")

        async with async_playwright() as p:
            if (self._main_page is None or self._main_page.is_closed()) and (
                self._live_page is None or self._live_page.is_closed()
            ):
                browser = await self._get_browser(p)
                context = await self._get_context(browser)

                self._main_page = await self._open_main_page(context)

            if self._live_page is None or self._live_page.is_closed():
                self._live_page = await self._opex_live_page(self._main_page)

            # Open/reopen tab for each sport
            sports_selectors = [
                sport
                for sport in self.config.selectors.get("required_sports", {}).keys()
                if (
                    sport not in self._mathes_pages
                    or self._sports_pages.get(sport) is None
                    or self._sports_pages[sport].page is None
                    or self._sports_pages[sport].page.is_closed()
                )
            ]
            tasks = []
            for selector in sports_selectors:
                task = asyncio.create_task(
                    self._open_tab_for_selector(
                        context,
                        self._live_page.url,
                        selector,
                        self.config.selectors.get("sport_text"),
                    )
                )
                tasks.append(task)
            sports_pages_data = await asyncio.gather(*tasks)

            for selector, page_data in zip(sports_selectors, sports_pages_data):
                self._sports_pages[selector] = page_data

            # Open/reopen tab for each match
            for selector, sport_page_data in self._sports_pages.items():
                sport_page_data.matches_data = self._parse_sport_matches(sport_page_data)

            result_data = {}
            for sport in self._sports_pages:
                result_data[sport.name] = [asdict(match_data) for match_data in self._sports_pages.matches_data]

        return {
            "url": self.config.url,
            "data": result_data,
        }
