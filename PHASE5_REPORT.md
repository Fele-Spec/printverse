# PrintVerse Phase 5 纠偏报告

日期：2026-11-06 · 目标：保住六大模块，恢复被误删（本审计证明没有删除）并补齐真正缺失的链路。

## 0. 审计结论

- Git 全历史没有任何删除文件；上一阶段没有删除耗材、G-code、机械或数字孪生模块。
- 当前真正缺失的是：彩色 GLB 主资产链、统一模型处理、桌宠/Tauri、独立部署/PostgreSQL。
- 本阶段新增功能不覆盖已有有效修改。

详见 [PHASE5_AUDIT.md](PHASE5_AUDIT.md) 和 [PRODUCT_ARCHITECTURE.md](PRODUCT_ARCHITECTURE.md)。

## 1. 已实现并验证

| 项目 | 状态 | 证据 |
|---|---|---|
| 图片→彩色 GLB | **PASS** | Mock、TripoSR、三视图视觉外壳都输出 glb；`texture_status=VERTEX_COLOR` |
| GLB + STL + 3MF + OBJ 同源导出 | **PASS** | `backend/app/mesh_prep.py`，`test_mesh_prep` 2 项 |
| 3MF 上传并真实 Orca 切片 | **PASS** | 3MF 上传返回 200、61 层、10.04 g、display.stl |
| STEP/DXF 工程图导入 | **PASS（基础）** | 20 mm STEP → 100 层/3.978 g；40×20 mm DXF 拉伸 → 15 层/1.934 g |
| 三视图本地重建 | **PASS** | `multiview_local`，正面/侧面/顶面；`phase5_multiview.png` |
| 彩色成品显示 | **PASS** | `phase5_finished_color.png`：彩色模型在热床 |
| 成品→收藏→桌宠 | **PASS（浏览器）** | `phase5_pet.png`；零 page/console error |
| 中文 UI | **PASS（主流程）** | `phase5_dashboard_cn.png`、`phase5_color_glb_panel.png` |
| 正文 ≥16px / 主按钮 ≥44px | **PASS（主流程）** | `styles.css` Phase-5 overrides |
| 彩色 GLB 不再被 STL 替代 | **PASS** | Image3D `output_format=glb`；STL 只作为切片派生 |
| 虚拟耗材/首件免费/admin/扣费 | **PASS（既有测试）** | `test_ledger.py` 6 项；16 passed（默认）；3 个 PostgreSQL 集成测试按环境变量跳过 |
| 独立 Worker | **PASS** | `WORKER_ONCE=1` 消费队列任务完成；`docs/reports/worker_test.json` |
| Compose 配置 | **PASS** | 独立 `docker-compose config` 退出 0；镜像构建仍 BLOCKED |
| 真实 G-code 机械运动/逐层沉积 | **PASS（既有证据）** | `GCODE_TEST_REPORT.md`、`phase2_e2e.json` |

## 2. 12 项验收矩阵

| # | 验收 | 状态 | 说明 |
|---:|---|---|---|
| 1 | 图片生成彩色 GLB | **PASS** | Mock/TripoSR/三视图；GLB 主资产 |
| 2 | 生成可切片 STL/3MF | **PASS** | STL + 3MF 实测；STEP 导入也实测 |
| 3 | Voron 整机机械结构 | **PASS** | 既有 4,526 placements / 8 GLB |
| 4 | 真实 G-code 驱动喷头/龙门 | **PASS** | 既有真实 Orca/G-code 证据 |
| 5 | 逐层材料沉积 | **PASS** | PrintSimulator 使用解析后的真实 moves |
| 6 | 虚拟耗材质量 | **PASS** | 16 passed（默认）+ 3 个 PostgreSQL 测试；3.978 g / 10.040 g 实测 |
| 7 | 管理员免收费 | **PASS** | `test_admin_unlimited_does_not_touch_first_print` |
| 8 | 新用户首次免费 | **PASS** | `test_first_print_is_free_once` |
| 9 | 后续打印扣费 | **PASS** | `test_first_print_is_free_once` 第二次扣 3.978 g |
| 10 | 完成后取出彩色模型 | **PASS** | 彩色 GLB 到成品/收藏；截图 |
| 11 | 添加到 Windows 桌面 | **PARTIAL** | 浏览器透明桌宠 PASS；Tauri 壳已写，但本机无 Cargo，未构建 MSI |
| 12 | 关闭 Harness 后独立运行 | **PARTIAL** | PostgreSQL 适配器已用本地 17.2 验证；Dockerfile/compose/worker 已写；本机无 Docker，Compose/Tauri 仍 BLOCKED |

## 3. 未能宣称完成的部分

1. **工程图转 CAD**：已支持封闭 DXF 轮廓拉伸为网格；尚未实现从扫描图片识别尺寸/约束并生成参数化 CAD。
2. **精确壁厚/支撑**：mesh API 提供 ray-cast 近似壁厚与悬垂面积，不是 Orca 切片器标定结果，子项为 **PARTIAL**。
3. **Tauri Windows 客户端**：源码 scaffolding 已写，构建 `BLOCKED`（本机无 cargo/MSVC）。
4. **Docker Compose**：文件已提供，`BLOCKED`（本机无 docker）；容器内没有 Orca，真实切片需 Windows 工具。
5. **Kimi**：账户 429 余额不足；未产生付费调用。
6. **TokenHub**：无 Key/账号端点；未调用、未产生费用。
7. **Stable Fast 3D**：未安装；Windows/许可证待审查。

## 4. 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q -p no:cacheprovider
# 16 passed

node scripts\phase5_ui_color_test.mjs
node scripts\phase5_full_acceptance.mjs
```

浏览器证据：

- `BEFORE_AFTER_SCREENSHOTS/phase5_dashboard_cn.png`（普通模式，高级工具默认隐藏）
- `BEFORE_AFTER_SCREENSHOTS/phase5_color_glb_panel.png`
- `BEFORE_AFTER_SCREENSHOTS/phase5_finished_color.png`
- `BEFORE_AFTER_SCREENSHOTS/phase5_pet.png`
- `BEFORE_AFTER_SCREENSHOTS/phase5_multiview.png`

## 5. 结论

**全功能架构：PARTIAL。**  
彩色 GLB 主链路、模型处理、虚拟打印、耗材、收藏/桌宠浏览器链路已打通；PostgreSQL 适配器已本地验证；真实 Windows 桌宠构建、Docker Compose 验证、工程图转 CAD、精确壁厚/支撑仍是未完成项。没有把未完成项标记为完成。
