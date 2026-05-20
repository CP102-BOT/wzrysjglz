import json
import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.exceptions import UnauthorizedError, NotFoundError
from models.guide import (
    ExplorationGuide,
    PvpTip,
    EXPLORATION_CATEGORIES,
    PVP_CATEGORIES,
    DIFFICULTY_LEVELS,
)

api = APIRouter(prefix="/api")

# ==================== 公开数据接口 ====================


@api.get("/exploration")
async def list_exploration(
    category: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    query = select(ExplorationGuide)
    if category and category in EXPLORATION_CATEGORIES:
        query = query.where(ExplorationGuide.category == category)
    if difficulty and difficulty in DIFFICULTY_LEVELS:
        query = query.where(ExplorationGuide.difficulty == difficulty)
    if tag:
        query = query.where(ExplorationGuide.tags.like(f"%{tag}%"))
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
    items = result.scalars().all()
    data = [item.to_dict() for item in items]
    return JSONResponse(data)


@api.get("/exploration/{slug}")
async def get_exploration(slug: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    result = await db.execute(select(ExplorationGuide).where(ExplorationGuide.slug == slug))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="攻略不存在")
    item.view_count += 1
    await db.commit()
    await db.refresh(item)
    data = item.to_dict()
    return JSONResponse(data)


@api.get("/pvp")
async def list_pvp(
    category: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    query = select(PvpTip)
    if category and category in PVP_CATEGORIES:
        query = query.where(PvpTip.category == category)
    if difficulty and difficulty in DIFFICULTY_LEVELS:
        query = query.where(PvpTip.difficulty == difficulty)
    if tag:
        query = query.where(PvpTip.tags.like(f"%{tag}%"))
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
    items = result.scalars().all()
    data = [item.to_dict() for item in items]
    return JSONResponse(data)


@api.get("/pvp/{slug}")
async def get_pvp(slug: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    result = await db.execute(select(PvpTip).where(PvpTip.slug == slug))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="攻略不存在")
    item.view_count += 1
    await db.commit()
    await db.refresh(item)
    data = item.to_dict()
    return JSONResponse(data)


@api.get("/meta")
async def get_meta() -> JSONResponse:
    return JSONResponse({
        "exploration_categories": EXPLORATION_CATEGORIES,
        "pvp_categories": PVP_CATEGORIES,
        "difficulty_levels": DIFFICULTY_LEVELS,
    })


# ==================== 管理后台认证 ====================


async def verify_admin(request: Request) -> None:
    session_user = request.cookies.get("admin_session")
    if session_user != settings.admin_username:
        raise UnauthorizedError("未登录")


@api.post("/admin/login")
async def admin_login(request: Request) -> JSONResponse:
    data = await request.json()
    username = data.get("username", "")
    password = data.get("password", "")
    if username == settings.admin_username and password == settings.admin_password:
        response = JSONResponse({"success": True})
        response.set_cookie("admin_session", settings.admin_username, httponly=True)
        return response
    raise UnauthorizedError("账号或密码错误")


@api.post("/admin/logout")
async def admin_logout() -> JSONResponse:
    response = JSONResponse({"success": True})
    response.delete_cookie("admin_session")
    return response


@api.get("/admin/check")
async def admin_check(request: Request) -> JSONResponse:
    try:
        await verify_admin(request)
        return JSONResponse({"logged_in": True})
    except UnauthorizedError:
        return JSONResponse({"logged_in": False})


# ==================== 管理后台 CRUD ====================


def _jsonify_dict(d: dict[str, Any]) -> dict[str, Any]:
    for key in ("tags",):
        if key in d and isinstance(d[key], list):
            d[key] = json.dumps(d[key], ensure_ascii=False)
    return d


@api.post("/admin/upload-video")
async def upload_video(file: UploadFile = File(...)) -> JSONResponse:
    allowed_types = {"video/mp4", "video/webm", "video/ogg", "video/x-msvideo", "video/quicktime"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 mp4/webm/ogg/avi/mov 格式")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "videos")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 200MB 限制")
    with open(save_path, "wb") as f:
        f.write(content)
    url = f"/uploads/videos/{filename}"
    logger.info(f"[admin] 上传视频: {filename} ({len(content)} bytes)")
    return JSONResponse({"success": True, "url": url})


@api.post("/admin/exploration")
async def create_exploration(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    data = await request.json()
    data = _jsonify_dict(data)
    item = ExplorationGuide(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    logger.info(f"[admin] 创建探险攻略: {item.title}")
    return JSONResponse({"success": True, "id": item.id})


@api.put("/admin/exploration/{item_id}")
async def update_exploration(item_id: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    result = await db.execute(select(ExplorationGuide).where(ExplorationGuide.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("攻略不存在")
    data = await request.json()
    data = _jsonify_dict(data)
    for k, v in data.items():
        if k != "id":
            setattr(item, k, v)
    await db.commit()
    logger.info(f"[admin] 更新探险攻略: {item.title}")
    return JSONResponse({"success": True})


@api.delete("/admin/exploration/{item_id}")
async def delete_exploration(item_id: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    result = await db.execute(select(ExplorationGuide).where(ExplorationGuide.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("攻略不存在")
    await db.delete(item)
    await db.commit()
    logger.info(f"[admin] 删除探险攻略: {item_id}")
    return JSONResponse({"success": True})


@api.post("/admin/pvp")
async def create_pvp(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    data = await request.json()
    data = _jsonify_dict(data)
    item = PvpTip(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    logger.info(f"[admin] 创建PVP技巧: {item.title}")
    return JSONResponse({"success": True, "id": item.id})


@api.put("/admin/pvp/{item_id}")
async def update_pvp(item_id: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    result = await db.execute(select(PvpTip).where(PvpTip.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("攻略不存在")
    data = await request.json()
    data = _jsonify_dict(data)
    for k, v in data.items():
        if k != "id":
            setattr(item, k, v)
    await db.commit()
    logger.info(f"[admin] 更新PVP技巧: {item.title}")
    return JSONResponse({"success": True})


@api.delete("/admin/pvp/{item_id}")
async def delete_pvp(item_id: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    await verify_admin(request)
    result = await db.execute(select(PvpTip).where(PvpTip.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("攻略不存在")
    await db.delete(item)
    await db.commit()
    logger.info(f"[admin] 删除PVP技巧: {item_id}")
    return JSONResponse({"success": True})
