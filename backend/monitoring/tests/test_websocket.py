"""
WebSocket Tests — Phase 5.7
"""
import pytest
from monitoring.websocket.connection_manager import ConnectionManager
from monitoring.schemas.websocket import WSFrame, WSFrameType


@pytest.mark.asyncio
async def test_connection_manager_init():
    manager = ConnectionManager()
    assert len(manager.active_connections) == 0
