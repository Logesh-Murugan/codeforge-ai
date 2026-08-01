"""
WebSocket ConnectionManager — Phase 5.7

Manages live WebSocket connections, heartbeats, broadcasting updates.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Set
from fastapi import WebSocket

from monitoring.schemas.websocket import WSFrame, WSFrameType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket Connection Manager.
    """

    def __init__(self) -> None:
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int) -> None:
        """Accept connection and add to active connections pool."""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
        logger.info(f"[WS-Manager] Client connected for project {project_id}")

    def disconnect(self, websocket: WebSocket, project_id: int) -> None:
        """Remove WebSocket from active connections pool."""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        logger.info(f"[WS-Manager] Client disconnected from project {project_id}")

    async def broadcast_to_project(self, project_id: int, frame: WSFrame) -> None:
        """Broadcast frame payload to all clients connected to project_id."""
        connections = self.active_connections.get(project_id, set())
        if not connections:
            return

        payload_str = frame.model_dump_json()
        disconnected = []
        for ws in connections:
            try:
                await ws.send_text(payload_str)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, project_id)


ws_manager = ConnectionManager()
