from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models.guide import EXPLORATION_CATEGORIES, PVP_CATEGORIES, DIFFICULTY_LEVELS

import pathlib

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from models.guide import EXPLORATION_CATEGORIES, PVP_CATEGORIES, DIFFICULTY_LEVELS

pages = APIRouter()
_tpl_dir = pathlib.Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_tpl_dir)), auto_reload=True)


def _render(name: str, context: dict) -> HTMLResponse:
    template = _jinja_env.get_template(name)
    return HTMLResponse(template.render(**context))


@pages.get("/")
async def index(request: Request) -> HTMLResponse:
    return _render("index.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })


@pages.get("/exploration")
async def exploration_page(request: Request) -> HTMLResponse:
    return _render("index.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "active_tab": "exploration",
    })


@pages.get("/pvp")
async def pvp_page(request: Request) -> HTMLResponse:
    return _render("index.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "active_tab": "pvp",
    })


@pages.get("/admin")
async def admin_page(request: Request) -> HTMLResponse:
    return _render("admin.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })
