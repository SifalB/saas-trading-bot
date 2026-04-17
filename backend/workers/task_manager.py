"""
In-memory registry of running bot tasks.
Maps bot_id -> asyncio.Task so we can start/stop bots per user.
"""

import asyncio
from typing import Callable

_tasks: dict[int, asyncio.Task] = {}
_log_queues: dict[int, asyncio.Queue] = {}


def is_running(bot_id: int) -> bool:
    task = _tasks.get(bot_id)
    return task is not None and not task.done()


def start(bot_id: int, coro_factory: Callable) -> None:
    if is_running(bot_id):
        return
    _log_queues[bot_id] = asyncio.Queue(maxsize=500)
    task = asyncio.create_task(coro_factory())
    _tasks[bot_id] = task


def stop(bot_id: int) -> None:
    task = _tasks.pop(bot_id, None)
    if task and not task.done():
        task.cancel()
    _log_queues.pop(bot_id, None)


def get_log_queue(bot_id: int) -> asyncio.Queue | None:
    return _log_queues.get(bot_id)


async def push_log(bot_id: int, message: str) -> None:
    q = _log_queues.get(bot_id)
    if q:
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            q.get_nowait()  # Drop oldest
            q.put_nowait(message)
