import json, os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_db
from models import PvPGuide, PvEGuide, CodeItem, QuickRef
from admin_routes import router as admin_router
from logging_config import setup_logging
from exceptions import AppError, app_error_handler, generic_error_handler

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Setup logging
logger = setup_logging()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down application...")


app = FastAPI(title="王者荣耀世界攻略站", lifespan=lifespan)

# Rate limiting
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"}
    )

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(admin_router)
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def video_thumbnail(url: str) -> str | None:
    """Extract video thumbnail URL from YouTube/Bilibili links."""
    if not url:
        return None
    m = __import__("re").search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})", url)
    if m:
        return f"https://img.youtube.com/vi/{m.group(1)}/hqdefault.jpg"
    return None


templates.env.filters["video_thumbnail"] = video_thumbnail
os.makedirs(BASE_DIR / "uploads", exist_ok=True)
os.makedirs(BASE_DIR / "data", exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")


def parse_json_field(val: str):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/{table}")
async def api_list(table: str, db: AsyncSession = Depends(get_db)):
    model_map = {"pvp": PvPGuide, "pve": PvEGuide, "codes": CodeItem, "quickref": QuickRef}
    model = model_map.get(table)
    if not model:
        return {"items": [], "total": 0}
    result = await db.execute(select(model).order_by(model.sort_order, model.id))
    items = result.scalars().all()
    data = []
    for item in items:
        d = {c.name: getattr(item, c.name) for c in item.__table__.columns}
        for k in ("tags", "items"):
            if k in d:
                d[k] = parse_json_field(d[k])
        data.append(d)
    return {"items": data, "total": len(data)}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"section": "home"})


@app.get("/pvp", response_class=HTMLResponse)
async def pvp_page(request: Request, category: str = "all",
                   db: AsyncSession = Depends(get_db)):
    stmt = select(PvPGuide)
    if category and category != "all":
        stmt = stmt.where(PvPGuide.category == category)
    stmt = stmt.order_by(PvPGuide.sort_order, PvPGuide.id)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return templates.TemplateResponse(request, "pages/pvp.html", {
        "items": items, "category": category, "section": "pvp", "table": "pvp"
    })


@app.get("/pve", response_class=HTMLResponse)
async def pve_page(request: Request, category: str = "all",
                   db: AsyncSession = Depends(get_db)):
    stmt = select(PvEGuide)
    if category and category != "all":
        stmt = stmt.where(PvEGuide.category == category)
    stmt = stmt.order_by(PvEGuide.sort_order, PvEGuide.id)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return templates.TemplateResponse(request, "pages/pve.html", {
        "items": items, "category": category, "section": "pve", "table": "pve"
    })


@app.get("/guide/{table}/{item_id}", response_class=HTMLResponse)
async def guide_detail(request: Request, table: str, item_id: int,
                       db: AsyncSession = Depends(get_db)):
    model_map = {"pvp": PvPGuide, "pve": PvEGuide, "codes": CodeItem, "quickref": QuickRef}
    model = model_map.get(table)
    if not model:
        return HTMLResponse("Not found", status_code=404)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(request, "partials/_detail.html", {
        "item": item, "table": table
    })


@app.get("/partials/hero", response_class=HTMLResponse)
async def hero_partial(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PvPGuide).where(PvPGuide.badge != "").limit(5)
    )
    items = result.scalars().all()
    return templates.TemplateResponse(request, "partials/_hero.html", {
        "items": items
    })


@app.get("/partials/quickref", response_class=HTMLResponse)
async def quickref_partial(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuickRef).order_by(QuickRef.sort_order, QuickRef.id))
    items = result.scalars().all()
    return templates.TemplateResponse(request, "partials/_quickref.html", {
        "items": items
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse((BASE_DIR / "admin.html").read_text("utf-8"))


@app.get("/partials/codes", response_class=HTMLResponse)
async def codes_partial(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeItem).where(CodeItem.is_active == 1).order_by(CodeItem.sort_order, CodeItem.id)
    )
    items = result.scalars().all()
    return templates.TemplateResponse(request, "partials/_codes.html", {
        "items": items
    })


@app.get("/partials/{table}", response_class=HTMLResponse)
async def partial_list(request: Request, table: str, category: str = "all",
                       db: AsyncSession = Depends(get_db)):
    model_map = {"pvp": PvPGuide, "pve": PvEGuide}
    model = model_map.get(table)
    if not model:
        return HTMLResponse("", status_code=204)
    stmt = select(model)
    if category and category != "all":
        stmt = stmt.where(model.category == category)
    stmt = stmt.order_by(model.sort_order, model.id)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return templates.TemplateResponse(request, "partials/_card_grid.html", {
        "items": items, "table": table
    })
