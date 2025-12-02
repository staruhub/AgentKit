/**
 * WebSocket hook for real-time trace streaming
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface TraceEvent {
  event_type: string;
  agent: string;
  timestamp: number;
  data: Record<string, any>;
  tokens_used: number;
  duration_ms: number;
  session_id: string;
}

export interface UseWebSocketReturn {
  events: TraceEvent[];
  isConnected: boolean;
  error: string | null;
  connect: (sessionId: string) => void;
  disconnect: () => void;
  clearEvents: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  const connect = useCallback((sessionId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/interview/ws/${sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data: TraceEvent = JSON.parse(event.data);
          setEvents((prev) => [...prev, data]);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        console.log('WebSocket closed:', event.code, event.reason);

        // Auto-reconnect logic
        if (
          reconnectAttempts.current < maxReconnectAttempts &&
          event.code !== 1000 // Normal closure
        ) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`Reconnecting in ${delay}ms...`);
          setTimeout(() => connect(sessionId), delay);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      setError('Failed to create WebSocket connection');
      console.error('WebSocket creation error:', e);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    events,
    isConnected,
    error,
    connect,
    disconnect,
    clearEvents,
  };
}

// Utility functions for trace events
export function getAgentColor(agent: string): string {
  switch (agent) {
    case 'interviewer':
      return 'rgb(139, 92, 246)'; // Purple
    case 'scorer':
      return 'rgb(245, 158, 11)'; // Amber
    case 'feedback':
      return 'rgb(16, 185, 129)'; // Emerald
    default:
      return 'rgb(107, 114, 128)'; // Gray
  }
}

export function getAgentBgColor(agent: string): string {
  switch (agent) {
    case 'interviewer':
      return 'bg-purple-100 text-purple-800';
    case 'scorer':
      return 'bg-amber-100 text-amber-800';
    case 'feedback':
      return 'bg-emerald-100 text-emerald-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function formatEventType(eventType: string): string {
  switch (eventType) {
    case 'agent_start':
      return 'Started';
    case 'agent_thinking':
      return 'Thinking';
    case 'agent_complete':
      return 'Completed';
    case 'tool_call':
      return 'Tool Call';
    case 'handoff':
      return 'Handoff';
    case 'interview_complete':
      return 'Interview Complete';
    default:
      return eventType;
  }
}

export function calculateTotalMetrics(events: TraceEvent[]): {
  totalTokens: number;
  totalDuration: number;
  agentCounts: Record<string, number>;
} {
  let totalTokens = 0;
  let totalDuration = 0;
  const agentCounts: Record<string, number> = {};

  for (const event of events) {
    totalTokens += event.tokens_used || 0;
    totalDuration += event.duration_ms || 0;

    if (event.agent) {
      agentCounts[event.agent] = (agentCounts[event.agent] || 0) + 1;
    }
  }

  return { totalTokens, totalDuration, agentCounts };
}
