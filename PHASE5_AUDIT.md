# PrintVerse 全功能纠偏审计（2026-11-06）

## 1. Git / 删除审计

- 当前 HEAD：`e223002`；工作区在审计开始时干净。
- 全历史 `git log --all --diff-filter=D` 的结果为空：**没有任何文件被 Git 删除过**。
- 因此“上一阶段删除了耗材、G-code、机械或数字孪生模块”的说法不成立；这些能力要么仍在，要么从未实现。
- 审计开始时仓库没有 `desktop/`、`src-tauri/`、`Dockerfile`、`docker-compose.yml`、PostgreSQL 适配器；这些不是被删除，而是**尚未实现**，本轮已补上骨架/适配器。

## 2. 六大模块现状

| 模块 | 现状 | 证据 / 缺口 |
|---|---|---|
| A AI 三维创作 | **PARTIAL** | 图片→彩色 GLB、TripoSR/Mock、TokenHub/Kimi 适配器；三视图本地重建、栅格工程图拉伸、STEP/DXF/STL/3MF/OBJ/GLB 导入已接；参数化 CAD 仍缺 |
| B 模型处理 | **PARTIAL** | 统一 analyze/repair/export；近似 ray-cast 壁厚与悬垂面积；支撑仍需切片器标定 |
| C 数字孪生 | **COMPLETE（有已声明缺陷）** | 4,526 placements、8 个 GLB、真实 CAD 层级、零件选择、PBR、爆炸/模块/高速紧固件；XY 横梁仍静态，WIRING 仅 1 个实体 |
| D G-code 虚拟打印 | **COMPLETE（有已声明限制）** | 真实 Orca 切片、G-code 解析、CoreXY/Z/E 驱动、逐层沉积、暂停/继续/取消/倍速、完成/脱离；冷却/加速度仍为估算 |
| E 耗材计量 | **COMPLETE（虚拟边界）** | 真实 G-code 质量、首件免费、预扣/提交/退款、admin 无限、幂等；只记录虚拟额度，不碰实体 |
| F 桌宠 / 云端 | **PARTIAL** | 浏览器透明桌宠可用；PostgreSQL 适配器已用本地 17.2 验证；Tauri 壳/Compose/Worker 已写，但本机无 cargo/docker |

## 3. 关键代码审计

- 打印上传仅接受 `.stl`（`backend/app/main.py:110`）；STL 是唯一展示/切片输入。
- `FinishedObject.tsx` 使用 `STLLoader`，没有 GLB/材质路径；成品颜色被统一材质覆盖。
- `collection.model_path` 固定指向 `model.stl`，没有彩色 GLB 的集合资产。
- `Image3DPanel` 只暴露一个 `Download`，把 `output_url` 当作 STL；TripoSR 明明有 vertex colour，却没有把 GLB 作为主结果。
- 前端全英文、8–11px 的正文/按钮非常普遍；不满足“正文 ≥16px、主按钮 ≥44px”。
- 审计开始时后端只有 SQLite；本轮已新增 PostgreSQL 适配器、任务 Worker 和 Compose 骨架。

## 4. 本轮不删除任何既有能力

保留不变：

- `backend/app/db.py` 的虚拟耗材账本和 admin/guest 规则；
- `backend/app/slicer.py` 的真实 Orca CLI 链；
- `frontend/src/components/RealModules.tsx` / `VoronMachine.tsx` 及 8 个模块 GLB；
- 4,526 placements 的 CAD 索引和零件选择；
- 现有 Image3D 多 Provider、成本授权与共享额度。

## 5. 纠偏顺序

1. 彩色 GLB 成为主资产；STL/3MF/OBJ 从同一网格派生，禁止先转 STL 再作为唯一展示。
2. 成品/收藏/桌宠传递彩色 GLB；打印切片继续使用 STL/3MF。
3. 统一模型检查/修复/导出，并明确打印可行性。
4. 中文 UI、字号与按钮尺寸、普通/高级模式分层。
5. 桌宠（浏览器 Transparent Pet + Tauri 壳）和独立部署（Docker/Postgres/Worker）。
6. 按 12 项验收逐项提供 PASS/PARTIAL/BLOCKED 证据，不虚报。

## 6. 当前验收结论

- 彩色 GLB 主资产：**PASS**（Mock/TripoSR + 浏览器预览）
- 可切片 STL/3MF：**PARTIAL**（STL 真实可用，3MF 已生成但未接上传/切片）
- 数字孪生整机：**PASS（既有证据）**
- 真实 G-code 驱动：**PASS（既有证据）**
- 逐层沉积：**PASS（既有证据）**
- 虚拟耗材：**PASS（既有测试）**
- 管理员/首件免费/扣费：**PASS（既有测试）**
- 彩色成品取出：**PASS**（成品/收藏/浏览器桌宠）
- 添加到 Windows 桌面：**PARTIAL**（浏览器桌宠 PASS；Tauri 构建 BLOCKED）
- 关闭 Harness 独立运行：**PARTIAL**（PostgreSQL 已在本地 17.2 验证；Compose/Tauri 因无 docker/cargo 仍 BLOCKED）
