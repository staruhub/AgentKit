"""
WebSocket connection manager for real-time tracing.

This module handles WebSocket connections for streaming
agent trace events to the frontend observation panel.
"""

import json
import asyncio
from typing import Any
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class TraceEvent:
    """A trace event to be sent to clients."""
    event_type: str
    agent: str
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    duration_ms: int = 0
    session_id: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type,
            "agent": self.agent,
            "timestamp": self.timestamp,
            "data": self.data,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "session_id": self.session_id,
        })


class ConnectionManager:
    """
    Manages WebSocket connections for real-time trace streaming.

    Supports multiple clients per session for observation panel.
    """

    def __init__(self):
        # Map session_id -> list of connected WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Map session_id -> list of trace events (for replay)
        self.session_traces: dict[str, list[TraceEvent]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Accept a new WebSocket connection for a session.

        Args:
            websocket: The WebSocket connection
            session_id: The interview session ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
                self.session_traces[session_id] = []

            self.active_connections[session_id].append(websocket)

        # Send existing trace events for this session (replay)
        if session_id in self.session_traces:
            for event in self.session_traces[session_id]:
                try:
                    await websocket.send_text(event.to_json())
                except Exception:
                    pass

    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect
            session_id: The session ID it was connected to
        """
        async with self._lock:
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)

                # Clean up empty session lists
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, event: TraceEvent) -> None:
        """
        Broadcast a trace event to all clients connected to a session.

        Args:
            session_id: The session to broadcast to
            event: The trace event to send
        """
        event.session_id = session_id

        # Store event for replay
        async with self._lock:
            if session_id not in self.session_traces:
                self.session_traces[session_id] = []
            self.session_traces[session_id].append(event)

        # Broadcast to all connected clients
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_text(event.to_json())
                except Exception:
                    disconnected.append(websocket)

            # Clean up disconnected clients
            for ws in disconnected:
                await self.disconnect(ws, session_id)

    async def send_agent_start(
        self,
        session_id: str,
        agent: str,
        timestamp: float,
        message: str = "",
    ) -> None:
        """Send agent start event."""
        event = TraceEvent(
            event_type="agent_start",
            agent=agent,
            timestamp=timestamp,
            data={"message": message},
        )
        await self.broadcast_to_session(session_id, event)

    async def send_agent_thinking(
        self,
        session_id: str,
        agent: str,
        timestamp: float,
        thinking: str,
    ) -> None:
        """Send agent thinking event."""
        event = TraceEvent(
            event_type="agent_thinking",
            agent=agent,
            timestamp=timestamp,
            data={"thinking": thinking},
        )
        await self.broadcast_to_session(session_id, event)

    async def send_tool_call(
        self,
        session_id: str,
        agent: str,
        timestamp: float,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: dict[str, Any] | None = None,
        duration_ms: int = 0,
    ) -> None:
        """Send tool call event."""
        event = TraceEvent(
            event_type="tool_call",
            agent=agent,
            timestamp=timestamp,
            data={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
            },
            duration_ms=duration_ms,
        )
        await self.broadcast_to_session(session_id, event)

    async def send_handoff(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        timestamp: float,
        data_passed: dict[str, Any] | None = None,
    ) -> None:
        """Send agent handoff event."""
        event = TraceEvent(
            event_type="handoff",
            agent=from_agent,
            timestamp=timestamp,
            data={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "data_passed": data_passed or {},
            },
        )
        await self.broadcast_to_session(session_id, event)

    async def send_agent_complete(
        self,
        session_id: str,
        agent: str,
        timestamp: float,
        result: dict[str, Any] | None = None,
        tokens_used: int = 0,
        duration_ms: int = 0,
    ) -> None:
        """Send agent completion event."""
        event = TraceEvent(
            event_type="agent_complete",
            agent=agent,
            timestamp=timestamp,
            data={"result": result or {}},
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
        await self.broadcast_to_session(session_id, event)

    async def send_interview_complete(
        self,
        session_id: str,
        timestamp: float,
        summary: dict[str, Any],
    ) -> None:
        """Send interview completion event with summary."""
        event = TraceEvent(
            event_type="interview_complete",
            agent="system",
            timestamp=timestamp,
            data=summary,
        )
        await self.broadcast_to_session(session_id, event)

    def get_session_trace(self, session_id: str) -> list[dict[str, Any]]:
        """
        Get all trace events for a session.

        Args:
            session_id: The session ID

        Returns:
            List of trace events as dictionaries
        """
        if session_id not in self.session_traces:
            return []

        return [
            {
                "event_type": e.event_type,
                "agent": e.agent,
                "timestamp": e.timestamp,
                "data": e.data,
                "tokens_used": e.tokens_used,
                "duration_ms": e.duration_ms,
            }
            for e in self.session_traces[session_id]
        ]

    def clear_session(self, session_id: str) -> None:
        """
        Clear trace data for a session.

        Args:
            session_id: The session ID to clear
        """
        if session_id in self.session_traces:
            del self.session_traces[session_id]


# Global connection manager instance
manager = ConnectionManager()
