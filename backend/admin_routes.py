import json, csv, io, os, secrets, hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
from models import PvPGuide, PvEGuide, CodeItem, QuickRef, AuditLog
from schemas import (
    GuideCreate, GuideUpdate, CodeCreate, CodeUpdate,
    QuickRefCreate, QuickRefUpdate, SortPayload, BatchDeletePayload,
    ChangePasswordPayload, LoginPayload, PaginatedResponse,
)

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security configuration - MUST be set in .env
SECRET_KEY = os.environ.get("ADMIN_SECRET")
if not SECRET_KEY:
    raise RuntimeError("ADMIN_SECRET environment variable is not set. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS")
if not ADMIN_PASS:
    raise RuntimeError("ADMIN_PASS environment variable is not set.")

_admin_hash = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
_is_default_password = (ADMIN_PASS == "admin888")
security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/admin", tags=["admin"])

TABLE_MAP = {
    "pvp_guides": PvPGuide,
    "explore_guides": PvEGuide,
    "codes": CodeItem,
    "quickref": QuickRef,
}
TABLE_NAMES = {"pvp_guides": "PVP攻略", "explore_guides": "探索攻略", "codes": "兑换码", "quickref": "速查手册"}


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("user") != ADMIN_USER:
            raise HTTPException(status_code=401, detail="无效凭证")
    except JWTError:
        raise HTTPException(status_code=401, detail="凭证过期或无效")


@router.post("/login")
@limiter.limit(os.environ.get("LOGIN_RATE_LIMIT", "5/minute"))
async def admin_login(request: Request, payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    if payload.username != ADMIN_USER or hashlib.sha256(payload.password.encode()).hexdigest() != _admin_hash:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = jwt.encode(
        {"user": payload.username, "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)},
        SECRET_KEY, algorithm=ALGORITHM,
    )
    await log_audit(db, "login", "", detail="管理员登录")
    return {"success": True, "token": token, "must_change_password": _is_default_password}


@router.get("/check")
async def admin_check(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials:
        return {"logged_in": False}
    try:
        jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"logged_in": True}
    except JWTError:
        return {"logged_in": False}


@router.get("/stats")
async def admin_stats(_=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = {}
    for key, model in TABLE_MAP.items():
        count_q = select(func.count(model.id))
        latest_q = select(model.created_at).order_by(model.created_at.desc()).limit(1)
        cnt = (await db.execute(count_q)).scalar() or 0
        latest = (await db.execute(latest_q)).scalar()
        result[key] = {"count": cnt, "latest": str(latest) if latest else None}

    log_stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)
    logs = (await db.execute(log_stmt)).scalars().all()
    result["logs"] = [
        {"id": log.id, "action": log.action, "table_name": log.table_name,
         "item_id": log.item_id, "detail": log.detail, "created_at": str(log.created_at) if log.created_at else None}
        for log in logs
    ]
    return result


@router.post("/change-password")
async def admin_change_password(payload: ChangePasswordPayload, _=Depends(get_current_user)):
    global _admin_hash, _is_default_password
    
    if hashlib.sha256(payload.current_password.encode()).hexdigest() != _admin_hash:
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    # Update .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        content = env_path.read_text("utf-8")
        content = content.replace(f"ADMIN_PASS={ADMIN_PASS}", f"ADMIN_PASS={payload.new_password}")
        env_path.write_text(content, "utf-8")
    
    # Update in-memory
    _admin_hash = hashlib.sha256(payload.new_password.encode()).hexdigest()
    _is_default_password = False
    
    return {"success": True, "message": "密码修改成功"}


def get_model(table: str):
    m = TABLE_MAP.get(table)
    if not m:
        raise HTTPException(status_code=404, detail="未知数据表")
    return m


async def log_audit(db: AsyncSession, action: str, table_name: str = "", item_id: int | None = None, detail: str = ""):
    log = AuditLog(action=action, table_name=table_name, item_id=item_id, detail=detail)
    db.add(log)
    await db.commit()


@router.get("/data/{table}")
async def admin_list(table: str, page: int = 1, page_size: int = 50,
                     _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    total_q = select(func.count(model.id))
    total = (await db.execute(total_q)).scalar() or 0

    stmt = select(model).order_by(model.sort_order, model.id).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = []
    for row in result.scalars().all():
        d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        for k in ("tags", "items"):
            if k in d and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except (json.JSONDecodeError, TypeError):
                    pass
        items.append(d)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=-(-total // page_size))


@router.post("/{table}")
async def admin_create(table: str, data: dict, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    
    # Validate input based on table
    if table in ("pvp_guides", "explore_guides"):
        validated = GuideCreate(**data)
        data = validated.model_dump()
    elif table == "codes":
        validated = CodeCreate(**data)
        data = validated.model_dump()
    elif table == "quickref":
        validated = QuickRefCreate(**data)
        data = validated.model_dump()
    
    # Serialize list fields to JSON
    for k in ("tags", "items"):
        if k in data and isinstance(data[k], list):
            data[k] = json.dumps(data[k], ensure_ascii=False)
    
    item = model(**{k: v for k, v in data.items() if hasattr(model, k)})
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await log_audit(db, "create", table, item.id, f"创建 {TABLE_NAMES.get(table, table)}: {item.title if hasattr(item, 'title') else getattr(item, 'code', '')}")
    return {"success": True, "id": item.id}


@router.put("/{table}/{item_id}")
async def admin_update(table: str, item_id: int, data: dict,
                       _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # Validate input based on table
    if table in ("pvp_guides", "explore_guides"):
        validated = GuideUpdate(**data)
        data = validated.model_dump(exclude_unset=True)
    elif table == "codes":
        validated = CodeUpdate(**data)
        data = validated.model_dump(exclude_unset=True)
    elif table == "quickref":
        validated = QuickRefUpdate(**data)
        data = validated.model_dump(exclude_unset=True)
    
    for k, v in data.items():
        if hasattr(item, k):
            if k in ("tags", "items") and isinstance(v, list):
                v = json.dumps(v, ensure_ascii=False)
            setattr(item, k, v)
    await db.commit()
    await log_audit(db, "update", table, item_id, f"更新 {TABLE_NAMES.get(table, table)}: {item.title if hasattr(item, 'title') else getattr(item, 'code', '')}")
    return {"success": True}


@router.delete("/{table}/{item_id}")
async def admin_delete(table: str, item_id: int,
                       _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    await db.execute(delete(model).where(model.id == item_id))
    await db.commit()
    await log_audit(db, "delete", table, item_id, f"删除 {TABLE_NAMES.get(table, table)} ID: {item_id}")
    return {"success": True}


@router.post("/{table}/sort")
async def admin_sort(table: str, payload: SortPayload,
                     _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    for entry in payload.items:
        item = await db.get(model, entry.id)
        if item:
            item.sort_order = entry.sort_order
    await db.commit()
    return {"success": True}


@router.post("/{table}/{item_id}/duplicate")
async def admin_duplicate(table: str, item_id: int,
                          _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    result = await db.execute(select(model).where(model.id == item_id))
    orig = result.scalar_one_or_none()
    if not orig:
        raise HTTPException(status_code=404, detail="内容不存在")
    skip = {"id", "created_at", "updated_at"}
    data = {c.name: getattr(orig, c.name) for c in orig.__table__.columns if c.name not in skip}
    new_item = model(**data)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    await log_audit(db, "duplicate", table, new_item.id, f"复制 {TABLE_NAMES.get(table, table)}: {new_item.title if hasattr(new_item, 'title') else getattr(new_item, 'code', '')}")
    return {"success": True, "id": new_item.id}


@router.post("/batch-delete")
async def admin_batch_delete(payload: BatchDeletePayload, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(payload.table)
    if not payload.ids:
        raise HTTPException(status_code=400, detail="未指定 ID")
    await db.execute(delete(model).where(model.id.in_(payload.ids)))
    await db.commit()
    await log_audit(db, "batch_delete", payload.table, detail=f"批量删除 {len(payload.ids)} 条 {TABLE_NAMES.get(payload.table, payload.table)}")
    return {"success": True, "deleted": len(payload.ids)}


@router.get("/template/{table}")
async def admin_template(table: str):
    model = get_model(table)
    cols = [c.name for c in model.__table__.columns if c.name not in ("id", "created_at")]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(cols)
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table}_template.csv"},
    )


@router.post("/import")
async def admin_import(table: str = Form(...), file: UploadFile = File(...),
                       _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    cols = [c.name for c in model.__table__.columns if c.name not in ("id", "created_at")]
    count = 0
    for row in reader:
        data = {k: v.strip() if v else "" for k, v in row.items() if k in cols}
        for k in ("tags", "items"):
            if k in data:
                try:
                    json.loads(data[k])
                except (json.JSONDecodeError, TypeError):
                    data[k] = json.dumps([t.strip() for t in data[k].split(",") if t.strip()], ensure_ascii=False)
        db.add(model(**data))
        count += 1
    await db.commit()
    await log_audit(db, "import", table, detail=f"导入 {count} 条 {TABLE_NAMES.get(table, table)}")
    return {"success": True, "inserted": count}


@router.get("/media")
async def admin_media_list(_=Depends(get_current_user)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    files = []
    for fname in os.listdir(upload_dir):
        fpath = os.path.join(upload_dir, fname)
        if os.path.isfile(fpath):
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            ftype = "image" if ext in ("jpg", "jpeg", "png", "gif", "webp", "svg") else "video" if ext in ("mp4", "webm", "mov") else "other"
            files.append({"filename": fname, "url": f"/uploads/{fname}", "type": ftype})
    return files


@router.delete("/media/{filename:path}")
async def admin_media_delete(filename: str, _=Depends(get_current_user)):
    safe = os.path.basename(filename)
    fpath = os.path.join("uploads", safe)
    if os.path.exists(fpath):
        os.remove(fpath)
    return {"success": True}


@router.post("/upload")
async def admin_upload(file: UploadFile = File(...), _=Depends(get_current_user)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # File size limit (5MB)
    max_size = int(os.environ.get("MAX_UPLOAD_SIZE", "5")) * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"文件大小超过限制（最大 {max_size // 1024 // 1024}MB）")
    
    # MIME type whitelist
    allowed_types = {
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
        "video/mp4", "video/webm", "video/quicktime",
    }
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
    
    # Extension whitelist
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp", "svg", "mp4", "webm", "mov"}
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件扩展名: .{ext}")
    
    # Sanitize filename
    import re
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename)
    safe = f"{int(datetime.now().timestamp())}_{safe_name}"
    fpath = os.path.join(upload_dir, safe)
    
    with open(fpath, "wb") as f:
        f.write(content)
    
    ftype = "image" if ext in ("jpg", "jpeg", "png", "gif", "webp", "svg") else "video"
    return {"success": True, "filename": safe, "url": f"/uploads/{safe}", "type": ftype}


@router.get("/export")
async def admin_export(_=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = {}
    for key, model in TABLE_MAP.items():
        rows = (await db.execute(select(model).order_by(model.sort_order, model.id))).scalars().all()
        result[key] = [
            {c.name: getattr(r, c.name) for c in r.__table__.columns if c.name != "id"}
            for r in rows
        ]
    return result
