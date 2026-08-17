# STEP1 · 项目进展（阶段 0/1）

> 输出日期：2026-08-17
> 分支：`codex/stage-0-1`
> 说明：合同审查审批系统（《项目实战》2.4）第一阶段实施进展。

## 一、当前目标

完成阶段 0（项目脚手架与运行环境）和阶段 1（核心基础设施），
为后续认证、审批适配、解析、规则引擎、回写与 API 提供可运行底座。

## 二、已完成内容

### 阶段 0：项目脚手架与运行环境

- `pyproject.toml`：Python 3.12，uv 管理依赖，锁定 87 个包。
- `uv.lock`：依赖锁定文件，随仓库提交。
- `docker-compose.yml`：MySQL 8 容器，utf8mb4 字符集，镜像走国内代理源。
- `.env.example` / `.env`：全部配置项（LLM、OCR、重试、文件限制、DB、JWT、目录）。
- `.gitignore`：忽略 `.env`、`.venv`、日志、上传目录内容等，保留 `uv.lock`。

### 阶段 1：核心基础设施

- `app/config.py`：配置单例，只从项目根 `.env` 读取，忽略系统环境变量。
- `app/db.py`：MySQL engine / Session 依赖 / `init_db()`。
- `app/models/`：9 张表 ORM（8 张业务表 + `users` 支撑表）。
- `app/schemas/`：统一响应、分页、认证、任务、规则、命中、日志、解析、结果模型。
- `app/core/state_machine.py`：任务/回写/命中状态与合法流转。
- `app/core/security.py`：bcrypt 密码哈希、JWT 签发解析、种子管理员。
- `app/cache.py`：进程内 TTL 缓存（用户信息、登录态）。
- `app/core/logging.py` + `app/services/log_service.py`：文件+控制台日志、`task_logs` 落库与分页查询。
- `tests/`：安全与状态机单元测试。

## 三、数据库（真实 MySQL）

`contract_review` 库已创建 9 张表：

```text
approval_tasks / approval_attachments / contract_parses
review_rules / rule_hits / review_results
comment_logs / task_logs / users
```

- 种子管理员：`admin / 123456`（密码哈希存储）。
- `init_db()` 幂等，可重复执行。

## 四、配置要点

- 配置唯一来源：项目根 `.env`；代码默认值仅兜底。
- 改 `.env` 后重启服务生效（开发用 `uvicorn --reload`）。
- 关键可调项：`MAX_LLM_CHARS`、`OCR_CONFIDENCE_THRESHOLD`、`MAX_RETRY_COUNT`、
  `UPLOAD_MAX_MB`、`MAX_PDF_PAGES`、`HEADING_SCORE_THRESHOLD`、
  `HEADING_MAX_LENGTH`、`CLAUSE_KEYWORDS`、`DOCX_TO_PDF`、`MYSQL_IMAGE`。
- 目录支持绝对路径或相对路径（相对路径自动基于项目根解析）。

## 五、验证结果

- `uv run pytest tests -q`：5 passed，无测试失败。
- 模块导入：config/db/cache/security/logging/state_machine/models/schemas/log_service 全部通过。
- MySQL：9 张表真实建表成功，`init_db()` 幂等。
- 日志链路：`write_task_log` 落库、`list_task_logs` 分页查询成功。
- 依赖：`uv lock --check` 一致；默认环境可直接 `uv run pytest`（dev 组默认安装）。

## 六、本次 Debug 发现与修复

1. 依赖声明与实际使用不一致：`config.py` 已改用 `python-dotenv`，
   但 pyproject 仍声明未使用的 `pydantic-settings` → 已移除，并显式声明 `python-dotenv`。
2. dev 依赖默认不安装：`[project.optional-dependencies]` 导致全新环境 `uv run pytest`
   报 "program not found" → 改为 uv 的 `[dependency-groups] dev`，`uv sync` 默认安装。
3. LLM 配置缺少校验：`LLM_API_KEY` 已填但 `LLM_BASE_URL` 不是 http(s) 地址时静默失效
   → `config.py` 增加 UserWarning，明确提示密钥与地址放错位置。

## 七、遗留问题 / 待办

- **LLM 配置待修正**：当前 `.env` 的 `LLM_BASE_URL` 不是 http(s) 地址（疑似误填密钥），
  需用户确认后修正；修改后会触发启动警告。
- MySQL 运行依赖 Docker Desktop，国内拉镜像已切 DaoCloud 代理源，备选源见 `.env` 注释。
- 阶段 0/1 尚未实现：认证接口、审批适配层、工具层、解析服务、规则引擎、回写、API、前端契约。

## 八、下一步

- 阶段 2：认证服务与接口（`auth_service`、`deps`、`/api/auth`）。
- 阶段 3：Mock 审批数据与适配层。
- 阶段 4-7：工具层、解析服务（LLM 抽取）、规则引擎、回写服务。
