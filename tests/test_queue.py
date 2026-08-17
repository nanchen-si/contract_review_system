"""后台队列单元测试。"""

import asyncio

import pytest

from app.workers import queue


def test_queue_singleton():
    """get_task_queue 返回同一实例。"""
    assert queue.get_task_queue() is queue.get_task_queue()


@pytest.mark.asyncio
async def test_worker_processes_task(monkeypatch):
    """worker 消费队列并执行工作流。"""
    seen = []
    monkeypatch.setattr(queue, "run_workflow", lambda task_id: seen.append(task_id))
    worker = asyncio.create_task(queue.worker_loop())
    queue.enqueue_task(42)
    for _ in range(100):
        if seen:
            break
        await asyncio.sleep(0.01)
    worker.cancel()
    with pytest.raises(asyncio.CancelledError):
        await worker
    assert seen == [42]
