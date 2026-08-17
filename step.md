# 合同审批审查系统 实施步骤

> 依据：`.spec.md`（v0.1）与技术选型讨论
> 执行方式：按 Step 顺序逐步实现，每步完成可独立验证
> 工具链：Python 3.12 + uv + Docker Desktop

## 全局约束

- 项目根目录：`contract-review/`（`main.py` 在根目录）。
- 依赖管理：uv，`pyproject.toml` 为唯一依赖声明，`uv.lock` 由 `uv lock` 生成。
- 数据库：MySQL 8（docker compose），连接参数全部来自 `.env`。
- 命名规范（coding-skill）：模块/目录小写下划线，类大驼峰，函数小写下划线，常量全大写。
- 数据库规范：主键 `id`，业务表含审计字段，无外键、无额外索引，逻辑删除；字段以 `.spec.md` 第 6 章为准。
- 配置规范：所有客户端配置放 `.env`，`app/config.py` 统一读取。
- 解耦约定：`api → services → tools/graph/adapters`，模块间通过 schemas/模型交互。
- 编码：UTF-8，中文注释与日志，函数必须有一行作用说明。

## 项目技术栈

| 类别 | 技术 | 用途 |
|---|---|---|
| 语言 | Python 3.12 | 全项目实现语言 |
| 包管理 | uv（pyproject.toml + uv.lock） | 依赖声明、锁定与运行 |
| 后端框架 | FastAPI + Uvicorn | REST API、Pydantic 校验、自动 OpenAPI |
| 编排 | LangGraph | 固定顺序工作流图，state 传递数据，节点内调用 LLM |
| LLM | OpenAI 兼容 API（langchain-openai/openai SDK） | 字段抽取、语义规则判断、评论生成；model/base_url/api_key 走 `.env` |
| 数据库 | MySQL 8（Docker）+ SQLAlchemy 2.0 + PyMySQL | 9 张业务表持久化 |
| 任务调度 | asyncio.Queue + FastAPI 后台任务 | 人工触发后异步执行工作流，状态以数据库为准 |
| 文档解析 | pdfplumber + python-docx | PDF/Word 合同文本提取（按页/段落） |
| 认证与安全 | PyJWT + passlib[bcrypt] | token 签发校验、密码哈希 |
| 配置管理 | pydantic-settings | 读取 `.env`，统一配置单例 |
| 文件与上传 | python-multipart | 附件上传支持 |
| 测试 | pytest + pytest-asyncio + httpx | 单元测试、接口冒烟测试 |
| 容器 | Docker Desktop + docker compose | 本地启动 MySQL 服务 |
| 前端 | 暂缓（预留 REST API 契约） | 后续按 OpenAPI 对接 |

## 统一属性命名约定

所有类中语义相同的属性必须使用同一名称，以下为对齐表：

| 语义 | 统一属性名 |
|---|---|
| 主键 | `id` |
| 任务标识 | `task_id` |
| 审批系统侧实例标识 | `instance_id` |
| 审批单业务编号 | `approval_code` |
| 审批标题 | `approval_title` |
| 申请人 | `applicant_name` |
| 申请时间 | `application_time` |
| 附件标识 | `attachment_id` |
| 文件名 / 文件类型 / 文件路径 | `file_name` / `file_type` / `file_path` |
| 用户标识 | `user_id` |
| 登录名 / 密码哈希 / 角色 | `username` / `password_hash` / `role` |
| 任务状态 / 回写状态 / 下载状态 / 解析状态 / 命中状态 / 规则状态 | `task_status` / `write_status` / `download_status` / `parse_status` / `hit_status` / `rule_status` |
| 风险等级 / 总风险等级 | `risk_level` / `overall_risk_level` |
| 规则编码 / 规则名称 / 匹配模式 / 匹配文本 / 建议文本 | `rule_code` / `rule_name` / `match_mode` / `match_text` / `suggestion_text` |
| 证据文本 / 证据位置 | `evidence_text` / `evidence_position` |
| 摘要 / 关注点 / 评论 | `summary_text` / `focus_points_json` / `comment_text` |
| 日志级别 / 日志类型 / 日志内容 | `log_level` / `log_type` / `log_content` |
| 回写响应文本 | `write_response_text` |
| 解析错误 | `parse_error` |
| 审计字段 | `create_user_id` / `create_time` / `update_user_id` / `update_time` / `is_deleted` |
| 分页 | `page` / `size` / `total` / `items` |

## 阶段 0：项目脚手架与运行环境

### Step 1：初始化 uv 项目与依赖

文件：创建 `pyproject.toml`（`uv.lock` 由 `uv lock` 生成）
目的：建立 uv 管理的 Python 项目骨架，锁定运行与开发依赖。
文件详情：
- `pyproject.toml`
  - `[project]`：name=contract-review，requires-python>=3.12
  - `[project.optional-dependencies]` dev：pytest、pytest-asyncio
  - 运行依赖：fastapi、uvicorn[standard]、sqlalchemy、pymysql、cryptography、langgraph、langchain-openai、pydantic-settings、pyjwt、passlib[bcrypt]、pdfplumber、python-docx、python-multipart、httpx
验证：`uv lock && uv run python -c "import fastapi"`

### Step 2：Docker Compose（MySQL）

文件：创建 `docker-compose.yml`
目的：以 Docker 启动 MySQL 8 数据库服务，供本地开发与 demo 使用。
文件详情：
- `docker-compose.yml`
  - 服务 `mysql`：image=mysql:8，container_name=contract-mysql
  - 环境变量：MYSQL_DATABASE=contract_review、MYSQL_ROOT_PASSWORD 读取 `.env` 的 `DB_PASSWORD`
  - ports：3306:3306
  - volumes：命名卷 `mysql_data` 挂载 `/var/lib/mysql`
  - healthcheck：`mysqladmin ping`
验证：`docker compose up -d mysql && docker compose ps`

### Step 3：环境变量与忽略文件

文件：创建 `.env.example`、`.gitignore`
目的：提供全部环境变量模板（LLM/DB/服务/权限/适配器/目录），用户复制为 `.env` 后填写；忽略本地环境与生成文件。
文件详情：
- `.env.example`
  - 变量：LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、DB_HOST、DB_PORT、DB_USER、DB_PASSWORD、DB_NAME、APP_HOST、APP_PORT、SECRET_KEY、TOKEN_EXPIRE_MINUTES、ADMIN_USERNAME、ADMIN_PASSWORD、APPROVAL_ADAPTER、MOCK_DATA_DIR、UPLOAD_DIR、LOG_DIR
  - 预留（注释形式）：LLM_PARSE_MODEL、LLM_RULE_MODEL、LLM_WRITEBACK_MODEL
- `.gitignore`
  - 忽略：`.env`、`uploads/`、`logs/`、`__pycache__/`、`.venv/`、`uv.lock`（保留则删）等
验证：`uv run python -c "from dotenv import dotenv_values; print(sorted(dotenv_values('.env.example')))"`

## 阶段 1：核心基础设施

### Step 4：配置模块

文件：创建 `app/__init__.py`、`app/config.py`
目的：统一读取 `.env`，向全项目提供配置单例。
文件详情：
- `app/config.py`
  - `class Settings(BaseSettings)`：配置模型
    - `llm_api_key: str`、`llm_base_url: str`、`llm_model: str`：LLM 接入配置
    - `db_host: str`、`db_port: int`、`db_user: str`、`db_password: str`、`db_name: str`：MySQL 连接配置
    - `app_host: str`、`app_port: int`、`secret_key: str`、`token_expire_minutes: int`：服务与令牌配置
    - `admin_username: str`、`admin_password: str`：种子管理员配置
    - `approval_adapter: str`、`mock_data_dir: str`、`upload_dir: str`、`log_dir: str`：适配器与目录配置
  - `def get_settings()`：加载 `.env` 并返回 Settings 单例（lru_cache）
验证：`uv run python -c "from app.config import get_settings; print(get_settings().db_name)"`

### Step 5：数据库连接

文件：创建 `app/db.py`
目的：建立 SQLAlchemy engine 与 Session 依赖，并初始化数据库表结构。
文件详情：
- `app/db.py`
  - `def get_engine()`：创建 engine（pool_pre_ping，charset=utf8mb4）
  - `def get_session()`：FastAPI 依赖，yield Session
  - `def init_db()`：建表（Base.metadata.create_all）并调用 `ensure_admin_seed()`
验证：`uv run python -c "from app.db import get_engine; print(get_engine())"`

### Step 6：ORM 模型（9 张表）

文件：创建 `app/models/__init__.py`、`app/models/base.py`、`app/models/user.py`、`app/models/approval.py`、`app/models/parse.py`、`app/models/rule.py`、`app/models/result.py`、`app/models/log.py`
目的：定义 9 张表对应的 ORM 模型，字段与 `.spec.md` 第 6 章及属性命名约定一致。
文件详情：
- `app/models/base.py`
  - `class Base(DeclarativeBase)`：声明式基类，统一元数据
- `app/models/user.py`
  - `class User(Base)`：users 表
    - `id`：主键；`username`：登录账号（唯一）；`password_hash`：密码哈希；`role`：角色
    - `create_time`、`update_time`、`is_deleted`：审计与逻辑删除
- `app/models/approval.py`
  - `class ApprovalTask(Base)`：approval_tasks 表
    - `id`：主键；`approval_code`（唯一）；`approval_title`；`applicant_name`
    - `task_status`、`write_status`
    - `create_user_id`、`create_time`、`update_user_id`、`update_time`、`is_deleted`
  - `class ApprovalAttachment(Base)`：approval_attachments 表
    - `id`：主键；`task_id`；`attachment_id`；`file_name`；`file_type`；`file_path`；`download_status`
    - 审计与逻辑删除字段
- `app/models/parse.py`
  - `class ContractParse(Base)`：contract_parses 表
    - `id`：主键；`task_id`；`basic_info_json`；`clause_info_json`；`parse_status`；`parse_error`
    - `create_time`、`update_time`
- `app/models/rule.py`
  - `class ReviewRule(Base)`：review_rules 表
    - `id`：主键；`rule_code`（唯一）；`rule_name`；`risk_level`；`rule_status`；`match_mode`；`match_text`；`suggestion_text`
    - `create_time`、`update_time`
  - `class RuleHit(Base)`：rule_hits 表
    - `id`：主键；`task_id`；`rule_id`；`evidence_text`；`evidence_position`；`hit_status`
    - `create_time`、`update_time`
- `app/models/result.py`
  - `class ReviewResult(Base)`：review_results 表
    - `id`：主键；`task_id`；`overall_risk_level`；`summary_text`；`focus_points_json`；`comment_text`
    - `create_time`、`update_time`
  - `class CommentLog(Base)`：comment_logs 表
    - `id`：主键；`task_id`；`write_status`；`write_response_text`；`create_time`
- `app/models/log.py`
  - `class TaskLog(Base)`：task_logs 表
    - `id`：主键；`task_id`；`log_level`；`log_type`；`log_content`；`create_time`
验证：`uv run python -c "from app.db import init_db; init_db()"` 建表成功

### Step 7：Pydantic Schemas

文件：创建 `app/schemas/__init__.py`、`app/schemas/common.py`、`app/schemas/auth.py`、`app/schemas/task.py`、`app/schemas/rule.py`、`app/schemas/hit.py`、`app/schemas/log.py`、`app/schemas/parse.py`
目的：定义 API 请求/响应模型，保证接口契约稳定并供前端对接。
文件详情：
- `app/schemas/common.py`
  - `class ApiResponse(BaseModel, Generic[T])`：统一响应，属性 `code`、`message`、`data`
  - `class PageResult(BaseModel, Generic[T])`：分页结果，属性 `items`、`total`、`page`、`size`
- `app/schemas/auth.py`
  - `class RegisterRequest(BaseModel)`：属性 `username`、`password`
  - `class LoginRequest(BaseModel)`：属性 `username`、`password`
  - `class TokenResponse(BaseModel)`：属性 `token`、`token_type`、`expires_in`
  - `class UserOut(BaseModel)`：属性 `id`、`username`、`role`
- `app/schemas/task.py`
  - `class TaskSummary(BaseModel)`：属性 `id`、`approval_code`、`approval_title`、`applicant_name`、`task_status`、`write_status`
  - `class TaskDetail(BaseModel)`：属性 `id`、`approval_code`、`approval_title`、`applicant_name`、`task_status`、`write_status`、`attachments`、`parse`、`hits`、`result`
  - `class TaskStatusFilter(BaseModel)`：属性 `task_status`、`page`、`size`
- `app/schemas/rule.py`
  - `class RuleCreate(BaseModel)`：属性 `rule_code`、`rule_name`、`risk_level`、`rule_status`、`match_mode`、`match_text`、`suggestion_text`
  - `class RuleUpdate(BaseModel)`：属性同 RuleCreate（全部可选）
  - `class RuleOut(BaseModel)`：属性 `id` 加 RuleCreate 全部属性
- `app/schemas/hit.py`
  - `class HitOut(BaseModel)`：属性 `id`、`task_id`、`rule_id`、`rule_name`、`risk_level`、`evidence_text`、`evidence_position`、`hit_status`
  - `class HitConfirmRequest(BaseModel)`：属性 `hit_status`
- `app/schemas/log.py`
  - `class LogOut(BaseModel)`：属性 `id`、`task_id`、`log_level`、`log_type`、`log_content`、`create_time`
  - `class LogQuery(BaseModel)`：属性 `task_id`、`log_level`、`log_type`、`page`、`size`
- `app/schemas/parse.py`
  - `class ParseOut(BaseModel)`：属性 `id`、`task_id`、`basic_info_json`、`clause_info_json`、`parse_status`、`parse_error`
验证：`uv run python -c "from app.schemas.common import ApiResponse; print(ApiResponse)"`

### Step 8：状态机

文件：创建 `app/core/__init__.py`、`app/core/state_machine.py`
目的：集中定义任务/回写/命中状态常量与合法流转规则。
文件详情：
- `app/core/state_machine.py`
  - 常量 `TASK_STATUSES`、`WRITE_STATUSES`、`HIT_STATUSES`：状态取值集合
  - `def can_transition(current, target)`：判断任务状态流转是否合法
  - `def retry_stage_for(task_status)`：blocked 重试后应回到 parsing 还是 reviewing
验证：`uv run python -c "from app.core.state_machine import can_transition; print(can_transition('pending','parsing'))"`

### Step 9：安全与令牌

文件：创建 `app/core/security.py`
目的：提供密码哈希、token 签发/解析与管理员种子账号能力。
文件详情：
- `app/core/security.py`
  - `def hash_password(plain)`：bcrypt 哈希密码
  - `def verify_password(plain, hashed)`：校验密码
  - `def create_access_token(user_id, role)`：签发 JWT
  - `def decode_access_token(token)`：解析并校验 JWT，返回 user_id/role
  - `def ensure_admin_seed()`：无 admin 时创建种子管理员（账号密码来自 Settings）
验证：单元测试 `test_security.py`（哈希/校验/签发/解析）

### Step 10：缓存

文件：创建 `app/cache.py`
目的：提供进程内 TTL 缓存，缓存用户信息与登录态（demo 无 Redis）。
文件详情：
- `app/cache.py`
  - `class TTLCache`：通用 TTL 缓存
    - `def get(key)`：读取缓存；`def set(key, value, ttl)`：写入缓存；`def delete(key)`：删除缓存
  - `def get_user_cache(username)` / `put_user_cache(user)` / `invalidate_user_cache(username)`：用户信息缓存读写
  - `def get_token_session(token)` / `put_token_session(token, user)`：登录态缓存读写
验证：`uv run python -c "from app.cache import TTLCache; c=TTLCache(); c.set('a',1); print(c.get('a'))"`

### Step 11：日志基础设施

文件：创建 `app/core/logging.py`、`app/services/log_service.py`
目的：统一日志输出（文件 + 控制台）并持久化任务日志到 `task_logs`。
文件详情：
- `app/core/logging.py`
  - `def setup_logging()`：初始化 logger，输出到 LOG_DIR 与控制台
  - `def get_logger(name)`：返回命名 logger
- `app/services/log_service.py`
  - `def write_task_log(task_id, log_level, log_type, log_content)`：写 task_logs
  - `def list_task_logs(task_id, log_level, log_type, page, size)`：分页查询日志，返回 PageResult
验证：`uv run python -c "from app.services.log_service import write_task_log; write_task_log(None,'info','task','ok')"`

## 阶段 2：认证与权限

### Step 12：认证服务

文件：创建 `app/services/auth_service.py`
目的：实现注册、登录、用户查询与缓存读写。
文件详情：
- `app/services/auth_service.py`
  - `def register_user(username, password)`：注册 reviewer 账号（唯一性校验、密码哈希、写库并缓存）
  - `def login_user(username, password)`：校验密码并签发 token、缓存登录态
  - `def get_user_by_username(username)`：先缓存后库查询用户
  - `def get_user_by_id(user_id)`：按 id 查询用户
验证：单元测试 `test_auth.py`（注册/重复注册/登录成功/密码错误）

### Step 13：认证接口与依赖

文件：创建 `app/core/deps.py`、`app/api/__init__.py`、`app/api/auth.py`
目的：暴露注册/登录接口，并提供当前用户与 admin 校验依赖。
文件详情：
- `app/core/deps.py`
  - `def get_current_user()`：从 token 解析当前用户（缓存优先），失败抛 401
  - `def require_admin()`：校验当前用户为 admin，否则抛 403
- `app/api/auth.py`
  - `def register()`：POST /api/auth/register
  - `def login()`：POST /api/auth/login
  - `def me()`：GET /api/auth/me
验证：启动后可 curl 注册/登录

## 阶段 3：审批适配层与 Mock 数据

### Step 14：Mock 数据与样例合同

文件：创建 `mock/approvals.json`、`scripts/gen_mock_contracts.py`（生成 `mock/attachments/` 三份 docx）
目的：准备可演示的假审批单与高/中/低风险样例合同。
文件详情：
- `mock/approvals.json`
  - 数据：3 个审批单，字段含 `instance_id`、`approval_code`、`approval_title`、`applicant_name`、`application_time`、`attachments`
- `scripts/gen_mock_contracts.py`
  - `def gen_high_risk_contract()`：生成高风险合同 docx（预付款 80%、自动续约、无保密条款）
  - `def gen_medium_risk_contract()`：生成中风险合同 docx（缺验收标准、境外管辖地）
  - `def gen_low_risk_contract()`：生成低风险合同 docx（条款齐全）
  - `def main()`：依次生成并校验文件存在
验证：`uv run python scripts/gen_mock_contracts.py`

### Step 15：适配层接口

文件：创建 `app/adapters/__init__.py`、`app/adapters/base.py`
目的：定义审批系统适配层的数据模型与统一接口，使上层与具体审批系统解耦。
文件详情：
- `app/adapters/base.py`
  - `@dataclass(slots=True) class AttachmentInfo`：附件信息
    - `attachment_id: str`、`file_name: str`、`file_type: str`
  - `@dataclass(slots=True) class ApprovalRecord`：待办列表项
    - `approval_code: str`、`approval_title: str`、`applicant_name: str`、`application_time: datetime`、`attachment_count: int`
  - `@dataclass(slots=True) class ApprovalDetail`：审批详情
    - `instance_id: str`、`approval_code: str`、`approval_title: str`、`applicant_name: str`、`application_time: datetime`、`form_data: dict`、`attachments: list[AttachmentInfo]`、`status: str`
  - `@dataclass(slots=True) class DownloadResult`：下载结果
    - `file_path: str`、`file_checksum: str`
  - `@dataclass(slots=True) class WritebackResult`：回写结果
    - `success: bool`、`response_text: str`
  - `class ApprovalAdapter(ABC)`：审批系统接口
    - `def list_pending(limit)`：拉取待办，返回 list[ApprovalRecord]
    - `def get_detail(instance_id)`：获取审批详情，返回 ApprovalDetail
    - `def download(instance_id, attachment_id, file_name)`：下载附件，返回 DownloadResult
    - `def write_comment(instance_id, review_id)`：回写评论，返回 WritebackResult
验证：`uv run python -c "from app.adapters.base import ApprovalAdapter"`

### Step 16：Mock 适配实现

文件：创建 `app/adapters/mock_client.py`
目的：实现 ApprovalAdapter 的 mock 版本，读取本地样例数据完成闭环演示。
文件详情：
- `app/adapters/mock_client.py`
  - `class MockClient(ApprovalAdapter)`
    - `def __init__(data_dir, upload_dir)`：加载 approvals.json 与附件目录
    - `def list_pending(limit)`：返回待办列表
    - `def get_detail(instance_id)`：返回审批详情与附件列表
    - `def download(instance_id, attachment_id, file_name)`：复制样例附件到 uploads，返回路径与校验值
    - `def write_comment(instance_id, review_id)`：写 mock/comments JSON，返回 WritebackResult
验证：单元测试 `test_adapters.py`（四方法各返回合法结构）

### Step 17：适配器工厂

文件：创建 `app/adapters/factory.py`
目的：按配置选择审批适配器实现，屏蔽上层对具体实现的依赖。
文件详情：
- `app/adapters/factory.py`
  - `def get_adapter()`：按 `APPROVAL_ADAPTER` 返回适配器实例（RealClient 未实现时明确报错）
验证：`uv run python -c "from app.adapters.factory import get_adapter; print(get_adapter())"`

## 阶段 4：工具层（7 个工具）

### Step 18：审批类工具

文件：创建 `app/tools/__init__.py`、`app/tools/approval_tools.py`
目的：将拉取、详情、下载三个能力封装为可被 LangGraph 节点调用的工具函数。
文件详情：
- `app/tools/approval_tools.py`
  - `def list_pending_contract_approvals(limit)`：拉取待办并去重入库，返回任务列表
  - `def get_contract_approval(instance_id)`：返回审批详情（ApprovalDetail）
  - `def download_contract_attachment(instance_id, attachment_id, file_name)`：下载附件并保存附件记录，返回本地路径
验证：脚本调用三个工具并打印结果

### Step 19：解析类工具

文件：创建 `app/tools/document_tools.py`
目的：将文档解析能力封装为工具函数，供解析节点调用。
文件详情：
- `app/tools/document_tools.py`
  - `def parse_contract_document(document_id)`：调用解析服务，返回结构化字段、原文片段与定位信息
验证：对 mock 合同调用并打印字段

### Step 20：规则类工具

文件：创建 `app/tools/review_tools.py`
目的：将规则审查流水线封装为工具函数，供规则节点调用。
文件详情：
- `app/tools/review_tools.py`
  - `def run_contract_rules(case_id)`：执行规则审查流水线，返回命中结果与风险结论
验证：对已解析任务调用并打印命中

### Step 21：结果类工具

文件：创建 `app/tools/result_tools.py`
目的：将结果保存与评论回写封装为工具函数。
文件详情：
- `app/tools/result_tools.py`
  - `def save_review_result(case_id, overall_risk_level, summary_text, focus_points_json, comment_text)`：保存审查结果
  - `def write_approval_comment(instance_id, review_id)`：生成评论并回写审批系统
验证：脚本完成保存+回写，检查 mock/comments 输出

## 阶段 5：解析服务

### Step 22：文档文本提取

文件：创建 `app/services/parse_service.py`
目的：把 PDF/Word 合同提取为带页码的文本结构，并管理解析结果落库。
文件详情：
- `app/services/parse_service.py`
  - `@dataclass(slots=True) class DocumentPage`：文档页
    - `page_no: int`、`text: str`
  - `@dataclass(slots=True) class DocumentText`：文档文本
    - `file_path: str`、`pages: list[DocumentPage]`
  - `def extract_document_text(file_path)`：按扩展名分发 pdfplumber/python-docx，返回 DocumentText
  - `def parse_pdf(file_path)`：PDF 文本提取（按页）
  - `def parse_docx(file_path)`：Word 文本提取（段落 + 表格）
  - `def save_parse_result(task_id, parse_result)`：写 contract_parses，更新 parse_status
  - `def mark_parse_failed(task_id, parse_error)`：记录 parse_error 并置 parse_status=failed
  - `def get_parse_by_task(task_id)`：查询解析结果
验证：单元测试 `test_parse_service.py`（pdf/docx 各提取文本并带页码）

### Step 23：LLM 字段抽取

文件：创建 `app/agents/__init__.py`、`app/agents/parse_agent.py`
目的：用 LLM 将合同文本抽取为结构化字段，保留原文片段与定位。
文件详情：
- `app/agents/parse_agent.py`
  - `@dataclass(slots=True) class ParseField`：单个解析字段
    - `field_name: str`、`field_value: str`、`raw_text: str`、`page_no: int`、`extract_status: str`
  - `@dataclass(slots=True) class ContractParseResult`：解析结果
    - `basic_info: dict`、`clauses: dict`、`fields: list[ParseField]`、`parse_status: str`、`parse_error: str | None`
  - `def extract_contract_fields(document_text, llm)`：抽取并返回 ContractParseResult
  - `def build_parse_messages(document_text)`：构造抽取提示词（字段清单与输出格式要求）
  - `def validate_parse_result(result)`：校验必填字段与缺失状态，缺失时置 extract_status
验证：配置真实 key 后对样例合同抽取并打印 JSON；无 key 时明确失败

## 阶段 6：规则引擎

### Step 24：代码规则匹配

文件：创建 `app/services/rule_service.py`
目的：实现规则加载与代码规则（regex/numeric）确定性匹配。
文件详情：
- `app/services/rule_service.py`
  - `@dataclass(slots=True) class HitMatch`：一次规则命中
    - `rule_id: int`、`rule_code: str`、`rule_name: str`、`risk_level: str`、`evidence_text: str`、`evidence_position: str`
  - `def load_enabled_rules()`：加载 enabled 规则，返回 list[ReviewRule]
  - `def match_regex(rule, document_text)`：正则匹配，命中返回 HitMatch
  - `def match_numeric(rule, basic_info)`：数值阈值匹配（预付款比例、付款周期），命中返回 HitMatch
  - `def match_code_rules(parse, rules)`：遍历 regex/numeric 规则生成候选命中列表
验证：单元测试 `test_rule_engine.py`（各代码规则命中/未命中）

### Step 25：LLM 语义规则与流水线

文件：创建 `app/agents/rule_agent.py`
目的：实现 LLM 语义规则判断与可选证据复核，并组装完整审查流水线。
文件详情：
- `app/agents/rule_agent.py`
  - `@dataclass(slots=True) class SemanticVerdict`：LLM 语义判断结果
    - `rule_id: int`、`hit: bool`、`evidence_text: str`、`evidence_position: str`、`reason: str`
  - `def judge_semantic_rules(context, llm_rules, llm)`：逐条语义判断，返回 list[SemanticVerdict]
  - `def review_code_hits(hits, context, llm)`：对代码规则命中做语义复核，过滤明显误报
  - `def run_review_pipeline(task_id)`：阶段1 代码匹配 → 阶段2 LLM 判断/复核 → 阶段3 汇总，返回 ReviewResult
  - `def aggregate_risk(hits)`：按命中风险等级聚合总风险等级
  - `def build_focus_points(hits)`：生成审批关注点列表
  - `def save_hits(task_id, hits)`：命中落库 rule_hits
  - `def save_review_result(task_id, result)`：结果落库 review_results
验证：对高/中/低风险样例合同各跑一次，检查风险等级与证据

## 阶段 7：回写服务

### Step 26：评论生成与回写

文件：创建 `app/agents/writeback_agent.py`、`app/services/writeback_service.py`
目的：生成回写评论、调用审批适配层回写并记录回写状态。
文件详情：
- `app/agents/writeback_agent.py`
  - `def generate_comment(review_result)`：LLM 生成回写评论（总风险 + 关注点 + 摘要）
- `app/services/writeback_service.py`
  - `def prepare_writeback(task_id)`：生成评论并写入 review_results.comment_text
  - `def writeback(task_id)`：调用适配层回写，更新 write_status 并写 comment_logs
  - `def retry_writeback(task_id)`：回写失败重试
验证：脚本完成回写，检查 mock/comments 中评论内容

## 阶段 8：任务服务与 LangGraph 编排

### Step 27：任务服务

文件：创建 `app/services/task_service.py`
目的：实现任务入库、去重、查询、重试与人工触发入口。
文件详情：
- `app/services/task_service.py`
  - `def ingest_pending_approvals()`：拉取待办并按 approval_code 去重（更新或创建）
  - `def create_task_from_approval(detail)`：创建任务（task_status=pending，write_status=not_written）
  - `def get_task_detail(task_id)`：聚合任务、附件、解析、命中、结果、日志，返回 TaskDetail
  - `def list_tasks(task_status, page, size)`：分页查询任务，返回 PageResult
  - `def retry_task(task_id)`：blocked 任务重试，按失败点回 parsing/reviewing
  - `def trigger_pull()`：人工触发入口，拉取待办并入队
验证：单元测试 `test_task_service.py`（去重、状态流转、重试）

### Step 28：LangGraph 状态

文件：创建 `app/graph/__init__.py`、`app/graph/state.py`
目的：定义 LangGraph 节点间共享的数据包，保证节点输入输出一致。
文件详情：
- `app/graph/state.py`
  - `class ContractReviewState(TypedDict)`：图状态
    - `task_id: int`
    - `instance_id: str`
    - `approval_detail: ApprovalDetail | None`
    - `attachment_path: str | None`
    - `document_text: DocumentText | None`
    - `parse_result: ContractParseResult | None`
    - `hits: list[HitMatch]`
    - `review_result: ReviewResult | None`
    - `comment_text: str | None`
    - `writeback_result: WritebackResult | None`
    - `error: str | None`
    - `stage: str`
验证：`uv run python -c "from app.graph.state import ContractReviewState"`

### Step 29：图节点

文件：创建 `app/graph/nodes.py`
目的：把主流程每一步实现为图节点，节点间只通过 ContractReviewState 交互。
文件详情：
- `app/graph/nodes.py`
  - `def ingest_node(state)`：调用审批工具拉取并入库
  - `def download_node(state)`：下载主附件并更新附件记录
  - `def parse_node(state)`：文本提取 + LLM 字段抽取
  - `def review_node(state)`：执行规则审查流水线
  - `def save_node(state)`：保存审查结果
  - `def writeback_node(state)`：生成评论并回写
  - `def block_node(state)`：记录异常并置 task_status=blocked
验证：直接以样例 state 调用各节点

### Step 30：工作流图

文件：创建 `app/graph/workflow.py`
目的：组装固定顺序图，定义节点与异常流转。
文件详情：
- `app/graph/workflow.py`
  - `def build_graph()`：固定顺序图 ingest→download→parse→review→save→writeback，异常边指向 block
  - `def run_workflow(task_id)`：执行图并返回最终状态
验证：对 mock 审批单跑完整图，观察状态序列

### Step 31：后台队列

文件：创建 `app/workers/__init__.py`、`app/workers/queue.py`
目的：用 asyncio 队列承接人工触发，后台 worker 串行执行工作流。
文件详情：
- `app/workers/queue.py`
  - `def get_task_queue()`：返回 asyncio.Queue 单例
  - `def enqueue_task(task_id)`：任务入队
  - `async def worker_loop()`：后台消费队列并执行 run_workflow
验证：启动 worker 后 trigger 一个任务，轮询状态到 done

## 阶段 9：对外 API 与入口

### Step 32：任务接口

文件：创建 `app/api/tasks.py`
目的：暴露任务列表、详情、重试与人工拉取接口。
文件详情：
- `app/api/tasks.py`
  - `def list_tasks()`：GET /api/tasks（状态筛选 + 分页）
  - `def get_task()`：GET /api/tasks/{task_id}
  - `def retry_task()`：POST /api/tasks/{task_id}/retry（admin）
  - `def trigger_pull()`：POST /api/tasks/trigger（前端按钮）
验证：接口冒烟测试

### Step 33：规则与命中接口

文件：创建 `app/api/rules.py`、`app/api/hits.py`
目的：暴露规则维护与命中查询接口，人工复核接口预留。
文件详情：
- `app/api/rules.py`
  - `def list_rules()`：GET /api/rules（admin/reviewer）
  - `def create_rule()`：POST /api/rules（admin）
  - `def update_rule()`：PUT /api/rules/{rule_id}（admin）
  - `def delete_rule()`：DELETE /api/rules/{rule_id}（admin，逻辑删除）
- `app/api/hits.py`
  - `def list_hits()`：GET /api/hits（按任务/规则/风险筛选）
  - `def confirm_hit()`：POST /api/hits/{hit_id}/confirm（框架预留，demo 返回未启用）
  - `def ignore_hit()`：POST /api/hits/{hit_id}/ignore（框架预留，demo 返回未启用）
验证：接口冒烟测试

### Step 34：日志接口

文件：创建 `app/api/logs.py`
目的：暴露运行日志查询接口。
文件详情：
- `app/api/logs.py`
  - `def list_logs()`：GET /api/logs（admin，按级别/类型/任务筛选）
验证：接口冒烟测试

### Step 35：应用入口

文件：创建 `main.py`（根目录）
目的：组装 FastAPI 应用，注册路由、启动任务与健康检查。
文件详情：
- `main.py`
  - `def create_app()`：组装 FastAPI：CORS、路由注册、异常处理器、统一响应
  - `async def startup()`：init_db、ensure_admin_seed、启动 worker
  - `def health()`：GET /api/health
验证：`uv run uvicorn main:app --reload`，访问 `/docs` 与 `/api/health`

## 阶段 10：测试与演示

### Step 36：自动化测试

文件：创建 `tests/conftest.py`、`tests/test_state_machine.py`、`tests/test_task_service.py`、`tests/test_rule_engine.py`、`tests/test_adapters.py`、`tests/test_auth.py`、`tests/test_api_smoke.py`
目的：覆盖核心逻辑与接口契约，防止回归。
文件详情：
- `tests/conftest.py`
  - `def setup_test_db()`：测试数据库初始化（SQLite 内存）
  - `def client()`：测试用 FastAPI TestClient 夹具
- `tests/test_state_machine.py`
  - `def test_valid_transitions()`：合法流转
  - `def test_invalid_transitions()`：非法流转被拒绝
- `tests/test_task_service.py`
  - `def test_deduplicate_by_approval_code()`：重复拉取不新建任务
  - `def test_retry_blocked_task()`：blocked 重试回到正确阶段
- `tests/test_rule_engine.py`
  - `def test_regex_rule_hit()` / `def test_numeric_rule_hit()`：代码规则命中
  - `def test_no_false_positive()`：未命中不产生记录
- `tests/test_adapters.py`
  - `def test_mock_list_pending()` / `test_mock_download()` / `test_mock_write_comment()`：MockClient 四方法
- `tests/test_auth.py`
  - `def test_register_and_login()`：注册后登录成功
  - `def test_duplicate_register()`：重复注册失败
- `tests/test_api_smoke.py`
  - `def test_health()` / `def test_trigger_pull_flow()`：接口冒烟
验证：`uv run pytest -v` 全绿

### Step 37：演示脚本与 README

文件：创建 `scripts/demo.py`、`README.md`
目的：提供一键演示脚本与完整启动说明。
文件详情：
- `scripts/demo.py`
  - `def run_demo()`：触发拉取 → 轮询任务 → 打印各阶段结果（附件、解析、命中、风险、评论）
- `README.md`
  - 内容：MySQL 启动、`.env` 填写、依赖安装、服务启动、演示步骤
验证：按 README 从头跑通闭环演示

## 收尾核对

- [ ] 数据库 9 张表建表成功，无外键、含审计与逻辑删除字段
- [ ] 注册/登录可用，admin/123456 可登录并管理
- [ ] trigger 拉取后任务按 pending→parsing→reviewing→done 流转
- [ ] 高/中/低风险样例合同得到对应总风险等级与证据
- [ ] 评论写回 mock/comments，回写状态 success
- [ ] 附件缺失等异常进入 blocked，admin 重试可恢复
- [ ] pytest 全绿、OpenAPI 可访问、README 演示闭环跑通
