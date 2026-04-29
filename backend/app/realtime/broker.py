from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from typing import Any


class NarrationBroker:
    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, scan_id: uuid.UUID) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers[scan_id].add(queue)
        return queue

    async def unsubscribe(self, scan_id: uuid.UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            queues = self._subscribers.get(scan_id)
            if not queues:
                return
            queues.discard(queue)
            if not queues:
                self._subscribers.pop(scan_id, None)

    async def publish(self, scan_id: uuid.UUID, event: dict[str, Any]) -> int:
        async with self._lock:
            queues = list(self._subscribers.get(scan_id, ()))
        delivered = 0
        for queue in queues:
            try:
                queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                pass
        return delivered


narration_broker = NarrationBroker()
