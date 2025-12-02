/**
 * Observation Panel Component
 *
 * Displays real-time trace events from the multi-agent system.
 * This is the "transparency" feature that shows users how AI decisions are made.
 */

import { useMemo } from 'react';
import {
  Eye,
  Zap,
  Clock,
  Hash,
  ArrowRight,
  Brain,
  Wrench,
  CheckCircle,
  AlertCircle,
  Activity,
} from 'lucide-react';
import {
  TraceEvent,
  getAgentBgColor,
  formatEventType,
  calculateTotalMetrics,
} from '../hooks/useWebSocket';

interface ObservationPanelProps {
  events: TraceEvent[];
  isConnected: boolean;
  sessionId: string | null;
}

export function ObservationPanel({
  events,
  isConnected,
  sessionId,
}: ObservationPanelProps) {
  const metrics = useMemo(() => calculateTotalMetrics(events), [events]);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'agent_start':
        return <Zap className="w-3 h-3" />;
      case 'agent_thinking':
        return <Brain className="w-3 h-3" />;
      case 'agent_complete':
        return <CheckCircle className="w-3 h-3" />;
      case 'tool_call':
        return <Wrench className="w-3 h-3" />;
      case 'handoff':
        return <ArrowRight className="w-3 h-3" />;
      default:
        return <Activity className="w-3 h-3" />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col h-[calc(100vh-200px)] min-h-[500px]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
              <Eye className="w-4 h-4 text-slate-600" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">AI Observation Panel</h2>
              <p className="text-xs text-slate-500">
                See how your AI coach thinks
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'
              }`}
            />
            <span className="text-xs text-slate-500">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>

        {/* Metrics bar */}
        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-600">
              {metrics.totalDuration}ms
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg">
            <Hash className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-600">
              {metrics.totalTokens} tokens
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg">
            <Activity className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-600">
              {events.length} events
            </span>
          </div>
        </div>
      </div>

      {/* Agent status indicators */}
      <div className="px-6 py-3 border-b border-slate-100 flex gap-4">
        <AgentIndicator
          name="Interviewer"
          color="purple"
          isActive={events.some(
            (e) => e.agent === 'interviewer' && e.event_type === 'agent_start'
          )}
          count={metrics.agentCounts['interviewer'] || 0}
        />
        <AgentIndicator
          name="Scorer"
          color="amber"
          isActive={events.some(
            (e) => e.agent === 'scorer' && e.event_type === 'agent_start'
          )}
          count={metrics.agentCounts['scorer'] || 0}
        />
        <AgentIndicator
          name="Feedback"
          color="emerald"
          isActive={events.some(
            (e) => e.agent === 'feedback' && e.event_type === 'agent_start'
          )}
          count={metrics.agentCounts['feedback'] || 0}
        />
      </div>

      {/* Event stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <Eye className="w-8 h-8 text-slate-400" />
            </div>
            <p className="text-slate-500 text-sm">
              Waiting for agent activity...
            </p>
            <p className="text-slate-400 text-xs mt-1">
              Events will appear here as the AI processes your interview
            </p>
          </div>
        ) : (
          events.map((event, index) => (
            <TraceEventCard key={`${event.timestamp}-${index}`} event={event} />
          ))
        )}
      </div>

      {/* Footer with session info */}
      {sessionId && (
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Session: {sessionId.slice(0, 8)}...</span>
            <span>
              {events.length > 0
                ? `Last update: ${formatTimestamp(events[events.length - 1].timestamp)}`
                : 'No events yet'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

interface AgentIndicatorProps {
  name: string;
  color: 'purple' | 'amber' | 'emerald';
  isActive: boolean;
  count: number;
}

function AgentIndicator({ name, color, isActive, count }: AgentIndicatorProps) {
  const colorClasses = {
    purple: {
      bg: 'bg-purple-500',
      ring: 'ring-purple-200',
      text: 'text-purple-700',
    },
    amber: {
      bg: 'bg-amber-500',
      ring: 'ring-amber-200',
      text: 'text-amber-700',
    },
    emerald: {
      bg: 'bg-emerald-500',
      ring: 'ring-emerald-200',
      text: 'text-emerald-700',
    },
  };

  const colors = colorClasses[color];

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <div
          className={`w-3 h-3 rounded-full ${colors.bg} ${
            isActive ? `ring-4 ${colors.ring} animate-pulse` : ''
          }`}
        />
      </div>
      <span className={`text-xs font-medium ${colors.text}`}>{name}</span>
      {count > 0 && (
        <span className="text-xs text-slate-400">({count})</span>
      )}
    </div>
  );
}

interface TraceEventCardProps {
  event: TraceEvent;
}

function TraceEventCard({ event }: TraceEventCardProps) {
  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'agent_start':
        return <Zap className="w-3 h-3" />;
      case 'agent_thinking':
        return <Brain className="w-3 h-3" />;
      case 'agent_complete':
        return <CheckCircle className="w-3 h-3" />;
      case 'tool_call':
        return <Wrench className="w-3 h-3" />;
      case 'handoff':
        return <ArrowRight className="w-3 h-3" />;
      default:
        return <Activity className="w-3 h-3" />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <div className="animate-slide-in bg-slate-50 rounded-lg p-3 border border-slate-100">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${getAgentBgColor(
              event.agent
            )}`}
          >
            {event.agent}
          </span>
          <span className="inline-flex items-center gap-1 text-xs text-slate-500">
            {getEventIcon(event.event_type)}
            {formatEventType(event.event_type)}
          </span>
        </div>
        <span className="text-xs text-slate-400">
          {formatTimestamp(event.timestamp)}
        </span>
      </div>

      {/* Event-specific content */}
      {event.event_type === 'agent_thinking' && event.data.thinking && (
        <div className="mt-2 text-xs text-slate-600 bg-white rounded p-2 border border-slate-100">
          <span className="text-slate-400 italic">Thinking: </span>
          {event.data.thinking}
        </div>
      )}

      {event.event_type === 'tool_call' && event.data.tool_name && (
        <div className="mt-2 text-xs">
          <div className="bg-white rounded p-2 border border-slate-100">
            <div className="font-mono text-slate-700">
              {event.data.tool_name}()
            </div>
            {event.data.tool_input && (
              <div className="mt-1 text-slate-500 truncate">
                Input: {JSON.stringify(event.data.tool_input).slice(0, 100)}...
              </div>
            )}
          </div>
        </div>
      )}

      {event.event_type === 'handoff' && (
        <div className="mt-2 flex items-center gap-2 text-xs text-slate-600">
          <span className="font-medium">{event.data.from_agent}</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="font-medium">{event.data.to_agent}</span>
        </div>
      )}

      {event.event_type === 'agent_complete' && (
        <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
          {event.tokens_used > 0 && (
            <span className="flex items-center gap-1">
              <Hash className="w-3 h-3" />
              {event.tokens_used} tokens
            </span>
          )}
          {event.duration_ms > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {event.duration_ms}ms
            </span>
          )}
        </div>
      )}
    </div>
  );
}
