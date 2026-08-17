"""LangGraph 固定顺序工作流图。"""

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    block_node,
    download_node,
    ingest_node,
    parse_node,
    review_node,
    save_node,
    writeback_node,
)
from app.graph.state import ContractReviewState


def _safe(fn):
    """包装节点：异常写入 state.error，由条件边路由到 block。"""

    def wrapper(state):
        try:
            return fn(state)
        except Exception as exc:
            return {"error": str(exc)}

    return wrapper


def _router(state):
    """按 error 字段决定去下一节点还是 block。"""
    return "block" if state.get("error") else "ok"


def build_graph():
    """固定顺序图 ingest→download→parse→review→save→writeback，异常边指向 block。"""
    graph = StateGraph(ContractReviewState)
    graph.add_node("ingest", _safe(ingest_node))
    graph.add_node("download", _safe(download_node))
    graph.add_node("parse", _safe(parse_node))
    graph.add_node("review", _safe(review_node))
    graph.add_node("save", _safe(save_node))
    graph.add_node("writeback", _safe(writeback_node))
    graph.add_node("block", block_node)
    graph.set_entry_point("ingest")
    for source, target in (
        ("ingest", "download"),
        ("download", "parse"),
        ("parse", "review"),
        ("review", "save"),
        ("save", "writeback"),
    ):
        graph.add_conditional_edges(
            source,
            _router,
            {"ok": target, "block": "block"},
        )
    graph.add_edge("writeback", END)
    graph.add_edge("block", END)
    return graph.compile()


def run_workflow(task_id: int) -> dict:
    """执行图并返回最终状态。"""
    graph = build_graph()
    return graph.invoke({"task_id": task_id, "stage": "pending"})
