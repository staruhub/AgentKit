"""
Interview Question Bank

Provides a curated set of interview questions for the demo.
Questions are categorized by type and difficulty.
"""

from dataclasses import dataclass
from typing import Any
from enum import Enum


class QuestionType(Enum):
    """Types of interview questions."""
    INTRODUCTION = "introduction"
    MOTIVATION = "motivation"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    CAREER = "career"
    TECHNICAL = "technical"


class Difficulty(Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class InterviewQuestion:
    """Interview question with metadata."""
    id: str
    question: str
    question_type: QuestionType
    difficulty: Difficulty
    follow_ups: list[str]
    tips: list[str]
    expected_duration_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "follow_ups": self.follow_ups,
            "tips": self.tips,
            "expected_duration_seconds": self.expected_duration_seconds,
        }


# Demo Question Bank
QUESTION_BANK: list[InterviewQuestion] = [
    InterviewQuestion(
        id="intro-001",
        question="Please introduce yourself briefly.",
        question_type=QuestionType.INTRODUCTION,
        difficulty=Difficulty.EASY,
        follow_ups=[
            "What made you choose your current career path?",
            "What's your proudest professional achievement?",
        ],
        tips=[
            "Keep it under 2 minutes",
            "Focus on professional background",
            "Mention relevant skills and experiences",
        ],
        expected_duration_seconds=90,
    ),
    InterviewQuestion(
        id="motiv-001",
        question="Why are you interested in this position?",
        question_type=QuestionType.MOTIVATION,
        difficulty=Difficulty.EASY,
        follow_ups=[
            "What specific aspects of our company appeal to you?",
            "How does this role fit into your career goals?",
        ],
        tips=[
            "Research the company beforehand",
            "Connect your skills to the job requirements",
            "Show genuine enthusiasm",
        ],
        expected_duration_seconds=60,
    ),
    InterviewQuestion(
        id="behav-001",
        question="Tell me about a challenge you faced at work and how you overcame it.",
        question_type=QuestionType.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        follow_ups=[
            "What did you learn from that experience?",
            "Would you do anything differently if faced with the same situation?",
        ],
        tips=[
            "Use the STAR method (Situation, Task, Action, Result)",
            "Be specific about your role",
            "Quantify results if possible",
        ],
        expected_duration_seconds=120,
    ),
    InterviewQuestion(
        id="career-001",
        question="Where do you see yourself in 5 years?",
        question_type=QuestionType.CAREER,
        difficulty=Difficulty.MEDIUM,
        follow_ups=[
            "What steps are you taking to achieve those goals?",
            "How does this position help you get there?",
        ],
        tips=[
            "Show ambition but be realistic",
            "Align goals with the company's growth",
            "Demonstrate commitment to professional development",
        ],
        expected_duration_seconds=60,
    ),
    InterviewQuestion(
        id="behav-002",
        question="Describe a time when you had to work with a difficult colleague.",
        question_type=QuestionType.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        follow_ups=[
            "How did you maintain professionalism?",
            "What was the outcome of that working relationship?",
        ],
        tips=[
            "Focus on the solution, not the drama",
            "Show empathy and communication skills",
            "Avoid speaking negatively about others",
        ],
        expected_duration_seconds=120,
    ),
    InterviewQuestion(
        id="situa-001",
        question="If you disagreed with your manager's decision, how would you handle it?",
        question_type=QuestionType.SITUATIONAL,
        difficulty=Difficulty.HARD,
        follow_ups=[
            "Can you give an example of when this happened?",
            "How do you balance expressing your opinion with respecting authority?",
        ],
        tips=[
            "Show respect for hierarchy",
            "Demonstrate professional communication",
            "Emphasize finding solutions, not creating conflict",
        ],
        expected_duration_seconds=90,
    ),
]


def get_question_bank(
    question_type: QuestionType | None = None,
    difficulty: Difficulty | None = None,
) -> list[InterviewQuestion]:
    """
    Get questions from the question bank with optional filtering.

    Args:
        question_type: Filter by question type
        difficulty: Filter by difficulty level

    Returns:
        List of matching questions
    """
    questions = QUESTION_BANK

    if question_type:
        questions = [q for q in questions if q.question_type == question_type]

    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]

    return questions


def get_interview_question(
    question_id: str | None = None,
    question_index: int | None = None,
) -> InterviewQuestion | None:
    """
    Get a specific interview question.

    Args:
        question_id: The unique question ID
        question_index: The index in the question bank (0-based)

    Returns:
        The question if found, None otherwise
    """
    if question_id:
        for q in QUESTION_BANK:
            if q.id == question_id:
                return q
        return None

    if question_index is not None:
        if 0 <= question_index < len(QUESTION_BANK):
            return QUESTION_BANK[question_index]
        return None

    # Return first question by default
    return QUESTION_BANK[0] if QUESTION_BANK else None


def get_demo_questions() -> list[InterviewQuestion]:
    """
    Get the subset of questions used for the demo.

    Returns the first 2 questions for a quick demo flow.
    """
    return QUESTION_BANK[:2]


# MCP Tool definitions
def create_question_tools():
    """
    Create MCP tool definitions for the question system.

    Note: Requires claude-agent-sdk to be installed.
    """
    try:
        from claude_agent_sdk import tool
    except ImportError:
        raise ImportError(
            "claude-agent-sdk is required for MCP tools. "
            "Install it with: pip install claude-agent-sdk"
        )

    @tool(
        "get_next_question",
        "Get the next interview question to ask the candidate",
        {
            "current_index": int,
            "question_type": str,
        },
    )
    async def get_next_question_tool(args: dict[str, Any]) -> dict[str, Any]:
        """MCP tool wrapper for getting next question."""
        current_index = args.get("current_index", 0)
        question = get_interview_question(question_index=current_index)

        if question:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": question.question,
                    }
                ],
                "data": question.to_dict(),
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No more questions available.",
                    }
                ],
                "is_error": True,
            }

    @tool(
        "get_question_tips",
        "Get tips for answering a specific question",
        {
            "question_id": str,
        },
    )
    async def get_question_tips_tool(args: dict[str, Any]) -> dict[str, Any]:
        """MCP tool wrapper for getting question tips."""
        question_id = args.get("question_id", "")
        question = get_interview_question(question_id=question_id)

        if question:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "\n".join(f"- {tip}" for tip in question.tips),
                    }
                ],
                "data": {"tips": question.tips, "follow_ups": question.follow_ups},
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Question not found.",
                    }
                ],
                "is_error": True,
            }

    return [get_next_question_tool, get_question_tips_tool]
