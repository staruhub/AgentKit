/**
 * Transparent AI Interview Coach - Main Application
 *
 * A multi-agent interview coaching system with real-time observation.
 */

import { useState, useCallback } from 'react';
import { InterviewPanel } from './components/InterviewPanel';
import { ObservationPanel } from './components/ObservationPanel';
import { useWebSocket, TraceEvent } from './hooks/useWebSocket';
import {
  startInterview,
  submitAnswer,
  StartInterviewResponse,
  SubmitAnswerResponse,
} from './utils/api';
import { Mic, Eye, Sparkles } from 'lucide-react';

type InterviewStatus = 'idle' | 'starting' | 'in_progress' | 'evaluating' | 'completed';

interface Message {
  id: string;
  role: 'interviewer' | 'candidate' | 'system';
  content: string;
  timestamp: number;
}

function App() {
  const [status, setStatus] = useState<InterviewStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [roundNumber, setRoundNumber] = useState(0);
  const [totalRounds, setTotalRounds] = useState(0);
  const [lastEvaluation, setLastEvaluation] = useState<SubmitAnswerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { events, isConnected, connect, clearEvents } = useWebSocket();

  const addMessage = useCallback((
    role: Message['role'],
    content: string
  ) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role,
        content,
        timestamp: Date.now(),
      },
    ]);
  }, []);

  const handleStartInterview = useCallback(async () => {
    setStatus('starting');
    setError(null);
    clearEvents();

    try {
      const response: StartInterviewResponse = await startInterview('Demo Candidate', true);

      setSessionId(response.session_id);
      setCurrentQuestion(response.current_question);
      setRoundNumber(response.round_number);
      setTotalRounds(response.total_rounds);

      // Connect to WebSocket for trace events
      connect(response.session_id);

      // Add interviewer greeting
      addMessage('interviewer', response.interviewer_greeting);

      setStatus('in_progress');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start interview');
      setStatus('idle');
    }
  }, [addMessage, clearEvents, connect]);

  const handleSubmitAnswer = useCallback(async (answer: string) => {
    if (!sessionId || !answer.trim()) return;

    // Add candidate's answer to messages
    addMessage('candidate', answer);
    setStatus('evaluating');

    try {
      const response: SubmitAnswerResponse = await submitAnswer(sessionId, answer);

      setLastEvaluation(response);

      // Add feedback as system message
      addMessage('system', response.feedback.summary);

      if (response.has_next_question && response.next_question) {
        // Move to next question
        setCurrentQuestion(response.next_question);
        setRoundNumber((prev) => prev + 1);
        addMessage('interviewer', `Great! Let's move on to the next question:\n\n**${response.next_question}**`);
        setStatus('in_progress');
      } else {
        // Interview complete
        addMessage('interviewer', 'Thank you for completing this interview session! Review your feedback in the panel on the right.');
        setStatus('completed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit answer');
      setStatus('in_progress');
    }
  }, [sessionId, addMessage]);

  const handleRestart = useCallback(() => {
    setStatus('idle');
    setSessionId(null);
    setMessages([]);
    setCurrentQuestion('');
    setRoundNumber(0);
    setTotalRounds(0);
    setLastEvaluation(null);
    setError(null);
    clearEvents();
  }, [clearEvents]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <Mic className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">
                Transparent AI Interview Coach
              </h1>
              <p className="text-xs text-slate-500">
                OneOneTalk × AgentKit Demo
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Status indicator */}
            <div className="flex items-center gap-2 text-sm">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-500' : 'bg-slate-300'
                }`}
              />
              <span className="text-slate-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Session info */}
            {sessionId && (
              <div className="text-sm text-slate-500">
                Round {roundNumber}/{totalRounds}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {status === 'idle' ? (
          /* Landing state */
          <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mb-6 shadow-lg shadow-primary-500/30">
              <Sparkles className="w-10 h-10 text-white" />
            </div>

            <h2 className="text-3xl font-bold text-slate-900 mb-3">
              Welcome to Your AI Interview Coach
            </h2>

            <p className="text-slate-600 max-w-lg mb-8">
              Practice English interviews with real-time AI feedback.
              Our transparent multi-agent system shows you exactly how
              your answers are evaluated.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <span>Interviewer Agent</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <span>Scorer Agent</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span>Feedback Agent</span>
              </div>
            </div>

            <button
              onClick={handleStartInterview}
              className="px-8 py-4 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 transition-all duration-200 flex items-center gap-2"
            >
              <Mic className="w-5 h-5" />
              Start Interview
            </button>

            <p className="text-xs text-slate-400 mt-4">
              Demo mode: 2 rounds of interview questions
            </p>
          </div>
        ) : (
          /* Interview state */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Interview Panel */}
            <InterviewPanel
              messages={messages}
              currentQuestion={currentQuestion}
              status={status}
              error={error}
              lastEvaluation={lastEvaluation}
              onSubmitAnswer={handleSubmitAnswer}
              onRestart={handleRestart}
            />

            {/* Observation Panel */}
            <ObservationPanel
              events={events}
              isConnected={isConnected}
              sessionId={sessionId}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-slate-500">
          <p>
            "每个英语学习者都值得一个透明的 AI 教练"
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Built with Claude Agent SDK | Volcengine Winter Conference Demo
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
