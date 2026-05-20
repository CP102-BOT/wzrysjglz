import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from core.config import settings
from core.database import init_db, async_session
from core.exceptions import AppError
from models.seed import seed_all
from web.routes.api import api as api_router
from web.routes.pages import pages as page_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as session:
        await seed_all(session)
    logger.info("数据库初始化完成，种子数据已检查")
    yield


app = FastAPI(title="王者荣耀世界攻略站", lifespan=lifespan)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(f"[{exc.status_code}] {exc.message}")
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


app.include_router(api_router)
app.include_router(page_router)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount("/uploads", StaticFiles(directory=(pathlib.Path(__file__).parent / "uploads")), name="uploads")

logger.add("logs/wzrysj.log", rotation="10 MB", retention="7 days", level="INFO")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
