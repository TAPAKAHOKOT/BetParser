from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from playwright.async_api import async_playwright

from config.log import logger
from config.parser import ParserConfig

parser_conf = ParserConfig()

app = FastAPI()

logger.info(f"Starting app: SITE_URL={parser_conf.url}, HEADLESS_MODE={parser_conf.headless}")


@app.get("/")
async def read_root():
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            docstring = route.endpoint.__doc__ or ""
            routes.append(
                {
                    "path": route.path,
                    "description": docstring.strip(),
                    "methods": list(route.methods),
                }
            )
    return routes


@app.get("/parse/live")
async def parse_live():
    """Parse live data"""
    if parser_conf.url is None:
        raise HTTPException(status_code=500, detail="Site url is not set")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(parser_conf.url)

        # Возьмём HTML-код
        content = await page.content()

        # Закрываем браузер
        await browser.close()

    # Возвращаем часть HTML-кода (или весь)
    return {"url": parser_conf.url, "content_snippet": content[:500]}
