"""
Conversational Deal Analysis API for DealFlow AI Copilot.

Chat interface for follow-up questions about analyzed deals.
Maintains conversation context per session via database persistence.
"""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_client import get_gemini_client
from app.database import crud
from app.database.session import get_db
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["conversational-analysis"])

# Access shared analysis results for deal context
from app.api.deals import _analysis_results


class ChatMessageRequest(BaseModel):
    """Chat message from user."""
    message: str = Field(..., description="User's question or message")
    session_id: Optional[str] = Field(
        default=None, description="Session ID for conversation continuity"
    )
    analysis_id: Optional[str] = Field(
        default=None, description="Analysis ID to ask questions about"
    )


class ChatResponse(BaseModel):
    """Chat response from AI."""
    session_id: str
    response: str
    analysis_id: Optional[str] = None
    sources: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Chat About a Deal",
    description="""
Ask follow-up questions about an analyzed deal. The AI maintains
conversation context so you can drill into specific areas.

**Example questions:**
- "What's the implied LTV:CAC if churn improves by 2%?"
- "How does this company compare to Stripe at a similar stage?"
- "What are the top 3 risks I should focus on in diligence?"
- "Summarize the bull case in 3 bullet points"
""",
)
async def chat_about_deal(
    msg: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Chat with AI about an analyzed deal."""

    # Get or create session
    session_id = msg.session_id or str(uuid.uuid4())[:12]
    analysis_id = msg.analysis_id

    # If continuing existing session and no analysis_id provided, try to get from history
    if not analysis_id and msg.session_id:
        history = await crud.get_chat_history(db, session_id, limit=1)
        if history:
            analysis_id = history[0].analysis_id

    # Get deal context from in-memory results
    deal_context = ""
    if analysis_id and analysis_id in _analysis_results:
        memo = _analysis_results[analysis_id]
        deal_context = _build_deal_context(memo.model_dump())
    elif analysis_id:
        logger.warning(f"Analysis {analysis_id} not found for chat context")

    # Save user message to DB
    await crud.save_chat_message(
        db, session_id, "user", msg.message, analysis_id=analysis_id
    )

    # Get conversation history from DB
    db_messages = await crud.get_chat_history(db, session_id, limit=10)
    conversation_history = _build_conversation_history([
        {"role": m.role, "content": m.content} for m in db_messages
    ])

    prompt = f"""You are a senior private equity analyst assistant. You help investors
analyze deals, answer questions about companies, and provide investment insights.

{f"DEAL CONTEXT:{chr(10)}{deal_context}" if deal_context else "No specific deal loaded. Answer general PE/VC questions."}

CONVERSATION HISTORY:
{conversation_history}

USER QUESTION: {msg.message}

Provide a clear, concise, data-driven response. Reference specific numbers from the deal
when available. If you're unsure about something, say so. At the end, suggest 2-3
follow-up questions the user might want to ask.

Format your response as JSON:
{{
    "response": "Your detailed answer here",
    "sources": ["data points or sections you referenced"],
    "suggested_questions": ["question 1", "question 2", "question 3"]
}}"""

    try:
        client = get_gemini_client()
        result = await client.generate_structured(
            prompt=prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "response": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "suggested_questions": {"type": "array", "items": {"type": "string"}},
                },
            },
            model="pro",
            temperature=0.4,
        )

        response_text = result.get("response", "I couldn't generate a response.")
        sources = result.get("sources", [])
        suggestions = result.get("suggested_questions", [])

    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        response_text = f"I encountered an error generating a response: {str(e)}"
        sources = []
        suggestions = ["Can you rephrase your question?"]

    # Save assistant response to DB
    await crud.save_chat_message(
        db, session_id, "assistant", response_text, analysis_id=analysis_id
    )

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        analysis_id=analysis_id,
        sources=sources,
        suggested_questions=suggestions,
    )


@router.get(
    "/sessions",
    summary="List Chat Sessions",
    description="List all active chat sessions",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all active chat sessions."""
    sessions = await crud.list_chat_sessions(db)
    return {"total": len(sessions), "sessions": sessions}


@router.get(
    "/{session_id}/history",
    summary="Get Chat History",
    description="Get the conversation history for a session",
)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get chat history for a session."""
    messages = await crud.get_chat_history(db, session_id)
    if not messages:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return {
        "session_id": session_id,
        "analysis_id": messages[0].analysis_id if messages else None,
        "message_count": len(messages),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "created_at": messages[0].created_at.isoformat() if messages else None,
    }


@router.delete(
    "/{session_id}",
    summary="Delete Chat Session",
    description="Delete a chat session and its history",
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete a chat session."""
    count = await crud.delete_chat_session(db, session_id)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return {"message": f"Session {session_id} deleted ({count} messages removed)"}


def _build_deal_context(memo_data: dict) -> str:
    """Build a compact deal context string from memo data."""
    parts = []

    # Company info
    parts.append(f"Company: {memo_data.get('company_name', 'Unknown')}")

    # Executive summary
    exec_sum = memo_data.get("executive_summary", {})
    if exec_sum.get("company_overview"):
        parts.append(f"Overview: {exec_sum['company_overview']}")
    if exec_sum.get("recommendation"):
        parts.append(f"Recommendation: {exec_sum['recommendation']}")

    # Key financials
    extraction = memo_data.get("extraction_result", {})
    financials = extraction.get("financials", {})
    if financials:
        fin_parts = []
        if financials.get("revenue"):
            rev = financials["revenue"]
            fin_parts.append(f"Revenue: ${rev.get('amount', 0)}{rev.get('unit', '')}")
        if financials.get("revenue_growth_rate") is not None:
            fin_parts.append(f"Growth: {financials['revenue_growth_rate']:.0%}")
        if financials.get("gross_margin") is not None:
            fin_parts.append(f"Gross Margin: {financials['gross_margin']:.0%}")
        if financials.get("runway_months"):
            fin_parts.append(f"Runway: {financials['runway_months']}mo")
        if fin_parts:
            parts.append(f"Financials: {', '.join(fin_parts)}")

    # Unit economics
    ue = extraction.get("unit_economics", {})
    if ue:
        ue_parts = []
        if ue.get("ltv_cac_ratio"):
            ue_parts.append(f"LTV/CAC: {ue['ltv_cac_ratio']:.1f}x")
        if ue.get("churn_rate"):
            ue_parts.append(f"Churn: {ue['churn_rate']:.1%}")
        if ue.get("net_revenue_retention"):
            ue_parts.append(f"NRR: {ue['net_revenue_retention']:.0%}")
        if ue_parts:
            parts.append(f"Unit Economics: {', '.join(ue_parts)}")

    # Risk summary
    risk = memo_data.get("risk_result", {})
    if risk:
        parts.append(
            f"Risk Score: {risk.get('overall_risk_score', 0):.1f}/10, "
            f"Total Risks: {risk.get('total_risks', 0)}, "
            f"Critical: {risk.get('critical_risks', 0)}"
        )

    # Valuation
    val = memo_data.get("valuation_result", {})
    if val:
        low = val.get("valuation_range_low", {})
        mid = val.get("valuation_range_mid", {})
        high = val.get("valuation_range_high", {})
        parts.append(
            f"Valuation Range: ${low.get('amount', 0):.1f}M - "
            f"${mid.get('amount', 0):.1f}M - "
            f"${high.get('amount', 0):.1f}M"
        )

    return "\n".join(parts)


def _build_conversation_history(messages: list[dict]) -> str:
    """Build conversation history string."""
    history_parts = []
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        history_parts.append(f"{role}: {content}")
    return "\n".join(history_parts) if history_parts else "No previous conversation."
