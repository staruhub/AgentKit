/**
 * API utility functions for Interview Coach
 */

const API_BASE = '/api/interview';

export interface StartInterviewResponse {
  session_id: string;
  status: string;
  current_question: string;
  question_id: string;
  round_number: number;
  total_rounds: number;
  interviewer_greeting: string;
}

export interface ScoreBreakdown {
  grammar: number;
  content: number;
  fluency: number;
  vocabulary: number;
  overall: number;
}

export interface EvaluationResponse {
  scores: ScoreBreakdown;
  highlights: string[];
  issues: string[];
  grammar_errors: Array<{ error: string; suggestion: string }>;
}

export interface FeedbackResponse {
  summary: string;
  practice_suggestions: string[];
  next_focus_areas: string[];
}

export interface SubmitAnswerResponse {
  session_id: string;
  status: string;
  evaluation: EvaluationResponse;
  feedback: FeedbackResponse;
  has_next_question: boolean;
  next_question: string | null;
}

export interface InterviewRound {
  round_number: number;
  question: string;
  question_id: string;
  answer: string | null;
  evaluation: EvaluationResponse | null;
  feedback: FeedbackResponse | null;
}

export interface InterviewSession {
  session_id: string;
  candidate_name: string;
  status: string;
  current_round: number;
  total_rounds: number;
  rounds: InterviewRound[];
  created_at: number;
  updated_at: number;
}

export interface TraceMetrics {
  total_duration_ms: number;
  total_tokens: number;
  agent_metrics: Record<string, { calls: number; tokens: number; duration_ms: number }>;
  tool_calls: Array<{ tool_name: string; tool_input: any; tool_output: any }>;
}

export interface InterviewCompleteResponse {
  session_id: string;
  status: string;
  rounds: InterviewRound[];
  overall_feedback: string;
  trace_metrics: TraceMetrics;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

export async function startInterview(
  candidateName: string = 'Candidate',
  demoMode: boolean = true
): Promise<StartInterviewResponse> {
  return fetchApi<StartInterviewResponse>('/start', {
    method: 'POST',
    body: JSON.stringify({
      candidate_name: candidateName,
      demo_mode: demoMode,
    }),
  });
}

export async function submitAnswer(
  sessionId: string,
  answer: string
): Promise<SubmitAnswerResponse> {
  return fetchApi<SubmitAnswerResponse>('/answer', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      answer: answer,
    }),
  });
}

export async function getSession(sessionId: string): Promise<InterviewSession> {
  return fetchApi<InterviewSession>(`/session/${sessionId}`);
}

export async function completeInterview(
  sessionId: string
): Promise<InterviewCompleteResponse> {
  return fetchApi<InterviewCompleteResponse>(`/session/${sessionId}/complete`);
}

export async function getTrace(
  sessionId: string
): Promise<Array<Record<string, any>>> {
  return fetchApi<Array<Record<string, any>>>(`/trace/${sessionId}`);
}

export function createWebSocket(sessionId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return new WebSocket(`${protocol}//${host}/api/interview/ws/${sessionId}`);
}
