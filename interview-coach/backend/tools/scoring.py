"""
Scoring Tools for Interview Evaluation

These tools provide the scoring functionality for the Scorer Agent.
They can be registered as MCP tools for transparent observation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreResult:
    """Individual dimension score with details."""
    dimension: str
    score: float
    max_score: float = 10.0
    details: str = ""
    examples: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "max_score": self.max_score,
            "details": self.details,
            "examples": self.examples or [],
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result with all dimensions."""
    grammar: ScoreResult
    content: ScoreResult
    fluency: ScoreResult
    vocabulary: ScoreResult
    overall: float
    highlights: list[str]
    issues: list[str]
    grammar_errors: list[dict[str, str]]
    sample_improvements: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scores": {
                "grammar": self.grammar.score,
                "content": self.content.score,
                "fluency": self.fluency.score,
                "vocabulary": self.vocabulary.score,
            },
            "score_details": {
                "grammar": self.grammar.to_dict(),
                "content": self.content.to_dict(),
                "fluency": self.fluency.to_dict(),
                "vocabulary": self.vocabulary.to_dict(),
            },
            "overall": self.overall,
            "highlights": self.highlights,
            "issues": self.issues,
            "grammar_errors": self.grammar_errors,
            "sample_improvements": self.sample_improvements,
        }


def calculate_overall_score(
    grammar: float,
    content: float,
    fluency: float,
    vocabulary: float,
    weights: dict[str, float] | None = None,
) -> float:
    """
    Calculate weighted overall score from dimension scores.

    Args:
        grammar: Grammar score (1-10)
        content: Content score (1-10)
        fluency: Fluency score (1-10)
        vocabulary: Vocabulary score (1-10)
        weights: Optional custom weights (default: equal weights)

    Returns:
        Weighted average score rounded to 1 decimal place
    """
    if weights is None:
        weights = {
            "grammar": 0.25,
            "content": 0.30,
            "fluency": 0.25,
            "vocabulary": 0.20,
        }

    overall = (
        grammar * weights["grammar"]
        + content * weights["content"]
        + fluency * weights["fluency"]
        + vocabulary * weights["vocabulary"]
    )

    return round(overall, 1)


def evaluate_answer(
    question: str,
    answer: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Evaluate an interview answer.

    This function is designed to be called by the Scorer Agent.
    It provides the structure for evaluation but the actual scoring
    is done by the LLM based on the scorer prompt.

    Args:
        question: The interview question that was asked
        answer: The candidate's answer
        context: Optional additional context (e.g., previous Q&A)

    Returns:
        Evaluation template to be filled by the Scorer Agent
    """
    # This is a template that guides the Scorer Agent
    # The actual evaluation is performed by the LLM
    evaluation_template = {
        "question": question,
        "answer": answer,
        "context": context or {},
        "evaluation_criteria": {
            "grammar": {
                "check_items": [
                    "Tense consistency",
                    "Subject-verb agreement",
                    "Article usage",
                    "Preposition accuracy",
                    "Sentence structure",
                ],
                "weight": 0.25,
            },
            "content": {
                "check_items": [
                    "Relevance to question",
                    "Logical structure",
                    "Specific examples",
                    "STAR method usage",
                    "Depth of response",
                ],
                "weight": 0.30,
            },
            "fluency": {
                "check_items": [
                    "Natural flow",
                    "Filler words frequency",
                    "Pacing",
                    "Confidence",
                    "Transitions",
                ],
                "weight": 0.25,
            },
            "vocabulary": {
                "check_items": [
                    "Word diversity",
                    "Accuracy",
                    "Professional terms",
                    "Register appropriateness",
                    "Idiomatic expressions",
                ],
                "weight": 0.20,
            },
        },
        "output_format": {
            "scores": {
                "grammar": "1-10",
                "content": "1-10",
                "fluency": "1-10",
                "vocabulary": "1-10",
            },
            "overall": "weighted average",
            "highlights": ["2-3 positive points"],
            "issues": ["2-3 areas for improvement"],
        },
    }

    return evaluation_template


# MCP Tool definition for claude-agent-sdk
def create_scoring_tools():
    """
    Create MCP tool definitions for the scoring system.

    Returns a list of tool definitions that can be registered
    with create_sdk_mcp_server().

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
        "evaluate_interview_answer",
        "Evaluate an interview answer across grammar, content, fluency, and vocabulary dimensions",
        {
            "question": str,
            "answer": str,
            "context": dict,
        },
    )
    async def evaluate_interview_answer_tool(args: dict[str, Any]) -> dict[str, Any]:
        """MCP tool wrapper for evaluate_answer."""
        result = evaluate_answer(
            question=args.get("question", ""),
            answer=args.get("answer", ""),
            context=args.get("context"),
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Evaluation template prepared for question: {args.get('question', '')[:50]}...",
                }
            ],
            "data": result,
        }

    @tool(
        "calculate_score",
        "Calculate the weighted overall score from individual dimension scores",
        {
            "grammar": float,
            "content": float,
            "fluency": float,
            "vocabulary": float,
        },
    )
    async def calculate_score_tool(args: dict[str, Any]) -> dict[str, Any]:
        """MCP tool wrapper for calculate_overall_score."""
        overall = calculate_overall_score(
            grammar=args.get("grammar", 5.0),
            content=args.get("content", 5.0),
            fluency=args.get("fluency", 5.0),
            vocabulary=args.get("vocabulary", 5.0),
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Overall score calculated: {overall}/10",
                }
            ],
            "data": {"overall": overall},
        }

    return [evaluate_interview_answer_tool, calculate_score_tool]
