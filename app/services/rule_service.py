"""规则加载、代码规则匹配与审查流水线。"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

from app.config import get_settings
from app.db import get_session
from app.models.result import ReviewResult
from app.models.rule import ReviewRule, RuleHit
from app.services.log_service import write_task_log
from app.services.parse_service import get_parse_by_task

RISK_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass(slots=True)
class HitMatch:
    """一次规则命中。"""

    rule_id: int
    rule_code: str
    rule_name: str
    risk_level: str
    evidence_text: str
    evidence_position: str
    suggestion_text: str = ""


def seed_default_rules():
    """幂等写入 mock/rules.json 中的 11 条默认规则。"""
    settings = get_settings()
    rules_file = Path(settings.mock_data_dir) / "rules.json"
    payload = json.loads(rules_file.read_text(encoding="utf-8"))["rules"]
    with next(get_session()) as db:
        for item in payload:
            exists = db.scalar(select(ReviewRule).where(ReviewRule.rule_code == item["rule_code"]))
            if exists is None:
                db.add(ReviewRule(**{key: item.get(key) for key in (
                    "rule_code",
                    "rule_name",
                    "risk_level",
                    "rule_status",
                    "match_mode",
                    "match_text",
                    "suggestion_text",
                )}))
                continue
            for key in ("rule_name", "risk_level", "rule_status", "match_mode", "match_text", "suggestion_text"):
                setattr(exists, key, item.get(key))
        db.commit()


def load_enabled_rules() -> list[ReviewRule]:
    """加载 enabled 规则。"""
    with next(get_session()) as db:
        return list(db.scalars(select(ReviewRule).where(ReviewRule.rule_status == "enabled")))


def _parse_values(parse_data: dict) -> list[float]:
    """从 basic_info 与 clauses 提取数值（金额、比例、天数）。"""
    values: list[float] = []
    texts = []
    for value in parse_data.get("basic_info", {}).values():
        texts.append(str(value))
    for clause in parse_data.get("clauses", {}).values():
        if isinstance(clause, dict):
            texts.append(str(clause.get("raw_text", "")))
            texts.extend(str(v) for v in clause.get("structured", {}).values())
        else:
            texts.append(str(clause))
    for text in texts:
        values.extend(float(num.replace(",", "")) for num in re.findall(r"\d+(?:\.\d+)?", text))
    return values


def match_regex(rule: ReviewRule, text: str) -> HitMatch | None:
    """正则匹配，命中返回 HitMatch。"""
    if not rule.match_text:
        return None
    match = re.search(rule.match_text, text, re.IGNORECASE)
    if match is None:
        return None
    evidence = match.group(0)
    return HitMatch(
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        risk_level=rule.risk_level,
        evidence_text=evidence,
        evidence_position="原文匹配",
        suggestion_text=rule.suggestion_text or "",
    )


def match_numeric(rule: ReviewRule, values: list[float]) -> HitMatch | None:
    """数值阈值匹配，超过阈值即命中。"""
    try:
        threshold = float(rule.match_text)
    except (TypeError, ValueError):
        return None
    hit_value = next((value for value in values if value > threshold), None)
    if hit_value is None:
        return None
    return HitMatch(
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        risk_level=rule.risk_level,
        evidence_text=f"数值 {hit_value} 超过阈值 {threshold}",
        evidence_position="结构化要点",
        suggestion_text=rule.suggestion_text or "",
    )


def match_missing(rule: ReviewRule, parse_data: dict) -> HitMatch | None:
    """主体信息/金额缺失检查。"""
    basic_info = parse_data.get("basic_info", {})
    missing_keys = {"RULE_PARTY_MISSING": "签约主体", "RULE_AMOUNT_MISSING": "金额"}
    key = missing_keys.get(rule.rule_code)
    if key is not None:
        if str(basic_info.get(key, "")).strip():
            return None
    else:
        # 文本型缺失规则：关键词未出现在全文才算命中
        text = _combined_text(parse_data)
        keywords = [item.strip() for item in (rule.match_text or "").split("|") if item.strip()]
        if any(keyword in text for keyword in keywords):
            return None
    return HitMatch(
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        risk_level=rule.risk_level,
        evidence_text=f"{key}缺失",
        evidence_position="基本信息",
        suggestion_text=rule.suggestion_text or "",
    )


def _combined_text(parse_data: dict) -> str:
    parts = [str(value) for value in parse_data.get("basic_info", {}).values()]
    for clause in parse_data.get("clauses", {}).values():
        if isinstance(clause, dict):
            parts.append(str(clause.get("raw_text", "")))
        else:
            parts.append(str(clause))
    return "\n".join(parts)


def match_code_rules(parse_data: dict, rules: list[ReviewRule]) -> list[HitMatch]:
    """遍历 regex/numeric/missing 规则生成候选命中。"""
    text = _combined_text(parse_data)
    values = _parse_values(parse_data)
    hits: list[HitMatch] = []
    for rule in rules:
        if rule.match_mode == "regex":
            hit = match_regex(rule, text)
        elif rule.match_mode == "numeric":
            hit = match_numeric(rule, values)
        elif rule.match_mode == "missing":
            hit = match_missing(rule, parse_data)
        else:
            continue
        if hit is not None:
            hits.append(hit)
    return hits


def save_hits(task_id: int, hits: list[HitMatch]):
    """命中落库 rule_hits。"""
    with next(get_session()) as db:
        for hit in hits:
            db.add(
                RuleHit(
                    task_id=task_id,
                    rule_id=hit.rule_id,
                    evidence_text=hit.evidence_text,
                    evidence_position=hit.evidence_position,
                    hit_status="pending",
                )
            )
        db.commit()


def aggregate_risk(hits: list[HitMatch]) -> str:
    """按命中风险等级聚合总风险等级。"""
    if not hits:
        return "low"
    return max((hit.risk_level for hit in hits), key=lambda level: RISK_ORDER.get(level, 0))


def build_focus_points(hits: list[HitMatch]) -> list[str]:
    """生成审批关注点列表。"""
    return [f"{hit.rule_name}（{hit.risk_level}）：{hit.evidence_text[:60]}" for hit in hits]


def save_review_result(
    task_id: int,
    overall_risk_level: str,
    summary_text: str,
    focus_points_json: list,
    comment_text: str | None = None,
) -> ReviewResult:
    """结果落库 review_results。"""
    with next(get_session()) as db:
        result = db.scalar(select(ReviewResult).where(ReviewResult.task_id == task_id))
        if result is None:
            result = ReviewResult(task_id=task_id)
            db.add(result)
        result.overall_risk_level = overall_risk_level
        result.summary_text = summary_text
        result.focus_points_json = focus_points_json
        if comment_text is not None:
            result.comment_text = comment_text
        db.commit()
        db.refresh(result)
    return result


def run_review_pipeline(task_id: int) -> dict:
    """阶段1 代码匹配 → 阶段2 LLM 判断 → 阶段3 汇总。"""
    from app.agents.rule_agent import judge_semantic_rules

    parse = get_parse_by_task(task_id)
    if parse is None or parse.parse_status != "success":
        raise RuntimeError(f"任务 {task_id} 无成功解析结果")
    parse_data = {
        "basic_info": parse.basic_info_json or {},
        "clauses": parse.clause_info_json or {},
    }
    rules = load_enabled_rules()
    code_hits = match_code_rules(parse_data, rules)
    llm_rules = [rule for rule in rules if rule.match_mode == "llm"]
    semantic_hits = judge_semantic_rules(parse_data, llm_rules)
    all_hits = code_hits + semantic_hits
    save_hits(task_id, all_hits)
    risk_level = aggregate_risk(all_hits)
    focus_points = build_focus_points(all_hits)
    summary = f"共命中 {len(all_hits)} 条规则，总风险等级为 {risk_level}。"
    save_review_result(task_id, risk_level, summary, focus_points)
    write_task_log(task_id, "info", "rule", f"规则审查完成，命中 {len(all_hits)} 条")
    return {
        "task_id": task_id,
        "overall_risk_level": risk_level,
        "summary_text": summary,
        "focus_points": focus_points,
        "hits": [
            {
                "rule_name": hit.rule_name,
                "risk_level": hit.risk_level,
                "evidence_text": hit.evidence_text,
                "evidence_position": hit.evidence_position,
            }
            for hit in all_hits
        ],
    }
