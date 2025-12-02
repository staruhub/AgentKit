"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Any
from enum import Enum


class InterviewStatus(str, Enum):
    """Interview session status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    FEEDBACK = "feedback"
    COMPLETED = "completed"


class AgentType(str, Enum):
    """Agent types in the interview system."""
    INTERVIEWER = "interviewer"
    SCORER = "scorer"
    FEEDBACK = "feedback"


# Request Models
class StartInterviewRequest(BaseModel):
    """Request to start a new interview session."""
    candidate_name: str = Field(default="Candidate", description="Name of the candidate")
    demo_mode: bool = Field(default=True, description="Whether to run in demo mode (limited questions)")


class SubmitAnswerRequest(BaseModel):
    """Request to submit an interview answer."""
    session_id: str = Field(..., description="Interview session ID")
    answer: str = Field(..., description="Candidate's answer to the current question")


class GetFeedbackRequest(BaseModel):
    """Request to get feedback for the current round."""
    session_id: str = Field(..., description="Interview session ID")


# Response Models
class AgentTraceEvent(BaseModel):
    """Real-time trace event from an agent."""
    event_type: str = Field(..., description="Type of event (start, thinking, tool_call, complete)")
    agent: AgentType = Field(..., description="Which agent generated this event")
    timestamp: float = Field(..., description="Unix timestamp of the event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    tokens_used: int = Field(default=0, description="Tokens consumed for this event")
    duration_ms: int = Field(default=0, description="Duration of this operation in milliseconds")


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown."""
    grammar: float = Field(..., ge=0, le=10)
    content: float = Field(..., ge=0, le=10)
    fluency: float = Field(..., ge=0, le=10)
    vocabulary: float = Field(..., ge=0, le=10)
    overall: float = Field(..., ge=0, le=10)


class EvaluationResponse(BaseModel):
    """Evaluation result from the Scorer Agent."""
    scores: ScoreBreakdown
    highlights: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    grammar_errors: list[dict[str, str]] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    """Feedback from the Feedback Agent."""
    summary: str = Field(..., description="Markdown-formatted feedback summary")
    practice_suggestions: list[str] = Field(default_factory=list)
    next_focus_areas: list[str] = Field(default_factory=list)


class InterviewRound(BaseModel):
    """A single round of interview Q&A."""
    round_number: int
    question: str
    question_id: str
    answer: str | None = None
    evaluation: EvaluationResponse | None = None
    feedback: FeedbackResponse | None = None


class InterviewSession(BaseModel):
    """Complete interview session state."""
    session_id: str
    candidate_name: str
    status: InterviewStatus
    current_round: int
    total_rounds: int
    rounds: list[InterviewRound] = Field(default_factory=list)
    created_at: float
    updated_at: float


class StartInterviewResponse(BaseModel):
    """Response when starting a new interview."""
    session_id: str
    status: InterviewStatus
    current_question: str
    question_id: str
    round_number: int
    total_rounds: int
    interviewer_greeting: str


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    session_id: str
    status: InterviewStatus
    evaluation: EvaluationResponse
    feedback: FeedbackResponse
    has_next_question: bool
    next_question: str | None = None


class TraceMetrics(BaseModel):
    """Aggregated trace metrics for the observation panel."""
    total_duration_ms: int
    total_tokens: int
    agent_metrics: dict[str, dict[str, Any]]
    tool_calls: list[dict[str, Any]]


class InterviewCompleteResponse(BaseModel):
    """Response when interview is completed."""
    session_id: str
    status: InterviewStatus
    rounds: list[InterviewRound]
    overall_feedback: str
    trace_metrics: TraceMetrics
