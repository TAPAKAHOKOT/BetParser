from fastapi import FastAPI
from fastapi.routing import APIRoute

from config.log import logger
from config.parser import ParserConfig
from src.parsers.bet365_parser import Bet365Parser

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


@app.get("/parse/live/")
async def parse_live():
    """Parse live data"""
    return await Bet365Parser().parse_live()
