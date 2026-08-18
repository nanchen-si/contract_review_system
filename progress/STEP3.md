# STEP3 · 项目进展（阶段 4 工具层）

> 输出日期：2026-08-17
> 分支：`codex/stage-0-1`
> 说明：合同审查审批系统（《项目实战》2.4）第三阶段实施进展，承接 STEP2。

## 一、当前目标

完成阶段 4：7 个工具函数（2.4.10）落地到 `app/tools/`，
并打通"拉取 → 下载 → 解析 → 审查 → 保存 → 回写"的可调用链路。

## 二、已完成内容

### 工具层

- `app/tools/approval_tools.py`：拉取待办并去重入库、审批详情、下载附件。
- `app/tools/document_tools.py`：`parse_contract_document` 完整解析链路。
- `app/tools/review_tools.py`：`run_contract_rules` 规则审查流水线。
- `app/tools/result_tools.py`：保存审查结果、评论回写。

### 支撑服务（按 HTML 流程图前置实现）

- `app/services/parse_service.py`：docx/pdf/图片提取、PDF 逐页 OCR 兜底、多附件合并、解析结果落库。
- `app/services/ocr_service.py`：rapidocr 识别 + `OCR_CONFIDENCE_THRESHOLD` 过滤。
- `app/services/clause_splitter.py`：清洗、标题识别（三级信号）、转 Markdown、章节切分、过滤、分块。
- `app/services/rule_service.py`：11 条规则种子、regex/numeric/missing 匹配、命中落库、风险聚合。
- `app/services/writeback_service.py`：评论准备、回写、状态记录。
- `app/agents/`：`parse_agent` / `rule_agent` / `writeback_agent`，统一 OpenAI 兼容接口 + JSON 结构化输出。

## 三、验证结果

- `uv run pytest tests -q`：26 passed。
- Step 18：拉取待办去重入库、详情、下载附件 ✓
- Step 19：docx 解析 + LLM 抽取，16 个字段全部产出 ✓
- Step 20：规则审查，命中 3 条，总风险 high ✓
- Step 21：评论生成（LLM）并回写，write_status=success ✓
- 附件重复下载不累积、命中重复执行不累积 ✓

## 四、本次 Debug 记录

### 阶段 4 实现期修复（第 1 批）

1. commit 后 ORM 对象脱离 Session → `expire_on_commit=False`。
2. 章节正则漏"条"字符 → `[章节条]`。
3. 标题块无正文被丢弃 → 标题块强制保留。
4. `LLM_BASE_URL` 缺 `/v1` → 配置自动补全。
5. 模型不支持 `temperature=0` → 移除该参数。
6. `json_object` 输出结构不匹配 → 要求 `{"fields": [...]}` + 容错解析。
7. 保密/验收"缺失"规则逻辑反了 → 改为未命中关键词才算命中。
8. 规则种子只插不更新 → 改为幂等 upsert。
9. 中文乱码修复。

### 阶段 4 复验期修复（第 2 批，本次 Debug 结论）

1. `rule_hits` 重复执行累积（4→8）→ `save_hits` 先清旧命中再写入。
2. 附件重复下载产生重复记录 → 按 `task_id + attachment_id` 先删后插。
3. 评论 LLM 静默失败：`response_format=json_object` 要求消息中出现 "json"，
   评论提示词缺少该字样 → 提示词补充 JSON 结构并解析 `comment_text`，失败时记日志并模板兜底。
4. `write_approval_comment` 的 `instance_id` 参数未透传 → 回写按传入实例 ID 落盘。
5. 数值规则误报：付款周期被金额/百分比误触发 → 预付款规则只取 `%` 值、
   付款周期规则只取"日/天"值。

## 五、遗留问题 / 待办

- `structured`（条款结构化要点，如预付款比例、管辖地）尚未由解析代理产出，
  规则引擎目前从原文数值启发式取值，后续按 `clause_info_json` 结构补全。
- 扫描件 PNG / 无文本层 PDF 的 OCR 链路未在真实样例上验证（demo 主附件为 docx）。
- 任务服务（去重/重试/详情聚合）与 LangGraph 编排、后台队列、对外 API、`main.py` 尚未实现。

## 六、下一步

- 阶段 5-7 收尾：条款 `structured` 输出、规则/回写与任务状态联动。
- 阶段 8：任务服务 `task_service` 与 LangGraph 图编排。
- 阶段 9：对外 API（任务/规则/命中/日志）与 `main.py` 入口，串成完整闭环演示。
