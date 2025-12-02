"""
Interview Runner - Claude Agent SDK Integration

This module provides the actual integration with Claude Agent SDK
for running the multi-agent interview flow.

In the demo API routes, we use simplified mock responses.
This module shows how to integrate with the real Claude Agent SDK.
"""

import time
import json
from typing import Any, AsyncIterator
from dataclasses import dataclass

# Note: In production, uncomment these imports and implement the actual SDK integration
# from claude_agent_sdk import (
#     query,
#     ClaudeSDKClient,
#     ClaudeAgentOptions,
#     AgentDefinition,
#     create_sdk_mcp_server,
#     tool,
#     AssistantMessage,
#     TextBlock,
#     ToolUseBlock,
# )

from agents import (
    INTERVIEWER_AGENT,
    INTERVIEWER_PROMPT,
    SCORER_AGENT,
    SCORER_PROMPT,
    FEEDBACK_AGENT,
    FEEDBACK_PROMPT,
)
from tools.scoring import evaluate_answer, calculate_overall_score
from tools.questions import get_interview_question, get_demo_questions


@dataclass
class TraceEvent:
    """Trace event for observation panel."""
    event_type: str
    agent: str
    timestamp: float
    data: dict[str, Any]
    tokens_used: int = 0
    duration_ms: int = 0


@dataclass
class InterviewResult:
    """Result from a single interview round."""
    question: str
    answer: str
    evaluation: dict[str, Any]
    feedback: str
    trace_events: list[TraceEvent]


class InterviewRunner:
    """
    Runs the multi-agent interview flow using Claude Agent SDK.

    This class orchestrates the three agents:
    1. Interviewer - Asks questions
    2. Scorer - Evaluates answers
    3. Feedback - Provides improvement suggestions
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.questions = get_demo_questions() if demo_mode else []
        self.current_question_index = 0
        self.trace_events: list[TraceEvent] = []

        # Initialize agents configuration
        # In production, this would use ClaudeAgentOptions
        self.agents_config = {
            "interviewer": INTERVIEWER_AGENT,
            "scorer": SCORER_AGENT,
            "feedback": FEEDBACK_AGENT,
        }

    def _emit_trace(
        self,
        event_type: str,
        agent: str,
        data: dict[str, Any],
        tokens: int = 0,
        duration: int = 0,
    ) -> TraceEvent:
        """Emit a trace event."""
        event = TraceEvent(
            event_type=event_type,
            agent=agent,
            timestamp=time.time(),
            data=data,
            tokens_used=tokens,
            duration_ms=duration,
        )
        self.trace_events.append(event)
        return event

    async def get_next_question(self) -> str | None:
        """Get the next interview question."""
        if self.current_question_index >= len(self.questions):
            return None

        question = self.questions[self.current_question_index]
        self.current_question_index += 1

        self._emit_trace(
            "agent_start",
            "interviewer",
            {"action": "get_question"},
        )

        return question.question

    async def run_evaluation(
        self,
        question: str,
        answer: str,
    ) -> AsyncIterator[TraceEvent]:
        """
        Run the evaluation flow for an answer.

        Yields trace events as the evaluation progresses.
        """
        start_time = time.time()

        # === Interviewer acknowledges answer ===
        yield self._emit_trace(
            "agent_complete",
            "interviewer",
            {"message": "Answer received, handing off to scorer"},
            tokens=20,
            duration=100,
        )

        # === Handoff to Scorer ===
        yield self._emit_trace(
            "handoff",
            "interviewer",
            {
                "from": "interviewer",
                "to": "scorer",
                "data": {"question": question, "answer_preview": answer[:100]},
            },
        )

        # === Scorer Agent ===
        yield self._emit_trace(
            "agent_start",
            "scorer",
            {"message": "Starting evaluation"},
        )

        yield self._emit_trace(
            "thinking",
            "scorer",
            {"thinking": "Analyzing grammar patterns and sentence structures..."},
        )

        yield self._emit_trace(
            "thinking",
            "scorer",
            {"thinking": "Evaluating content relevance and logical flow..."},
        )

        yield self._emit_trace(
            "tool_call",
            "scorer",
            {
                "tool": "evaluate_interview_answer",
                "input": {"question": question, "answer": answer},
            },
        )

        # Generate evaluation
        evaluation = self._generate_evaluation(question, answer)

        scorer_duration = int((time.time() - start_time) * 1000)
        yield self._emit_trace(
            "agent_complete",
            "scorer",
            {"evaluation": evaluation},
            tokens=156,
            duration=scorer_duration,
        )

        # === Handoff to Feedback ===
        yield self._emit_trace(
            "handoff",
            "scorer",
            {
                "from": "scorer",
                "to": "feedback",
                "data": {"evaluation": evaluation},
            },
        )

        # === Feedback Agent ===
        feedback_start = time.time()

        yield self._emit_trace(
            "agent_start",
            "feedback",
            {"message": "Generating feedback"},
        )

        yield self._emit_trace(
            "thinking",
            "feedback",
            {"thinking": "Synthesizing evaluation into actionable feedback..."},
        )

        # Generate feedback
        feedback = self._generate_feedback(evaluation, question, answer)

        feedback_duration = int((time.time() - feedback_start) * 1000)
        yield self._emit_trace(
            "agent_complete",
            "feedback",
            {"feedback_preview": feedback[:200]},
            tokens=141,
            duration=feedback_duration,
        )

    def _generate_evaluation(self, question: str, answer: str) -> dict[str, Any]:
        """Generate evaluation for demo purposes."""
        answer_length = len(answer.split())
        has_examples = any(
            word in answer.lower()
            for word in ["example", "instance", "specifically", "for instance"]
        )
        uses_star = any(
            word in answer.lower()
            for word in ["situation", "task", "action", "result"]
        )

        # Scoring heuristics
        grammar = min(8.5, 6.0 + answer_length / 50)
        content = 8.0 if uses_star else (7.0 if has_examples else 6.0)
        fluency = min(7.5, 5.5 + answer_length / 40)
        vocabulary = 7.0

        overall = calculate_overall_score(grammar, content, fluency, vocabulary)

        highlights = []
        if uses_star:
            highlights.append("Excellent use of STAR method to structure response")
        if has_examples:
            highlights.append("Good use of specific examples")
        if answer_length > 50:
            highlights.append("Comprehensive and detailed response")
        if not highlights:
            highlights.append("Clear communication of main points")

        issues = []
        if grammar < 7:
            issues.append("Some grammatical inconsistencies in tense usage")
        if not has_examples:
            issues.append("Consider adding specific examples to strengthen your answer")
        if answer_length < 30:
            issues.append("Response could be more detailed")

        return {
            "scores": {
                "grammar": round(grammar, 1),
                "content": round(content, 1),
                "fluency": round(fluency, 1),
                "vocabulary": round(vocabulary, 1),
            },
            "overall": overall,
            "highlights": highlights,
            "issues": issues,
            "grammar_errors": [
                {
                    "error": "Watch for tense consistency",
                    "suggestion": "Keep past tense consistent when describing past experiences",
                }
            ],
        }

    def _generate_feedback(
        self,
        evaluation: dict[str, Any],
        question: str,
        answer: str,
    ) -> str:
        """Generate feedback markdown for demo purposes."""
        scores = evaluation["scores"]
        overall = evaluation["overall"]
        stars = "⭐" * int(overall)

        feedback = f"""## 面试回答评估

**综合得分：{overall} / 10** {stars}

### 🎉 做得好的地方
"""
        for i, highlight in enumerate(evaluation["highlights"], 1):
            feedback += f"{i}. **{highlight}**\n"

        feedback += """
### 📈 可以提升的地方
"""
        for i, issue in enumerate(evaluation["issues"], 1):
            feedback += f"{i}. **{issue}**\n"

        feedback += f"""
### 📊 详细评分
| 维度 | 得分 | 说明 |
|------|------|------|
| 语法 Grammar | {scores['grammar']}/10 | 句子结构和时态使用 |
| 内容 Content | {scores['content']}/10 | 回答的相关性和深度 |
| 流利度 Fluency | {scores['fluency']}/10 | 表达的流畅度 |
| 词汇 Vocabulary | {scores['vocabulary']}/10 | 词汇的丰富度和准确性 |

### 💡 练习建议
1. 每天用英语录制一段2分钟的工作总结，注意时态一致性
2. 练习使用 STAR 方法组织你的回答（Situation, Task, Action, Result）
"""
        return feedback

    def get_trace_summary(self) -> dict[str, Any]:
        """Get a summary of all trace events."""
        total_tokens = sum(e.tokens_used for e in self.trace_events)
        total_duration = sum(e.duration_ms for e in self.trace_events)

        agent_stats: dict[str, dict[str, int]] = {}
        for event in self.trace_events:
            if event.agent not in agent_stats:
                agent_stats[event.agent] = {"events": 0, "tokens": 0, "duration": 0}
            agent_stats[event.agent]["events"] += 1
            agent_stats[event.agent]["tokens"] += event.tokens_used
            agent_stats[event.agent]["duration"] += event.duration_ms

        return {
            "total_events": len(self.trace_events),
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration,
            "agent_stats": agent_stats,
        }


# Production implementation with actual Claude Agent SDK
async def run_interview_with_sdk(question: str, answer: str) -> AsyncIterator[dict[str, Any]]:
    """
    Run interview evaluation using the actual Claude Agent SDK.

    This is the production implementation that uses the real SDK.
    Currently commented out for demo purposes.
    """
    # Uncomment and implement when Claude Agent SDK is available
    """
    from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

    # Create MCP server with scoring tools
    from tools.scoring import create_scoring_tools
    scoring_tools = create_scoring_tools()
    scoring_server = create_sdk_mcp_server(
        name="interview_scorer",
        version="1.0.0",
        tools=scoring_tools,
    )

    # Configure agents
    options = ClaudeAgentOptions(
        agents={
            "interviewer": AgentDefinition(
                description="Professional English interviewer",
                prompt=INTERVIEWER_PROMPT,
                model="sonnet",
            ),
            "scorer": AgentDefinition(
                description="English proficiency evaluator",
                prompt=SCORER_PROMPT,
                tools=["mcp__interview_scorer__evaluate_interview_answer"],
                model="sonnet",
            ),
            "feedback": AgentDefinition(
                description="Supportive English coach",
                prompt=FEEDBACK_PROMPT,
                model="sonnet",
            ),
        },
        mcp_servers={"interview_scorer": scoring_server},
        allowed_tools=[
            "mcp__interview_scorer__evaluate_interview_answer",
            "mcp__interview_scorer__calculate_score",
        ],
    )

    # Run evaluation
    evaluation_prompt = f'''
    Please evaluate the following interview answer:

    Question: {question}

    Answer: {answer}

    First, use the scorer agent to evaluate the answer across all dimensions.
    Then, use the feedback agent to generate improvement suggestions in Chinese.
    '''

    async for message in query(prompt=evaluation_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield {"type": "text", "content": block.text}
                elif isinstance(block, ToolUseBlock):
                    yield {
                        "type": "tool_call",
                        "tool": block.name,
                        "input": block.input,
                    }
    """
    pass
