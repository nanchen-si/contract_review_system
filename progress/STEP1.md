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

## 三、生成的 .py 文件说明（阶段 0/1）

> 本次生成的 Python 文件逐文件说明：列出文件中的类、函数及作用。

### app/config.py

- `class Settings(BaseModel)`：项目配置模型，字段与 `.env.example` 一一对应。
  - 覆盖 LLM、OCR 置信度、重试次数、文件/页数限制、标题识别参数、数据库、JWT、管理员、适配器与目录等全部配置。
  - 属性 `clause_keyword_list`：把 `CLAUSE_KEYWORDS` 逗号分隔字符串转成关键词列表，供标题识别与规则复用。
  - 方法 `model_post_init`：把目录字段解析为项目根下的绝对路径；校验 `LLM_BASE_URL` 必须是 http(s) 开头，否则发出 UserWarning。
- `def get_settings()`：`lru_cache` 单例，从项目根 `.env` 读取配置，忽略系统环境变量。
- 模块常量 `BASE_DIR`：项目根目录绝对路径。

### app/db.py

- `def get_engine()`：创建 MySQL engine（`pool_pre_ping`，charset 取自 `DB_CHARSET`），进程内复用。
- `def get_session()`：FastAPI 依赖生成器，yield Session，结束后自动关闭。
- `def init_db()`：`Base.metadata.create_all` 创建 9 张表，并调用 `ensure_admin_seed()` 写入种子管理员；幂等，可重复执行。

### app/models/（ORM，9 张表）

- `app/models/base.py`
  - `class Base(DeclarativeBase)`：SQLAlchemy 声明式基类，统一元数据。
- `app/models/user.py`
  - `class User`：`users` 支撑表（id、username、password_hash、role、审计字段）。
- `app/models/approval.py`
  - `class ApprovalTask`：审批任务表，`approval_code` 为唯一去重键（task_status、write_status、审计字段）。
  - `class ApprovalAttachment`：审批附件表（task_id、attachment_id、file_name、file_type、file_path、download_status、审计字段）。
- `app/models/parse.py`
  - `class ContractParse`：解析结果表（basic_info_json、clause_info_json、parse_status、parse_error）。
- `app/models/rule.py`
  - `class ReviewRule`：审查规则表（rule_code 唯一、rule_name、risk_level、rule_status、match_mode、match_text、suggestion_text）。
  - `class RuleHit`：规则命中表（evidence_text、evidence_position、hit_status）。
- `app/models/result.py`
  - `class ReviewResult`：审查结果表（overall_risk_level、summary_text、focus_points_json、comment_text）。
  - `class CommentLog`：回写日志表（write_status、write_response_text）。
- `app/models/log.py`
  - `class TaskLog`：全链路任务日志表（task_id、log_level、log_type、log_content）。
- `app/models/__init__.py`：统一导入并导出全部 ORM 模型，导入本模块即注册全部表。

### app/schemas/（Pydantic 请求/响应模型）

- `app/schemas/common.py`
  - `class ApiResponse(BaseModel, Generic[T])`：统一响应结构（code、message、data）。
  - `class PageResult(BaseModel, Generic[T])`：分页结果（items、total、page、size）。
- `app/schemas/auth.py`
  - `class RegisterRequest` / `class LoginRequest`：注册/登录请求（username、password）。
  - `class TokenResponse`：登录响应（token、token_type、expires_in）。
  - `class UserOut`：用户信息输出（id、username、role）。
- `app/schemas/task.py`
  - `class TaskSummary`：任务列表项。
  - `class TaskDetail`：任务详情聚合（attachments、parse、hits、result）。
  - `class TaskStatusFilter`：任务列表筛选（task_status、page、size）。
- `app/schemas/rule.py`
  - `class RuleCreate`：新增规则请求。
  - `class RuleUpdate`：更新规则请求（字段全部可选）。
  - `class RuleOut`：规则输出。
- `app/schemas/hit.py`
  - `class HitOut`：命中输出（含 rule_name、risk_level、evidence_text、evidence_position）。
  - `class HitConfirmRequest`：命中人工确认请求（hit_status）。
- `app/schemas/log.py`
  - `class LogOut`：日志输出。
  - `class LogQuery`：日志查询参数。
- `app/schemas/parse.py`
  - `class ParseOut`：解析结果输出。
- `app/schemas/result.py`
  - `class ResultOut`：审查结果输出。

### app/core/state_machine.py

- 常量：`TASK_STATUSES`（pending/parsing/reviewing/blocked/done）、`WRITE_STATUSES`、`HIT_STATUSES`。
- `def can_transition(current, target)`：判断任务状态流转是否合法。
- `def retry_stage_for(failure_stage)`：blocked 重试后应回到 parsing 还是 reviewing。

### app/core/security.py

- `def hash_password(plain)`：bcrypt 哈希密码。
- `def verify_password(plain, hashed)`：校验密码。
- `def create_access_token(user_id, role)`：签发 JWT（sub/role/exp）。
- `def decode_access_token(token)`：解析并校验 JWT，返回 payload。
- `def ensure_admin_seed()`：无 admin 时创建种子管理员（账号密码来自 Settings）。

### app/cache.py

- `class TTLCache`：进程内 TTL 缓存。
  - `get(key)`：读取缓存，过期返回 None。
  - `set(key, value, ttl)`：写入缓存。
  - `delete(key)`：删除缓存。
- 模块级函数：`get_user_cache(username)`、`put_user_cache(user)`、`invalidate_user_cache(username)`（用户信息缓存）；
  `get_token_session(token)`、`put_token_session(token, user)`（登录态缓存）。

### app/core/logging.py

- `def setup_logging()`：初始化 logger，输出到 LOG_DIR 文件与控制台。
- `def get_logger(name)`：返回命名 logger。

### app/services/log_service.py

- `def write_task_log(task_id, log_level, log_type, log_content)`：写一条 task_logs。
- `def list_task_logs(task_id, log_level, log_type, page, size)`：分页查询日志，返回 PageResult。

### tests/（单元测试）

- `tests/test_security.py`
  - `test_password_hash_and_verify()`：密码哈希与校验。
  - `test_token_roundtrip()`：token 签发与解析。
- `tests/test_state_machine.py`
  - `test_valid_transitions()`：合法流转。
  - `test_invalid_transitions()`：非法流转被拒绝。
  - `test_retry_stage_for()`：blocked 重试回到正确阶段。

## 四、数据库（真实 MySQL）

`contract_review` 库已创建 9 张表：

```text
approval_tasks / approval_attachments / contract_parses
review_rules / rule_hits / review_results
comment_logs / task_logs / users
```

- 种子管理员：`admin / 123456`（密码哈希存储）。
- `init_db()` 幂等，可重复执行。

## 五、配置要点

- 配置唯一来源：项目根 `.env`；代码默认值仅兜底。
- 改 `.env` 后重启服务生效（开发用 `uvicorn --reload`）。
- 关键可调项：`MAX_LLM_CHARS`、`OCR_CONFIDENCE_THRESHOLD`、`MAX_RETRY_COUNT`、
  `UPLOAD_MAX_MB`、`MAX_PDF_PAGES`、`HEADING_SCORE_THRESHOLD`、
  `HEADING_MAX_LENGTH`、`CLAUSE_KEYWORDS`、`DOCX_TO_PDF`、`MYSQL_IMAGE`。
- 目录支持绝对路径或相对路径（相对路径自动基于项目根解析）。

## 六、验证结果

- `uv run pytest tests -q`：5 passed，无测试失败。
- 模块导入：config/db/cache/security/logging/state_machine/models/schemas/log_service 全部通过。
- MySQL：9 张表真实建表成功，`init_db()` 幂等。
- 日志链路：`write_task_log` 落库、`list_task_logs` 分页查询成功。
- 依赖：`uv lock --check` 一致；默认环境可直接 `uv run pytest`（dev 组默认安装）。

## 七、本次 Debug 发现与修复

1. 依赖声明与实际使用不一致：`config.py` 已改用 `python-dotenv`，
   但 pyproject 仍声明未使用的 `pydantic-settings` → 已移除，并显式声明 `python-dotenv`。
2. dev 依赖默认不安装：`[project.optional-dependencies]` 导致全新环境 `uv run pytest`
   报 "program not found" → 改为 uv 的 `[dependency-groups] dev`，`uv sync` 默认安装。
3. LLM 配置缺少校验：`LLM_API_KEY` 已填但 `LLM_BASE_URL` 不是 http(s) 地址时静默失效
   → `config.py` 增加 UserWarning，明确提示密钥与地址放错位置。

## 八、遗留问题 / 待办

- **LLM 配置待修正**：当前 `.env` 的 `LLM_BASE_URL` 不是 http(s) 地址（疑似误填密钥），
  需用户确认后修正；修改后会触发启动警告。
- MySQL 运行依赖 Docker Desktop，国内拉镜像已切 DaoCloud 代理源，备选源见 `.env` 注释。
- 阶段 0/1 尚未实现：认证接口、审批适配层、工具层、解析服务、规则引擎、回写、API、前端契约。

## 九、下一步

- 阶段 2：认证服务与接口（`auth_service`、`deps`、`/api/auth`）。
- 阶段 3：Mock 审批数据与适配层。
- 阶段 4-7：工具层、解析服务（LLM 抽取）、规则引擎、回写服务。
