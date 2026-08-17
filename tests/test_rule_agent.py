"""规则代理回退逻辑测试。"""

from app.agents.rule_agent import review_code_hits
from app.config import Settings
from app.services.rule_service import HitMatch


def _hit() -> HitMatch:
    return HitMatch(
        rule_id=1,
        rule_code="R1",
        rule_name="测试规则",
        risk_level="high",
        evidence_text="证据",
        evidence_position="位置",
    )


def test_review_code_hits_empty():
    """无命中直接返回空。"""
    assert review_code_hits([], {}) == []


def test_review_code_hits_fallback(monkeypatch):
    """LLM 未配置时保留全部代码命中。"""
    from app.agents import rule_agent

    monkeypatch.setattr(rule_agent, "get_settings", lambda: Settings(llm_api_key="", llm_base_url=""))
    hits = [_hit()]
    assert review_code_hits(hits, {}) == hits
