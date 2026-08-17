# STEP5 · 项目进展（全项目调试与阶段 9-10 收尾）

> 输出日期：2026-08-17
> 分支：`codex/stage-0-1`
> 说明：合同审查审批系统（《项目实战》2.4）阶段 0-10 全量调试汇总，承接 STEP4。

## 一、当前状态

spec 阶段 0-10 全部落地：脚手架、认证、审批适配、工具层、解析、规则引擎、
回写、任务服务、LangGraph 编排、后台队列、对外 API、应用入口、测试与演示脚本。

## 二、阶段 9-10 完成内容

### 阶段 9：对外 API 与入口

- `app/api/tasks.py`：trigger / 列表 / 详情 / retry（admin）。
- `app/api/rules.py`：规则 CRUD，删除为逻辑删除（新增 `is_deleted`，真实库已 ALTER）。
- `app/api/hits.py`：命中查询（任务/规则/风险筛选），confirm/ignore 框架预留。
- `app/api/logs.py`：日志分页查询（admin）。
- `main.py`：`create_app`（CORS、统一异常响应、lifespan 启动 init_db/种子/worker）、
  `/api/health`、OpenAPI。

### 阶段 10：测试与演示

- `tests/test_api_smoke.py`：健康、任务列表、trigger 拉取流、admin 重试、规则 CRUD。
- `scripts/demo.py`：一键拉取 → 工作流 → 打印各阶段结果。
- `README.md`：启动、配置、演示与测试说明。

## 三、全项目调试结论

### 发现并修复

1. **评论未落库（重要）**：`prepare_writeback` 在第一个 Session 加载结果、关闭后
   再开新 Session 修改脱离实例，`review_results.comment_text` 始终为 NULL。
   修复：同一 Session 内加载、赋值、提交；新增 `test_writeback.py` 回归。
2. 队列单例跨测试污染：worker 测试消费到其他测试残留任务。
   修复：队列测试前重置模块级单例。
3. `demo.py` 缺少项目根路径：直接运行报 `No module named 'app'`。
   修复：脚本顶部插入项目根目录。
4. 任务详情命中缺 `risk_level`：规则映射补全，演示打印不再崩溃。
5. 阶段 4 遗留修复（承接）：命中/附件重复累积、LLM 提示词缺 "json"、
   instance_id 透传、数值规则误报、JSON Schema 结构化输出。

### 复验通过

- `uv run pytest tests -q`：44 passed。
- 真实服务冒烟：`/api/health`、`/docs`、登录、任务、规则、命中、日志、预留接口全部 200，
  对 done 任务重试正确返回 400。
- 真实 MySQL：9 张表齐全；`comment_text` 已落库（250 字符）；工作流 done/success。
- 全模块 38 个导入正常；`uv lock --check` 一致；无乱码。

## 四、已知行为（非缺陷）

- LLM 命中数在 3-4 间波动：模型仅支持默认 temperature=1，语义判断非确定性。
- `comment_logs` 按回写次数追加，保留回写历史。
- `retry_task` 统一回到 `parsing`，未按失败点区分 parsing/reviewing。

## 五、遗留优化点

- `structured` 条款结构化要点尚未由解析代理产出，规则数值匹配为启发式。
- 扫描件 PNG / 无文本层 PDF 的 OCR 链路未在真实样例验证（demo 主附件为 docx）。
- 前端调用端（2.4.7）仍由 OpenAPI 契约承接，前端暂缓。

## 六、下一步建议

- 生产化：真实审批适配 `RealClient`、Redis 缓存/队列、多 worker、部署配置。
- 业务增强：条款 `structured` 抽取、人工命中确认落地、规则引擎数值口径细化。
- 文档收尾：按提交历史整理 CHANGELOG，或开始前端对接。
