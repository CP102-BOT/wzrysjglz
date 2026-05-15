# 王者荣耀世界攻略站

## 项目结构（前后端分离）

```
wzrysj/
├── index.html              # 前台页面 → 部署到 GitHub Pages
├── backend/                # 后端 → 部署到 Render
│   ├── app.py              # Flask API + 管理后台
│   ├── admin.html          # 管理后台页面
│   └── requirements.txt    # Python 依赖
└── README.md
```

## 部署步骤

### 一、部署后端到 Render（免费）

1. 打开 https://dashboard.render.com ，注册/登录（用 GitHub 账号）

2. 点击 **New +** → **Web Service**

3. 连接你的 GitHub 仓库（先把整个 wzrysj 文件夹推到一个 GitHub 仓库）

4. 配置 Render：
   - **Name**: wzrysj（或自定义）
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

5. 点击 **Create Web Service**，等待部署完成

6. 部署完成后你会获得一个 URL，类似：
   ```
   https://wzrysj.onrender.com
   ```
   复制这个 URL。

### 二、部署前端到 GitHub Pages

1. 修改 `index.html` 第 3 行的 API 地址，把占位符换成你的 Render URL：
   ```javascript
   const API = 'https://wzrysj.onrender.com/api/data';
   ```

2. 在你的 GitHub 仓库中，进入 **Settings** → **Pages**

3. **Source**: Deploy from a branch
4. **Branch**: main，文件夹选 `/ (root)`
5. 点击 **Save**

6. 等待 1-2 分钟，GitHub Pages 会给你一个 URL：
   ```
   https://你的用户名.github.io/仓库名/
   ```
   别人访问这个 URL 就能看到你的攻略站了。

### 三、登录后台改内容

访问 `https://wzrysj.onrender.com/admin`（你的 Render URL + /admin）

- **账户**：`site_admin_2026`
- **密码**：`K9xP!7qR#3zL@2sN$5aM`

在后台可以增删改所有数据（英雄、资源、攻略、地图、兑换码、速查表），还支持批量导入 CSV。

### 四、本地测试（可选）

```bash
# 启动后端
cd backend
pip install -r requirements.txt
python app.py

# 打开前台（直接用浏览器打开 index.html）
```

注意：本地测试时 index.html 里 API 地址要改成 `http://localhost:5000/api/data`。

## 注意事项

- Render 免费版 15 分钟无访问会休眠，首次访问需等待 30 秒左右唤醒
- GitHub Pages 免费、无流量限制
- 数据库放在 Render 磁盘上，如果 Render 重装系统数据会丢失（建议定期在后台导出备份）
