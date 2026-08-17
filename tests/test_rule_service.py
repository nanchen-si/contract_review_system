"""规则匹配单元测试。"""

from app.models.rule import ReviewRule
from app.services.rule_service import (
    HitMatch,
    aggregate_risk,
    match_code_rules,
    match_missing,
    match_numeric,
    match_regex,
    save_hits,
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


def test_numeric_rule_rule_aware():
    """预付款取百分比、付款周期取天数，避免金额等无关数值误命中。"""
    prepay = _rule("numeric", "50", "RULE_PREPAY_RATIO")
    assert match_numeric(prepay, [60], text="预付款 60%") is not None
    cycle = _rule("numeric", "30", "RULE_PAYMENT_CYCLE")
    assert match_numeric(cycle, [30], text="验收合格后 30 日内付清") is None
    assert match_numeric(cycle, [60], text="验收合格后 60 日内付清") is not None


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


def test_save_hits_idempotent(db_session):
    """重复执行流水线不累积命中。"""
    hit = HitMatch(
        rule_id=1,
        rule_code="R1",
        rule_name="测试规则",
        risk_level="high",
        evidence_text="x",
        evidence_position="p",
    )
    save_hits(1, [hit])
    save_hits(1, [hit])
    from sqlalchemy import func, select

    from app.db import get_session
    from app.models.rule import RuleHit

    with next(get_session()) as db:
        assert db.scalar(select(func.count()).select_from(RuleHit)) == 1
