from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db import get_sessionmaker
from app.models.narration import NarrationEvent
from app.models.scan import Scan
from app.realtime import narration_broker

router = APIRouter(tags=["ws"])


def _sse_frame(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n".encode("utf-8")


async def _scan_exists(session: AsyncSession, scan_id: uuid.UUID) -> bool:
    result = await session.execute(select(Scan.id).where(Scan.id == scan_id))
    return result.scalar_one_or_none() is not None


async def _replay_history(
    session: AsyncSession, scan_id: uuid.UUID, limit: int = 200
) -> list[dict]:
    result = await session.execute(
        select(NarrationEvent)
        .where(NarrationEvent.scan_id == scan_id)
        .order_by(NarrationEvent.created_at.asc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    return [
        {
            "id": str(r.id),
            "scan_id": str(r.scan_id),
            "phase": str(r.phase),
            "success_signal": r.success_signal,
            "target_observations": r.target_observations,
            "decision": r.decision,
            "next_action": r.next_action,
            "content": r.content,
            "context": r.context,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.websocket("/ws/scans/{scan_id}")
async def scan_narration(websocket: WebSocket, scan_id: uuid.UUID) -> None:
    await websocket.accept()
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        if not await _scan_exists(session, scan_id):
            await websocket.send_json({"type": "error", "error": "scan not found"})
            await websocket.close(code=4404)
            return
        history = await _replay_history(session, scan_id)

    queue = await narration_broker.subscribe(scan_id)
    try:
        for event in history:
            await websocket.send_json({"type": "narration", "event": event})
        await websocket.send_json({"type": "ready"})

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_json({"type": "narration", "event": event})
            except TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        await narration_broker.unsubscribe(scan_id, queue)


@router.get("/sse/scans/{scan_id}")
async def scan_narration_sse(request: Request, scan_id: uuid.UUID) -> StreamingResponse:
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        if not await _scan_exists(session, scan_id):
            async def not_found() -> asyncio.AsyncIterator[bytes]:
                yield _sse_frame({"type": "error", "error": "scan not found"})

            return StreamingResponse(not_found(), media_type="text/event-stream")
        history = await _replay_history(session, scan_id)

    queue = await narration_broker.subscribe(scan_id)

    async def event_stream():
        try:
            for event in history:
                yield _sse_frame({"type": "narration", "event": event})
            yield _sse_frame({"type": "ready"})

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield _sse_frame({"type": "narration", "event": event})
                except TimeoutError:
                    yield _sse_frame({"type": "ping"})
        finally:
            await narration_broker.unsubscribe(scan_id, queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
