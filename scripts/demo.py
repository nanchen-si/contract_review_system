"""一键演示：拉取待办 → 执行工作流 → 打印各阶段结果。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.workflow import run_workflow
from app.services.task_service import get_task_detail, ingest_pending_approvals


def run_demo():
    """触发拉取、执行工作流并打印结果。"""
    tasks = ingest_pending_approvals()
    for task in tasks:
        print(f"任务：{task.approval_code} {task.approval_title}")
        state = run_workflow(task.id)
        detail = get_task_detail(task.id)
        print(f"工作流阶段：{state.get('stage')}，任务状态：{detail.task_status}，回写状态：{detail.write_status}")
        for attachment in detail.attachments:
            print(f"附件：{attachment['file_name']}（{attachment['download_status']}）")
        if detail.parse:
            print("解析状态：", detail.parse["parse_status"])
        if detail.result:
            print("总风险：", detail.result["overall_risk_level"])
            print("摘要：", detail.result["summary_text"])
            print("评论：", (detail.result["comment_text"] or "")[:80])
        for hit in detail.hits:
            print(f"命中：{hit['rule_name']} [{hit['risk_level']}] {hit['evidence_text'][:60]}")


if __name__ == "__main__":
    run_demo()
