# PrintVerse 独立部署说明

## 本地独立运行（不依赖 DeepSeek Harness）

```powershell
cd C:\Users\someb\Desktop\printverse
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
npm run build --prefix frontend
npm run preview --prefix frontend
```

网页：`http://127.0.0.1:4173/`  
API：`http://127.0.0.1:8000/api/health`

## Docker Compose（已在 WSL2 Docker Engine 验证）

实测：`docker compose build` 成功；`postgres/api/worker/web` 全部启动，API `healthy`，Web `http://localhost:8080` 返回 200。

```powershell
copy .env.example .env
docker compose up --build
# http://localhost:8080
```

服务：

- `web`：Nginx + 生产前端，`/api` 和 `/runtime` 反代到 API；
- `postgres`：PostgreSQL 17；
- `api`：独立 FastAPI，使用 PostgreSQL；
- `worker`：轮询 `image3d_jobs` 的独立 Worker；
- 数据卷：`printverse-data`（SQLite）、`printverse-runtime`（模型/G-code）、`printverse-logs`。

**当前缺口（不掩盖）：**

1. 已通过 WSL2 Ubuntu + Docker Engine 完成 `docker compose build` 和 `up -d`；PostgreSQL/API/Worker/Web 均健康。
2. **PostgreSQL 适配器已实现并验证**（`backend/app/db_postgres.py`，由 `PRINTVERSE_DATABASE_URL` 选择；本地 PostgreSQL 17.2 已跑通账本与 Image3D；Compose 已接入 `postgres:17-alpine`）。PostgreSQL-only API（8001）与 Worker 已实际跑通；Docker 容器内 Postgres 尚未验证。
3. 容器内没有 Windows `OrcaSlicer` 二进制，真实切片依赖宿主机/Windows 工具；云容器可用于图片生成与模型处理，不能在容器内直接完成 Orca 切片。
4. Tauri 客户端：Rust/MSVC 已安装，release exe 已构建；当前自动化会话无交互桌面，窗口未观察；NSIS 安装包已构建：23.19 MiB；静默安装/窗口在当前无交互桌面会话未验证。

## 环境变量

见 `.env.example`。真实 Kimi/TokenHub Key 只能放在服务端 `.env`，不得进入前端构建。

## 关闭 DeepSeek Harness 后

- `uvicorn`、`vite preview`、静态前端本身不依赖 Harness；
- 但当前这两个进程是由本会话启动的，关闭会话可能终止它们；
- 真正长期运行应使用 Docker Compose（Postgres 已接入，Compose 仍待 Docker 验证）或 Windows 服务/任务计划；
- 在未完成上述部署验证前，不能宣称“关闭 Harness 后一定仍可访问”。
