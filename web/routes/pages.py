import pathlib
import re

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select

from core.database import async_session
from models.guide import (
    ExplorationGuide,
    PvpTip,
    EXPLORATION_CATEGORIES,
    PVP_CATEGORIES,
    DIFFICULTY_LEVELS,
)

pages = APIRouter()
_tpl_dir = pathlib.Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_tpl_dir)), auto_reload=True)


def _render(name: str, context: dict) -> HTMLResponse:
    template = _jinja_env.get_template(name)
    return HTMLResponse(template.render(**context))


def _get_video_embed(video_url: str) -> str:
    if not video_url:
        return ""
    if "bilibili.com" in video_url:
        m = re.search(r"[BVbv][a-zA-Z0-9]+", video_url)
        if m:
            return f"https://player.bilibili.com/player.html?bvid={m[0]}&autoplay=0"
    elif "youtube.com" in video_url or "youtu.be" in video_url:
        m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", video_url)
        if m:
            return f"https://www.youtube.com/embed/{m[1]}"
    return video_url


def _is_video_embed(url: str) -> bool:
    return "player.bilibili.com" in url or "youtube.com/embed" in url


@pages.get("/")
async def index(request: Request) -> HTMLResponse:
    async with async_session() as db:
        exp_result = await db.execute(
            select(ExplorationGuide).order_by(ExplorationGuide.created_at.desc()).limit(8)
        )
        pvp_result = await db.execute(
            select(PvpTip).order_by(PvpTip.created_at.desc()).limit(8)
        )
        exploration = [item.to_dict() for item in exp_result.scalars().all()]
        pvp = [item.to_dict() for item in pvp_result.scalars().all()]
    return _render("list.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "items": exploration + pvp,
        "active_tab": "all",
        "page_title": "王者荣耀世界攻略站",
        "page_subtitle": "开放世界探险指南 & PVP对战技巧收录",
    })


@pages.get("/exploration")
async def exploration_list(
    request: Request,
    category: str | None = None,
    search: str | None = None,
    sort: str = "newest",
) -> HTMLResponse:
    async with async_session() as db:
        query = select(ExplorationGuide)
        if category and category in EXPLORATION_CATEGORIES:
            query = query.where(ExplorationGuide.category == category)
        if search:
            query = query.where(
                (ExplorationGuide.title.like(f"%{search}%"))
                | (ExplorationGuide.description.like(f"%{search}%"))
            )
        if sort == "hot":
            query = query.order_by(ExplorationGuide.is_hot.desc(), ExplorationGuide.view_count.desc())
        elif sort == "oldest":
            query = query.order_by(ExplorationGuide.created_at.asc())
        else:
            query = query.order_by(ExplorationGuide.created_at.desc())
        query = query.order_by(ExplorationGuide.sort_order)
        result = await db.execute(query)
        items = [item.to_dict() for item in result.scalars().all()]
    return _render("list.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "items": items,
        "active_tab": "exploration",
        "page_title": "🌍 开放世界探险攻略",
        "page_subtitle": "地图探索、资源收集、隐藏要素、BOSS攻略",
        "current_category": category or "all",
        "current_sort": sort,
        "current_search": search or "",
    })


@pages.get("/pvp")
async def pvp_list(
    request: Request,
    category: str | None = None,
    search: str | None = None,
    sort: str = "newest",
) -> HTMLResponse:
    async with async_session() as db:
        query = select(PvpTip)
        if category and category in PVP_CATEGORIES:
            query = query.where(PvpTip.category == category)
        if search:
            query = query.where(
                (PvpTip.title.like(f"%{search}%"))
                | (PvpTip.description.like(f"%{search}%"))
            )
        if sort == "hot":
            query = query.order_by(PvpTip.is_hot.desc(), PvpTip.view_count.desc())
        elif sort == "oldest":
            query = query.order_by(PvpTip.created_at.asc())
        else:
            query = query.order_by(PvpTip.created_at.desc())
        query = query.order_by(PvpTip.sort_order)
        result = await db.execute(query)
        items = [item.to_dict() for item in result.scalars().all()]
    return _render("list.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
        "items": items,
        "active_tab": "pvp",
        "page_title": "⚔️ PVP技巧收录",
        "page_subtitle": "角色技巧、连招教学、阵容搭配、对战策略",
        "current_category": category or "all",
        "current_sort": sort,
        "current_search": search or "",
    })


@pages.get("/exploration/{slug}")
async def exploration_detail(slug: str, request: Request) -> HTMLResponse:
    async with async_session() as db:
        result = await db.execute(select(ExplorationGuide).where(ExplorationGuide.slug == slug))
        item = result.scalar_one_or_none()
        if not item:
            return RedirectResponse(url="/exploration")
        item.view_count += 1
        await db.commit()
        await db.refresh(item)
        data = item.to_dict()
    data["video_embed"] = _get_video_embed(data.get("video_url") or "")
    return _render("detail.html", {
        "item": data,
        "item_type": "exploration",
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })


@pages.get("/pvp/{slug}")
async def pvp_detail(slug: str, request: Request) -> HTMLResponse:
    async with async_session() as db:
        result = await db.execute(select(PvpTip).where(PvpTip.slug == slug))
        item = result.scalar_one_or_none()
        if not item:
            return RedirectResponse(url="/pvp")
        item.view_count += 1
        await db.commit()
        await db.refresh(item)
        data = item.to_dict()
    data["video_embed"] = _get_video_embed(data.get("video_url") or "")
    return _render("detail.html", {
        "item": data,
        "item_type": "pvp",
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })


@pages.get("/admin")
async def admin_page(request: Request) -> HTMLResponse:
    return _render("admin.html", {
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })
