# STEP2 · 项目进展（阶段 2/3）

> 输出日期：2026-08-17
> 分支：`codex/stage-0-1`
> 说明：合同审查审批系统（《项目实战》2.4）第二阶段实施进展，承接 STEP1。

## 一、当前目标

完成阶段 2（认证与权限）和阶段 3（审批适配层与 Mock 数据），
为后续工具层、解析、规则引擎与回写提供可调用的认证接口和审批系统适配入口。

## 二、已完成内容

### 阶段 2：认证与权限

- `app/services/auth_service.py`：注册（唯一性校验、bcrypt 哈希、reviewer 角色）、
  登录（签发 JWT、缓存登录态）、按用户名/ID 查询用户（缓存优先）。
- `app/core/deps.py`：`get_current_user`（token 解析、缓存优先、401）、
  `require_admin`（非 admin 返回 403）。
- `app/api/auth.py`：`POST /api/auth/register`、`POST /api/auth/login`、
  `GET /api/auth/me`，统一 `ApiResponse` 包装。
- `tests/conftest.py`：SQLite 内存库测试夹具（StaticPool，线程安全）。
- `tests/test_auth.py`：注册/登录/重复注册/密码错误/带 token 访问 `/me`。

### 阶段 3：审批适配层与 Mock 数据

- `mock/approvals.json`：1 个审批单，附件含 docx 合同与 png 扫描件。
- `mock/rules.json`：11 条默认审查规则（2.4.6 清单）。
- `scripts/gen_mock_contracts.py`：生成高/中/低风险 docx 与扫描件 png。
- `app/adapters/base.py`：`AttachmentInfo` / `ApprovalRecord` / `ApprovalDetail` /
  `DownloadResult` / `WritebackResult` 数据类与 `ApprovalAdapter` 抽象接口。
- `app/adapters/mock_client.py`：`MockClient` 四方法实现。
- `app/adapters/factory.py`：按 `APPROVAL_ADAPTER` 返回适配器。
- `tests/test_adapters.py`：四方法 + 工厂测试。

## 三、运行与验证结果

- `uv run pytest tests -q`：14 passed。
- 真实 MySQL 认证链路：注册临时用户 → 登录 → 清理，读写正常。
- 真实 mock 数据冒烟：`list_pending` 返回 1 条审批，
  附件为 `采购合同2026.docx` 与 `采购合同2026-扫描件.png`。
- `uv lock --check`：87 包一致。
- LLM 配置：`LLM_API_KEY` / `LLM_BASE_URL`（http） / `LLM_MODEL` 均已就绪。

## 四、本次 Debug 记录

### 阶段 2/3 中发现并修复

1. SQLite 内存库跨线程丢表：`TestClient` 在子线程访问不到主线程建的表。
   根因：`sqlite://` 每个连接独立内存库 → 修复：测试夹具改用 `StaticPool` 共享连接。
2. SQLite 对 `BIGINT PRIMARY KEY` 不自增，插入报 `NOT NULL constraint failed: users.id`。
   根因：SQLite 仅对 `INTEGER PRIMARY KEY` 自增 → 修复：主键 `id` 统一改 `Integer`
   （关联字段仍为 `BigInteger`，spec 只要求 `id` 主键）。
3. `tests` 目录被 `.gitignore` 残留的 `tests` 行忽略，测试文件无法入库 →
   已清理 `.gitignore` 并补交测试文件。

### 遗留设计衔接点（阶段 4 处理）

- `ApprovalRecord`（2.4.3）没有 `instance_id` 字段，而审批详情工具
  `get_contract_approval(instance_id)` 需要它。阶段 4 实现拉取/详情工具时，
  需在适配层补充 `approval_code → instance_id` 的映射（建议 `MockClient` 提供
  `get_detail_by_code`，或让 `list_pending` 结果附带 `instance_id`）。

## 五、遗留问题 / 待办

- 阶段 4：工具层（7 个工具函数，LangGraph 节点调用）。
- 阶段 5：解析服务（PDF/Word/OCR、Markdown 章节提取、LLM 字段抽取）。
- 阶段 6：规则引擎（代码匹配 + LLM 语义判断）。
- 阶段 7：回写服务。
- 阶段 8-9：LangGraph 编排、任务服务、对外 API 与入口。

## 六、下一步

进入阶段 4：审批类/解析类/规则类/结果类工具，先把 7 个工具函数
（2.4.10）落到 `app/tools/`，并打通"拉取 → 下载 → 解析 → 审查 → 保存 → 回写"
的可调用链路。
