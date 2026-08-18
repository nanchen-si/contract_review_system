# contract_review_system 项目上下文

> 本文件在每次会话开始时作为项目上下文加载。所有设计、文档、代码、JSON 示例、图表都必须遵守以下规则。

## 项目定位

- 合同审查审批系统（《项目实战》2.4）：Python 3.12 + FastAPI + LangGraph + MySQL 8。
- 权威文档：`.spec.md`（37 步实施步骤，含统一属性命名约定）；流程图：根目录 `审批解析流程图.html`。
- `.spec.md` 与 `审批解析流程图.html` 必须保持字段名、流程、命名完全一致，一处改了必须同步另一处。

## 铁律：字段与属性名必须完全对齐

1. 唯一真源：`.spec.md` 的「统一属性命名约定」、`app/models` 的 ORM 模型、`app/schemas` 的 Pydantic Schema。任何文档、图表、JSON 示例、代码都不得定义同义新名。
2. 禁止发明别名：同一语义只能用真源中的名字。例如原文片段一律 `raw_text`，禁止 `clause_text`、`text` 等替代。
3. 层级归属固定：字段属于哪一层只能在那一层出现。例如 `evidence_position` 只属于命中结果（rule_hits）层，由 `page_no + clause_name` 拼出；解析层（contract_parses）只保存 `page_no`。
4. 完整性：规定"每个字段都带 X"时，所有条目都必须带 X，不能只在特殊条目出现。例如每个解析字段/条款都带 `raw_text`、`page_no`、`extract_status`。
5. 反向核对：写完文档、图表、JSON 示例后，逐个字段对照真源检查；发现不一致先修再交付，不得以"意思一样"为由放行。
6. 术语新增：确需新增字段（如 `structured`）时，先写入 spec 定义，再在示例中按同一名字使用，禁止先示例后定义。

## 教训记录（2026-08-17）

- 失误：在 `clause_info_json` 示例中发明了 `clause_text`；把 `evidence_position` 放进了解析层；只给 missing 条目带 `extract_status`。
- 根因：凭"意思差不多"造名，没有先对照 `.spec.md` 统一命名与模型定义。
- 通用教训：跨层引用和 JSON 示例最容易出现名字漂移；任何时候先查真源表再写字段，写完反向核对；分层字段不得串层。
