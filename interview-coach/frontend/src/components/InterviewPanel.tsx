/**
 * Interview Panel Component
 *
 * Displays the interview conversation and handles user input.
 */

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Send,
  RotateCcw,
  User,
  Bot,
  Loader2,
  MessageSquare,
} from 'lucide-react';
import { SubmitAnswerResponse } from '../utils/api';
import { ScoreCard } from './ScoreCard';

interface Message {
  id: string;
  role: 'interviewer' | 'candidate' | 'system';
  content: string;
  timestamp: number;
}

interface InterviewPanelProps {
  messages: Message[];
  currentQuestion: string;
  status: string;
  error: string | null;
  lastEvaluation: SubmitAnswerResponse | null;
  onSubmitAnswer: (answer: string) => void;
  onRestart: () => void;
}

export function InterviewPanel({
  messages,
  currentQuestion: _currentQuestion,
  status,
  error,
  lastEvaluation,
  onSubmitAnswer,
  onRestart,
}: InterviewPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && status === 'in_progress') {
      onSubmitAnswer(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const getMessageIcon = (role: string) => {
    switch (role) {
      case 'interviewer':
        return <Bot className="w-4 h-4" />;
      case 'candidate':
        return <User className="w-4 h-4" />;
      default:
        return <MessageSquare className="w-4 h-4" />;
    }
  };

  const getMessageStyle = (role: string) => {
    switch (role) {
      case 'interviewer':
        return 'bg-purple-50 border-purple-200';
      case 'candidate':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-emerald-50 border-emerald-200';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'interviewer':
        return 'Interviewer';
      case 'candidate':
        return 'You';
      default:
        return 'Feedback';
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col h-[calc(100vh-200px)] min-h-[500px]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900">Interview Session</h2>
            <p className="text-xs text-slate-500">
              {status === 'in_progress'
                ? 'Answer the question in English'
                : status === 'evaluating'
                ? 'Evaluating your answer...'
                : status === 'completed'
                ? 'Interview completed'
                : 'Starting...'}
            </p>
          </div>
        </div>

        {status === 'completed' && (
          <button
            onClick={onRestart}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            New Interview
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`animate-fade-in rounded-xl border p-4 ${getMessageStyle(message.role)}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  message.role === 'interviewer'
                    ? 'bg-purple-200 text-purple-700'
                    : message.role === 'candidate'
                    ? 'bg-blue-200 text-blue-700'
                    : 'bg-emerald-200 text-emerald-700'
                }`}
              >
                {getMessageIcon(message.role)}
              </div>
              <span className="text-sm font-medium text-slate-700">
                {getRoleLabel(message.role)}
              </span>
              <span className="text-xs text-slate-400">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <div className="markdown-content text-slate-700 text-sm">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>
        ))}

        {/* Score card after evaluation */}
        {lastEvaluation && messages.length > 0 && (
          <div className="animate-slide-in">
            <ScoreCard scores={lastEvaluation.evaluation.scores} />
          </div>
        )}

        {/* Typing indicator */}
        {status === 'evaluating' && (
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>AI is analyzing your answer...</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="px-4 py-3 border-t border-slate-200">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                status === 'in_progress'
                  ? 'Type your answer in English... (Press Enter to submit)'
                  : status === 'evaluating'
                  ? 'Please wait while we evaluate...'
                  : 'Interview completed'
              }
              disabled={status !== 'in_progress'}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              rows={1}
            />
          </div>

          <button
            type="submit"
            disabled={!inputValue.trim() || status !== 'in_progress'}
            className="px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        <p className="text-xs text-slate-400 mt-2 text-center">
          Tip: Use specific examples and the STAR method for better scores
        </p>
      </div>
    </div>
  );
}
