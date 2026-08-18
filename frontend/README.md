# 合同审查审批系统 · 前端

与后端 FastAPI（`main:app`）一一对应的演示前端。零依赖，原生 HTML + CSS + JS，
直接用浏览器打开 `index.html` 即可，无需构建。

## 启动

后端先起（默认监听 `http://127.0.0.1:8000`）：

```powershell
# 项目根目录
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

打开前端任选其一：

- 直接双击 `frontend/index.html`（推荐）
- 或在 `frontend/` 下起一个静态服务：`uv run python -m http.server 8080`，访问 [http://127.0.0.1:8080/](http://127.0.0.1:8080/)

首次登录：admin / 123456（也可注册 reviewer）。

## 接口对应表

所有调用走 `window.CRSApi.*`，与 `.spec.md` 中 2.4.7「调用端能力（5 个模块）」对齐：

| 模块 | 后端路径 | 前端入口 |
|---|---|---|
| 认证 | `/api/auth/{register,login,me}` | `CRSApi.auth` |
| 任务 | `/api/tasks/{trigger,GET,GET/{id},POST/{id}/retry}` | `CRSApi.tasks` |
| 规则 | `/api/rules` (GET/POST/PUT/DELETE) | `CRSApi.rules` |
| 命中 | `/api/hits` (GET/POST/{id}/confirm\|ignore) | `CRSApi.hits` |
| 日志 | `/api/logs` (GET, admin) | `CRSApi.logs` |
| 健康 | `/api/health` | `CRSApi.health` |

## 视图

- **登录**：账号密码登录 / 注册，token 存 `localStorage.crs.token`
- **任务**：拉取待办 → 入队 → 异步工作流（pending → parsing → reviewing → done / blocked）。
  - 列表分页、状态筛选、详情抽屉（附件 / 解析字段 / 命中 / 结论 / 日志）
  - 详情抽屉的解析结果按 2.4.5 的 8 基本信息 + 8 条款渲染为字段卡片，每条都带
    `raw_text` / `page_no` / `extract_status`
- **规则**：11 条默认规则的 CRUD（admin 写、reviewer 只读）
- **命中**：按任务 / 风险筛选 `rule_hits`，evidence_position 由 `page_no + clause_name` 拼接
- **日志**：admin 可见，按 task_id / log_level / log_type / 分页查询 `task_logs`

## 字段对齐

`app.js` 与 `.spec.md` 的统一属性命名约定严格保持一致：

- 任务层：`id` / `approval_code` / `approval_title` / `applicant_name` / `task_status` / `write_status`
- 附件层：`id` / `task_id` / `attachment_id` / `file_name` / `file_type` / `file_path` / `download_status`
- 解析层：`id` / `task_id` / `basic_info_json` / `clause_info_json` / `parse_status` / `parse_error`
- 命中层：`id` / `task_id` / `rule_id` / `evidence_text` / `evidence_position` / `hit_status`
- 结果层：`id` / `task_id` / `overall_risk_level` / `summary_text` / `focus_points_json` / `comment_text`
- 日志层：`id` / `task_id` / `log_level` / `log_type` / `log_content` / `create_time`

`evidence_position` 仅出现在命中层；解析层只保留 `page_no`。
所有解析字段（基本 / 条款）都带 `raw_text` / `page_no` / `extract_status`。

## 切换 API 地址

页面右上角 `API` 按钮即可改写 `localStorage.crs.baseUrl`，无需改代码。
