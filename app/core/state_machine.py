"""任务/回写/命中状态常量与合法流转规则。"""

TASK_STATUSES = {"pending", "parsing", "reviewing", "blocked", "done"}
WRITE_STATUSES = {"not_written", "writing", "success", "failed"}
HIT_STATUSES = {"pending", "confirmed", "ignored"}

_TRANSITIONS = {
    "pending": {"parsing"},
    "parsing": {"reviewing", "blocked"},
    "reviewing": {"done", "blocked"},
    "blocked": {"parsing", "reviewing"},
    "done": set(),
}


def can_transition(current: str, target: str) -> bool:
    """判断任务状态流转是否合法。"""
    return target in _TRANSITIONS.get(current, set())


def retry_stage_for(failure_stage: str) -> str:
    """blocked 任务按失败点回到 parsing 或 reviewing。"""
    return "parsing" if failure_stage == "parsing" else "reviewing"
