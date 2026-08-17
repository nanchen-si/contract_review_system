"""规则匹配单元测试。"""

from app.models.rule import ReviewRule
from app.services.rule_service import (
    aggregate_risk,
    match_code_rules,
    match_missing,
    match_numeric,
    match_regex,
)


def _rule(match_mode: str, match_text: str, rule_code: str = "R1") -> ReviewRule:
    return ReviewRule(
        id=1,
        rule_code=rule_code,
        rule_name="测试规则",
        risk_level="high",
        rule_status="enabled",
        match_mode=match_mode,
        match_text=match_text,
    )


def test_regex_rule_hit():
    """正则命中。"""
    hit = match_regex(_rule("regex", "自动续约"), "本合同到期自动续约")
    assert hit is not None
    assert hit.evidence_text == "自动续约"


def test_numeric_rule_hit():
    """数值阈值命中。"""
    hit = match_numeric(_rule("numeric", "50"), [60, 30])
    assert hit is not None
    assert "60" in hit.evidence_text


def test_missing_rule_hit():
    """缺失检查命中。"""
    hit = match_missing(_rule("missing", "签约主体", "RULE_PARTY_MISSING"), {"basic_info": {"签约主体": ""}})
    assert hit is not None


def test_match_code_rules_and_aggregate():
    """代码规则流水与风险聚合。"""
    parse_data = {
        "basic_info": {"金额": "1200000", "签约主体": "北京星辰科技有限公司"},
        "clauses": {"付款条款": {"raw_text": "预付款 80%"}},
    }
    rules = [
        _rule("regex", "自动续约"),
        _rule("numeric", "50", "RULE_PREPAY"),
        _rule("missing", "签约主体", "RULE_PARTY_MISSING"),
    ]
    hits = match_code_rules(parse_data, rules)
    assert len(hits) == 1
    assert aggregate_risk(hits) == "high"
