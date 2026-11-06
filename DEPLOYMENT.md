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

## Docker Compose（已提供，未在本机验证）

```powershell
copy .env.example .env
docker compose up --build
# http://localhost:8080
```

服务：

- `web`：Nginx + 生产前端，`/api` 和 `/runtime` 反代到 API；
- `api`：独立 FastAPI；
- `worker`：轮询 `image3d_jobs` 的独立 Worker；
- 数据卷：`printverse-data`（SQLite）、`printverse-runtime`（模型/G-code）、`printverse-logs`。

**当前缺口（不掩盖）：**

1. 本机没有 `docker` 命令，Compose 未构建验证，状态 `BLOCKED`。
2. **PostgreSQL 适配器尚未实现**；当前独立数据库仍是 SQLite 文件。`docker-compose.yml` 没有假装使用未连接的 Postgres。目标要求中的 PostgreSQL 一项是 `NOT_IMPLEMENTED`，不是被删减。
3. 容器内没有 Windows `OrcaSlicer` 二进制，真实切片依赖宿主机/Windows 工具；云容器可用于图片生成与模型处理，不能在容器内直接完成 Orca 切片。
4. Tauri 客户端需要 Rust/Cargo 和 Windows C++ Build Tools；本机没有 `cargo`，无法构建 MSI/NSIS。

## 环境变量

见 `.env.example`。真实 Kimi/TokenHub Key 只能放在服务端 `.env`，不得进入前端构建。

## 关闭 DeepSeek Harness 后

- `uvicorn`、`vite preview`、静态前端本身不依赖 Harness；
- 但当前这两个进程是由本会话启动的，关闭会话可能终止它们；
- 真正长期运行应使用 Docker Compose（待 Docker/Postgres 完整实现）或 Windows 服务/任务计划；
- 在未完成上述部署验证前，不能宣称“关闭 Harness 后一定仍可访问”。
