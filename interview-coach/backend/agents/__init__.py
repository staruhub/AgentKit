"""
Interview Coach Agents

This module contains the three main agents for the interview coaching system:
- InterviewerAgent: Conducts the interview, asks questions
- ScorerAgent: Evaluates answers across multiple dimensions
- FeedbackAgent: Provides constructive feedback and suggestions
"""

from .interviewer import INTERVIEWER_AGENT, INTERVIEWER_PROMPT
from .scorer import SCORER_AGENT, SCORER_PROMPT
from .feedback import FEEDBACK_AGENT, FEEDBACK_PROMPT

__all__ = [
    "INTERVIEWER_AGENT",
    "INTERVIEWER_PROMPT",
    "SCORER_AGENT",
    "SCORER_PROMPT",
    "FEEDBACK_AGENT",
    "FEEDBACK_PROMPT",
]
