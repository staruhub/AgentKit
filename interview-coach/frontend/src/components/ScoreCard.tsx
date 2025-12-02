/**
 * Score Card Component
 *
 * Displays the evaluation scores in a visual format.
 */

import { ScoreBreakdown } from '../utils/api';

interface ScoreCardProps {
  scores: ScoreBreakdown;
}

export function ScoreCard({ scores }: ScoreCardProps) {
  const dimensions = [
    { key: 'grammar', label: 'Grammar', labelCn: '语法', color: 'bg-blue-500' },
    { key: 'content', label: 'Content', labelCn: '内容', color: 'bg-purple-500' },
    { key: 'fluency', label: 'Fluency', labelCn: '流利度', color: 'bg-amber-500' },
    { key: 'vocabulary', label: 'Vocabulary', labelCn: '词汇', color: 'bg-emerald-500' },
  ] as const;

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-emerald-600';
    if (score >= 6) return 'text-amber-600';
    return 'text-red-600';
  };

  const getStars = (score: number) => {
    const fullStars = Math.floor(score / 2);
    const stars = [];
    for (let i = 0; i < 5; i++) {
      stars.push(
        <span
          key={i}
          className={i < fullStars ? 'text-amber-400' : 'text-slate-200'}
        >
          ★
        </span>
      );
    }
    return stars;
  };

  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200">
      {/* Overall score */}
      <div className="text-center mb-4">
        <div className="text-3xl font-bold text-slate-900">
          {scores.overall.toFixed(1)}
          <span className="text-lg text-slate-400">/10</span>
        </div>
        <div className="text-lg">{getStars(scores.overall)}</div>
        <p className="text-xs text-slate-500 mt-1">Overall Score</p>
      </div>

      {/* Dimension scores */}
      <div className="space-y-3">
        {dimensions.map(({ key, label, labelCn, color }) => {
          const score = scores[key];
          const percentage = (score / 10) * 100;

          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-600">
                  {label} <span className="text-slate-400">({labelCn})</span>
                </span>
                <span className={`text-sm font-semibold ${getScoreColor(score)}`}>
                  {score.toFixed(1)}
                </span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${color} rounded-full transition-all duration-500`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Score interpretation */}
      <div className="mt-4 pt-3 border-t border-slate-200">
        <p className="text-xs text-center text-slate-500">
          {scores.overall >= 8
            ? 'Excellent! Your answer demonstrates strong English proficiency.'
            : scores.overall >= 6
            ? 'Good effort! There are some areas for improvement.'
            : 'Keep practicing! Focus on the areas highlighted in the feedback.'}
        </p>
      </div>
    </div>
  );
}

interface ScoreRingProps {
  score: number;
  maxScore?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ScoreRing({
  score,
  maxScore = 10,
  size = 80,
  strokeWidth = 8,
  label,
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = (score / maxScore) * 100;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    if (percentage >= 80) return '#10b981'; // emerald
    if (percentage >= 60) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-slate-900">
          {score.toFixed(1)}
        </span>
        {label && <span className="text-xs text-slate-500">{label}</span>}
      </div>
    </div>
  );
}
