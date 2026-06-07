import json, csv, io, os, secrets, hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import PvPGuide, PvEGuide, CodeItem, QuickRef

SECRET_KEY = os.environ.get("ADMIN_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin888")

_admin_hash = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
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
async def admin_login(data: dict):
    user, pwd = data.get("username"), data.get("password")
    if user != ADMIN_USER or hashlib.sha256((pwd or "").encode()).hexdigest() != _admin_hash:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = jwt.encode(
        {"user": user, "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)},
        SECRET_KEY, algorithm=ALGORITHM,
    )
    return {"success": True, "token": token}


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
    return result


def get_model(table: str):
    m = TABLE_MAP.get(table)
    if not m:
        raise HTTPException(status_code=404, detail="未知数据表")
    return m


@router.get("/data/{table}")
async def admin_list(table: str, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    result = await db.execute(select(model).order_by(model.sort_order, model.id))
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
    return items


@router.post("/{table}")
async def admin_create(table: str, data: dict, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    for k in ("tags", "items"):
        if k in data and isinstance(data[k], list):
            data[k] = json.dumps(data[k], ensure_ascii=False)
    item = model(**{k: v for k, v in data.items() if hasattr(model, k)})
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"success": True, "id": item.id}


@router.put("/{table}/{item_id}")
async def admin_update(table: str, item_id: int, data: dict,
                       _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")
    for k, v in data.items():
        if hasattr(item, k):
            if k in ("tags", "items") and isinstance(v, list):
                v = json.dumps(v, ensure_ascii=False)
            setattr(item, k, v)
    await db.commit()
    return {"success": True}


@router.delete("/{table}/{item_id}")
async def admin_delete(table: str, item_id: int,
                       _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    await db.execute(delete(model).where(model.id == item_id))
    await db.commit()
    return {"success": True}


@router.post("/{table}/sort")
async def admin_sort(table: str, payload: dict,
                     _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(table)
    for entry in payload.get("items", []):
        await db.execute(
            select(model).where(model.id == entry["id"]).model.update(
                {"sort_order": entry.get("sort_order", 0)}
            )
        )
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
    data = {c.name: getattr(orig, c.name) for c in orig.__table__.columns if c.name != "id"}
    new_item = model(**data)
    db.add(new_item)
    await db.commit()
    return {"success": True, "id": new_item.id}


@router.post("/batch-delete")
async def admin_batch_delete(payload: dict, _=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = get_model(payload.get("table", ""))
    ids = payload.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="未指定 ID")
    await db.execute(delete(model).where(model.id.in_(ids)))
    await db.commit()
    return {"success": True, "deleted": len(ids)}


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
    safe = f"{int(datetime.now().timestamp())}_{file.filename}"
    fpath = os.path.join(upload_dir, safe)
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
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
