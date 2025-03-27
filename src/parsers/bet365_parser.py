from base_parser import BaseParser, MatchData
from playwright.async_api import Page


class Bet365Parser(BaseParser):
    async def _collect_match_data(self, page: Page) -> MatchData: ...
