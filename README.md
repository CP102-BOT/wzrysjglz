# 王者荣耀世界攻略站

FastAPI + Jinja2，开放世界探险攻略 + PVP技巧收录

## 项目结构

```
wzrysjglz/
├── main.py                  # FastAPI 入口
├── pyproject.toml           # uv 依赖管理
├── .env                     # 环境变量（不提交）
├── core/                    # 核心配置、数据库、异常
├── models/                  # 数据模型 + 种子数据
└── web/
    ├── routes/              # API路由 + 页面路由
    └── templates/           # Jinja2 模板（前台 + 后台）
```

## 本地启动

```bash
cd wzrysjglz
uv venv
uv run uvicorn main:app --port 8000
```

访问 http://localhost:8000，管理后台 /admin

## 部署到 Render

目前 https://wzrysjglz.onrender.com 已经跑着旧版 Flask，需要更新：

1. 打开 [Render Dashboard](https://dashboard.render.com) → 找到 `wzrysjglz` Web Service
2. 点 **Settings**，修改以下配置：
   - **Root Directory**: 留空（就是项目根目录）
   - **Build Command**: `pip install fastapi uvicorn sqlalchemy aiosqlite jinja2 python-multipart loguru pydantic-settings`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. 点 **Environment**，添加环境变量：
   - `ADMIN_USERNAME` = `site_admin_2026`
   - `ADMIN_PASSWORD` = `K9xP!7qR#3zL@2sN$5aM`
   - `SECRET_KEY` = `wzrysj_admin_2026_secret`
4. 代码已经 push 到 GitHub，Render 会自动检测并重新部署
5. 部署完成后访问 https://wzrysjglz.onrender.com

> **注意**：v2.0 不再需要 GitHub Pages，前后端都在 Render 一个服务上跑。

## 管理后台

- 地址: /admin
- 账号密码: 见 .env（或 Render 环境变量）
