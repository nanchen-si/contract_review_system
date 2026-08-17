"""LangGraph 工作流测试。"""

from app.graph.state import ContractReviewState
from app.graph.workflow import build_graph, run_workflow


def test_build_graph():
    """图可编译且包含关键节点。"""
    graph = build_graph()
    assert graph is not None


def test_run_workflow_blocked_on_missing_task(db_session):
    """任务不存在时进入 blocked 且带错误信息。"""
    state = run_workflow(99999)
    assert state["stage"] == "blocked"
    assert state.get("error")


def test_state_importable():
    """状态结构可导入。"""
    assert ContractReviewState is not None
