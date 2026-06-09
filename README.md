# 王者荣耀世界攻略站 — PVP + 自由探索

> 王者荣耀世界（Honor of Kings: World）开放世界RPG攻略站。PVP 为主界面，自由世界探索为辅。

## 两大板块

| 板块 | 内容 |
|------|------|
| **PVP攻略** | 武道对决(1v1)、孤身论决(1v1公平)、协战争魁(4v4)、PK模式(1v1/3v3/5v5)、通用战斗技巧 |
| **探索攻略** | 稷下学院、观星群山、奇门秘境、秘禁之地、织梦原野、地下世界、春溪漫滩、唤灵系统、武器锻造 |

## 项目结构

```
wzrysjglz/
├── index.html              # 前台页面 → GitHub Pages
├── backend/                # 后端 → Render
│   ├── app.py              # Flask API + 管理后台
│   ├── admin.html          # 管理后台页面
│   ├── requirements.txt    # Python 依赖
│   └── uploads/            # 上传的图片/视频
└── README.md
```

## 部署步骤

### 一、后端部署到 Render

1. 打开 https://dashboard.render.com 注册/登录
2. 点击 **New +** → **Web Service**
3. 连接 GitHub 仓库
4. 配置：
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. 部署后获得 URL，如：`https://wzrysjglz.onrender.com`

### 二、前端部署到 GitHub Pages

1. 修改 `index.html` 中 API 地址为你的 Render URL
2. GitHub 仓库 **Settings** → **Pages** → Source: `main` branch, root `/`
3. 访问 `https://你的用户名.github.io/wzrysjglz/`

### 三、管理后台

访问 `https://你的域名/admin`

- 账号密码通过环境变量配置，见 `.env.example`

### 后台功能

- **发布/编辑/删除** PVP攻略和探索攻略
- **视频嵌入**：支持 YouTube、B站、mp4直链，编辑器内置一键插入
- **媒体库**：上传图片/视频，复制链接直接使用
- **CSV批量导入**：下载模板 → 填入数据 → 一键导入
- **拖拽排序**、置顶、复制、批量删除
- **数据导出/恢复** JSON备份

## 本地测试

```bash
cd backend
pip install -r requirements.txt
python app.py
# 前台用浏览器打开 index.html
# 本地测试时 API 改为 http://localhost:5000/api/data
```

## 注意事项

- Render 免费版 15 分钟无访问会休眠
- 数据库在 Render 磁盘上，建议定期导出备份
- 视频支持上传到媒体库（mp4/webm/mov），也可直接贴外部视频链接