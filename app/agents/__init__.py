"""
AI Agents for DealFlow AI Copilot.

Multi-agent system for private equity deal analysis:
- ExtractionAgent: Extract structured data from pitch decks
- AnalysisAgent: Deep business and market analysis
- RiskAgent: Comprehensive risk assessment
- ValuationAgent: Multi-methodology valuation
- OrchestratorAgent: Master coordinator

Example:
    ```python
    from app.agents import OrchestratorAgent

    orchestrator = OrchestratorAgent()
    result = await orchestrator.analyze(
        images=pdf_images,
        text_content=extracted_text
    )
    print(result.final_recommendation)
    ```
"""

from app.agents.analysis_agent import AnalysisAgent
from app.agents.base import AgentContext, BaseAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.risk_agent import RiskAgent
from app.agents.valuation_agent import ValuationAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "ExtractionAgent",
    "AnalysisAgent",
    "RiskAgent",
    "ValuationAgent",
    "OrchestratorAgent",
]
