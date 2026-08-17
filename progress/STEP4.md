# STEP4 · 项目进展（阶段 0-8 汇总）

> 输出日期：2026-08-17
> 分支：`codex/stage-0-1`
> 说明：合同审查审批系统（《项目实战》2.4）阶段 0-8 汇总，承接 STEP3。

## 一、当前状态

阶段 0-8 已完成：脚手架、核心基础设施、认证、审批适配与 Mock、
工具层、解析服务、规则引擎、回写服务、任务服务、LangGraph 编排与后台队列全部可运行。

## 二、已完成内容总览

### 阶段 0-3（详见 STEP1/STEP2）

- uv 项目、MySQL compose、`.env` 配置、9 张表 ORM、认证接口、Mock 数据与适配层。

### 阶段 4（详见 STEP3）

- 7 个工具函数与解析/规则/回写支撑服务，链路"拉取 → 下载 → 解析 → 审查 → 保存 → 回写"打通。

### 阶段 5-6

- `parse_service` / `ocr_service` / `clause_splitter`：文本提取、OCR 置信度、Markdown 章节切分。
- `parse_agent`：`validate_parse_result` 三层判定、LLM 失败自动重试 1 次。
- `rule_service` / `rule_agent`：11 条规则、regex/numeric/missing 匹配、LLM 语义判断与代码命中复核。
- 三个 LLM 代理统一 JSON Schema 结构化输出（不兼容端点回退 json_object）。

### 阶段 7-8

- `writeback_service`：评论生成、回写、状态与日志。
- `task_service`：拉取去重、任务详情聚合、分页、重试上限、人工触发。
- `app/graph/`：`ContractReviewState` + 7 节点固定顺序图，异常路由到 block。
- `app/workers/queue.py`：`asyncio.Queue` 单例、入队、串行 worker。

## 三、验证结果

- `uv run pytest tests -q`：38 passed。
- `uv lock --check`：87 包一致。
- 全模块导入与配置检查通过。
- 真实 MySQL 完整工作流：`run_workflow(1)` → `stage=done`、`task_status=done`、`write_status=success`。
- 工作流幂等重跑：附件保持 2 条，命中被整体替换不累积，任务保持 done。

## 四、本次 Debug 结论

- 未发现新的代码缺陷。
- 两项已知行为（非缺陷）：
  1. LLM 命中数在 3-4 之间波动：当前模型仅支持默认 temperature=1，
     语义判断/复核结果存在非确定性；已确认不是数据累积问题。
  2. `comment_logs` 每次回写追加一条：按日志表设计保留回写历史。

## 五、遗留问题 / 待办

- `structured`（条款结构化要点）尚未由解析代理产出，规则数值匹配仍为启发式。
- 扫描件 PNG / 无文本层 PDF 的 OCR 链路未在真实样例验证（demo 主附件为 docx）。
- `retry_task` 当前统一回到 `parsing`，未按失败点区分 parsing/reviewing。
- 阶段 9 未实现：对外 API（任务/规则/命中/日志）、`main.py` 入口、
  worker 启动、OpenAPI 与演示脚本。

## 六、下一步

执行阶段 9：`app/api/tasks.py` / `rules.py` / `hits.py` / `logs.py`、
`main.py`（`create_app` + 启动 worker）、健康检查，并补接口冒烟测试，
最终通过 README/演示脚本跑通完整闭环。
