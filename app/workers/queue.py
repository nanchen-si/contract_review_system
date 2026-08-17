"""asyncio 任务队列与后台 worker。"""

import asyncio

from app.graph.workflow import run_workflow
from app.services.log_service import write_task_log

_queue: asyncio.Queue | None = None


def get_task_queue() -> asyncio.Queue:
    """返回 asyncio.Queue 单例。"""
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


def enqueue_task(task_id: int):
    """任务入队。"""
    get_task_queue().put_nowait(task_id)


async def worker_loop():
    """后台消费队列并执行 run_workflow。"""
    queue = get_task_queue()
    while True:
        task_id = await queue.get()
        try:
            await asyncio.to_thread(run_workflow, task_id)
        except Exception as exc:
            write_task_log(task_id, "error", "task", f"工作流执行失败：{exc}")
        finally:
            queue.task_done()
