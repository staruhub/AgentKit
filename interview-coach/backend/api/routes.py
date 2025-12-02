"""
API routes for the interview coaching system.
"""

import time
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from .models import (
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    InterviewSession,
    InterviewStatus,
    InterviewRound,
    ScoreBreakdown,
    EvaluationResponse,
    FeedbackResponse,
    TraceMetrics,
    InterviewCompleteResponse,
)
from .websocket import manager, TraceEvent
from ..tools.questions import get_demo_questions, get_interview_question

router = APIRouter(prefix="/api/interview", tags=["interview"])

# In-memory session storage (for demo purposes)
sessions: dict[str, InterviewSession] = {}


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    """
    Start a new interview session.

    This initializes the interview and returns the first question
    from the Interviewer Agent.
    """
    session_id = str(uuid.uuid4())
    current_time = time.time()

    # Get demo questions
    demo_questions = get_demo_questions()
    total_rounds = len(demo_questions) if request.demo_mode else 4

    # Get first question
    first_question = demo_questions[0] if demo_questions else get_interview_question(question_index=0)

    if not first_question:
        raise HTTPException(status_code=500, detail="No questions available")

    # Create session
    session = InterviewSession(
        session_id=session_id,
        candidate_name=request.candidate_name,
        status=InterviewStatus.IN_PROGRESS,
        current_round=1,
        total_rounds=total_rounds,
        rounds=[
            InterviewRound(
                round_number=1,
                question=first_question.question,
                question_id=first_question.id,
            )
        ],
        created_at=current_time,
        updated_at=current_time,
    )

    sessions[session_id] = session

    # Send trace events
    await manager.send_agent_start(
        session_id=session_id,
        agent="interviewer",
        timestamp=current_time,
        message="Starting interview session",
    )

    greeting = f"""Hello {request.candidate_name}! Welcome to this interview session.

I'll be asking you a few questions to assess your English communication skills. Please take your time to think before answering, and feel free to ask for clarification if needed.

Let's begin with our first question:

**{first_question.question}**

Please respond whenever you're ready."""

    await manager.send_agent_complete(
        session_id=session_id,
        agent="interviewer",
        timestamp=time.time(),
        result={"question": first_question.question},
        tokens_used=45,
        duration_ms=int((time.time() - current_time) * 1000),
    )

    return StartInterviewResponse(
        session_id=session_id,
        status=InterviewStatus.IN_PROGRESS,
        current_question=first_question.question,
        question_id=first_question.id,
        round_number=1,
        total_rounds=total_rounds,
        interviewer_greeting=greeting,
    )


@router.post("/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest) -> SubmitAnswerResponse:
    """
    Submit an answer to the current interview question.

    This triggers the Scorer Agent to evaluate the answer,
    then the Feedback Agent to generate improvement suggestions.
    """
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview is not in progress")

    current_round = session.rounds[-1]
    current_round.answer = request.answer

    start_time = time.time()

    # Update status to evaluating
    session.status = InterviewStatus.EVALUATING
    session.updated_at = time.time()

    # === Scorer Agent Phase ===
    await manager.send_handoff(
        session_id=request.session_id,
        from_agent="interviewer",
        to_agent="scorer",
        timestamp=time.time(),
        data_passed={
            "question": current_round.question,
            "answer": request.answer,
        },
    )

    await manager.send_agent_start(
        session_id=request.session_id,
        agent="scorer",
        timestamp=time.time(),
        message="Evaluating answer...",
    )

    # Simulate thinking
    await manager.send_agent_thinking(
        session_id=request.session_id,
        agent="scorer",
        timestamp=time.time(),
        thinking="Analyzing grammar, content structure, fluency patterns, and vocabulary usage...",
    )

    # Simulate tool call
    await manager.send_tool_call(
        session_id=request.session_id,
        agent="scorer",
        timestamp=time.time(),
        tool_name="evaluate_interview_answer",
        tool_input={
            "question": current_round.question,
            "answer": request.answer[:100] + "..." if len(request.answer) > 100 else request.answer,
        },
        tool_output={"status": "evaluation_complete"},
        duration_ms=150,
    )

    # Generate evaluation (in real implementation, this comes from Claude Agent SDK)
    evaluation = await _generate_evaluation(current_round.question, request.answer)
    current_round.evaluation = evaluation

    scorer_complete_time = time.time()
    await manager.send_agent_complete(
        session_id=request.session_id,
        agent="scorer",
        timestamp=scorer_complete_time,
        result={
            "scores": evaluation.scores.model_dump(),
            "highlights": evaluation.highlights,
            "issues": evaluation.issues,
        },
        tokens_used=156,
        duration_ms=int((scorer_complete_time - start_time) * 1000),
    )

    # === Feedback Agent Phase ===
    session.status = InterviewStatus.FEEDBACK

    await manager.send_handoff(
        session_id=request.session_id,
        from_agent="scorer",
        to_agent="feedback",
        timestamp=time.time(),
        data_passed={
            "question": current_round.question,
            "answer": request.answer,
            "scores": evaluation.scores.model_dump(),
            "highlights": evaluation.highlights,
            "issues": evaluation.issues,
        },
    )

    await manager.send_agent_start(
        session_id=request.session_id,
        agent="feedback",
        timestamp=time.time(),
        message="Generating feedback...",
    )

    await manager.send_agent_thinking(
        session_id=request.session_id,
        agent="feedback",
        timestamp=time.time(),
        thinking="Synthesizing evaluation results into actionable feedback and practice suggestions...",
    )

    # Generate feedback
    feedback = await _generate_feedback(evaluation, current_round.question, request.answer)
    current_round.feedback = feedback

    feedback_complete_time = time.time()
    await manager.send_agent_complete(
        session_id=request.session_id,
        agent="feedback",
        timestamp=feedback_complete_time,
        result={
            "summary_preview": feedback.summary[:200] + "...",
            "suggestions_count": len(feedback.practice_suggestions),
        },
        tokens_used=141,
        duration_ms=int((feedback_complete_time - scorer_complete_time) * 1000),
    )

    # Check if there's a next question
    has_next = session.current_round < session.total_rounds
    next_question = None

    if has_next:
        # Get next question
        next_q = get_interview_question(question_index=session.current_round)
        if next_q:
            next_question = next_q.question
            session.current_round += 1
            session.rounds.append(
                InterviewRound(
                    round_number=session.current_round,
                    question=next_q.question,
                    question_id=next_q.id,
                )
            )
        else:
            has_next = False

    session.status = InterviewStatus.IN_PROGRESS if has_next else InterviewStatus.COMPLETED
    session.updated_at = time.time()

    return SubmitAnswerResponse(
        session_id=request.session_id,
        status=session.status,
        evaluation=evaluation,
        feedback=feedback,
        has_next_question=has_next,
        next_question=next_question,
    )


@router.get("/session/{session_id}", response_model=InterviewSession)
async def get_session(session_id: str) -> InterviewSession:
    """Get the current state of an interview session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/session/{session_id}/complete", response_model=InterviewCompleteResponse)
async def complete_interview(session_id: str) -> InterviewCompleteResponse:
    """
    Get the complete interview summary when all rounds are done.
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Calculate overall metrics from trace
    trace_events = manager.get_session_trace(session_id)

    total_duration = 0
    total_tokens = 0
    agent_metrics: dict[str, dict[str, Any]] = {}

    for event in trace_events:
        total_tokens += event.get("tokens_used", 0)
        total_duration += event.get("duration_ms", 0)

        agent = event.get("agent", "unknown")
        if agent not in agent_metrics:
            agent_metrics[agent] = {
                "calls": 0,
                "tokens": 0,
                "duration_ms": 0,
            }
        agent_metrics[agent]["calls"] += 1
        agent_metrics[agent]["tokens"] += event.get("tokens_used", 0)
        agent_metrics[agent]["duration_ms"] += event.get("duration_ms", 0)

    # Extract tool calls
    tool_calls = [
        event["data"]
        for event in trace_events
        if event.get("event_type") == "tool_call"
    ]

    metrics = TraceMetrics(
        total_duration_ms=total_duration,
        total_tokens=total_tokens,
        agent_metrics=agent_metrics,
        tool_calls=tool_calls,
    )

    # Generate overall feedback
    overall_feedback = _generate_overall_feedback(session)

    await manager.send_interview_complete(
        session_id=session_id,
        timestamp=time.time(),
        summary={
            "rounds_completed": len(session.rounds),
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
        },
    )

    return InterviewCompleteResponse(
        session_id=session_id,
        status=session.status,
        rounds=session.rounds,
        overall_feedback=overall_feedback,
        trace_metrics=metrics,
    )


@router.get("/trace/{session_id}")
async def get_trace(session_id: str) -> list[dict[str, Any]]:
    """Get all trace events for a session."""
    return manager.get_session_trace(session_id)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time trace streaming.

    Connect to this endpoint to receive live updates about
    agent activities during the interview.
    """
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            # Could handle client commands here if needed
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)


# Helper functions for generating responses (in production, these call Claude Agent SDK)

async def _generate_evaluation(question: str, answer: str) -> EvaluationResponse:
    """
    Generate evaluation for an answer.

    In production, this would call the Scorer Agent via Claude Agent SDK.
    For demo, we return a structured response.
    """
    # Demo evaluation logic - in production, this comes from the LLM
    answer_length = len(answer.split())
    has_specific_examples = "example" in answer.lower() or "instance" in answer.lower()

    # Simple heuristic scoring for demo
    grammar_score = min(8.0, 6.0 + (answer_length / 50))
    content_score = 7.0 if has_specific_examples else 6.0
    fluency_score = min(7.5, 5.5 + (answer_length / 40))
    vocabulary_score = 7.0

    overall = round(
        grammar_score * 0.25 +
        content_score * 0.30 +
        fluency_score * 0.25 +
        vocabulary_score * 0.20,
        1
    )

    return EvaluationResponse(
        scores=ScoreBreakdown(
            grammar=grammar_score,
            content=content_score,
            fluency=fluency_score,
            vocabulary=vocabulary_score,
            overall=overall,
        ),
        highlights=[
            "Clear structure in response",
            "Good use of professional vocabulary" if vocabulary_score >= 7 else "Adequate vocabulary usage",
        ],
        issues=[
            "Consider adding more specific examples" if not has_specific_examples else "Good use of examples",
            "Watch for tense consistency in past experiences",
        ],
        grammar_errors=[
            {
                "error": "Tense inconsistency detected",
                "suggestion": "Use past tense consistently when describing past experiences",
            }
        ],
    )


async def _generate_feedback(
    evaluation: EvaluationResponse,
    question: str,
    answer: str,
) -> FeedbackResponse:
    """
    Generate feedback based on evaluation.

    In production, this would call the Feedback Agent via Claude Agent SDK.
    """
    scores = evaluation.scores
    star_rating = "⭐" * int(scores.overall)

    summary = f"""## 面试回答评估

**综合得分：{scores.overall} / 10** {star_rating}

### 🎉 做得好的地方
"""
    for i, highlight in enumerate(evaluation.highlights, 1):
        summary += f"{i}. **{highlight}**\n"

    summary += """
### 📈 可以提升的地方
"""
    for i, issue in enumerate(evaluation.issues, 1):
        summary += f"{i}. **{issue}**\n"

    if evaluation.grammar_errors:
        summary += """
### 🔧 语法改进建议
"""
        for error in evaluation.grammar_errors:
            summary += f"- ❌ {error.get('error', '')}\n"
            summary += f"- ✅ {error.get('suggestion', '')}\n"

    summary += f"""
### 📊 详细评分
| 维度 | 得分 |
|------|------|
| 语法 Grammar | {scores.grammar}/10 |
| 内容 Content | {scores.content}/10 |
| 流利度 Fluency | {scores.fluency}/10 |
| 词汇 Vocabulary | {scores.vocabulary}/10 |
"""

    return FeedbackResponse(
        summary=summary,
        practice_suggestions=[
            "录制一段1分钟的自我介绍，回放检查时态使用是否一致",
            "练习使用STAR方法组织回答结构",
        ],
        next_focus_areas=[
            "时态一致性",
            "添加具体例子支撑观点",
        ],
    )


def _generate_overall_feedback(session: InterviewSession) -> str:
    """Generate overall feedback for the complete interview."""
    total_score = 0
    count = 0

    for round_data in session.rounds:
        if round_data.evaluation:
            total_score += round_data.evaluation.scores.overall
            count += 1

    avg_score = total_score / count if count > 0 else 0

    return f"""## 面试总结报告

**候选人**: {session.candidate_name}
**完成轮次**: {len(session.rounds)}
**平均得分**: {avg_score:.1f}/10

### 整体表现
您完成了{len(session.rounds)}轮面试问答。整体表现{"良好" if avg_score >= 7 else "尚可" if avg_score >= 5 else "需要加强"}。

### 主要优势
- 能够理解并回应面试问题
- 展现了基本的英语沟通能力

### 改进建议
1. 继续练习时态的正确使用
2. 在回答中加入更多具体的例子
3. 减少填充词的使用，用自然停顿代替

### 推荐练习
1. 每天用英语录制2分钟的工作总结
2. 观看英语面试视频，学习优秀回答的结构
3. 找语伴进行模拟面试练习

祝您面试顺利！🎉
"""
