"""状态机单元测试。"""

from app.core.state_machine import can_transition, retry_stage_for


def test_valid_transitions():
    """合法流转。"""
    assert can_transition("pending", "parsing")
    assert can_transition("parsing", "reviewing")
    assert can_transition("parsing", "blocked")
    assert can_transition("blocked", "parsing")
    assert can_transition("blocked", "reviewing")


def test_invalid_transitions():
    """非法流转被拒绝。"""
    assert not can_transition("done", "parsing")
    assert not can_transition("pending", "reviewing")


def test_retry_stage_for():
    """blocked 重试回到正确阶段。"""
    assert retry_stage_for("parsing") == "parsing"
    assert retry_stage_for("reviewing") == "reviewing"
