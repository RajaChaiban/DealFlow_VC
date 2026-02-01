"""
Database seed script for DealFlow AI Copilot.

Populates the database with realistic sample data for development and demos:
- 2 users (analyst + partner)
- 8 deal analyses spanning different stages, scores, and industries
- Pipeline entries with stage history
- Chat sessions

Usage:
    python -m scripts.seed_data
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database.models import (
    Base,
    ChatMessage,
    DealAnalysis,
    DealPipelineEntry,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Sample Users
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "analyst@dealflow.ai",
        "password": "DealFlow2024!",
        "full_name": "Sarah Chen",
        "organization": "Horizon Ventures",
        "role": "analyst",
    },
    {
        "email": "partner@dealflow.ai",
        "password": "DealFlow2024!",
        "full_name": "Michael Torres",
        "organization": "Horizon Ventures",
        "role": "partner",
    },
]

# ---------------------------------------------------------------------------
# Sample Deals
# ---------------------------------------------------------------------------

DEALS = [
    {
        "analysis_id": "DEAL-001",
        "company_name": "TechVenture AI",
        "industry": "Enterprise Software",
        "stage": "series_a",
        "status": "completed",
        "recommendation": "Strong Buy",
        "conviction_level": "high",
        "overall_attractiveness_score": 8.2,
        "overall_risk_score": 3.5,
        "valuation_low": 45.0,
        "valuation_mid": 62.0,
        "valuation_high": 85.0,
        "processing_time_seconds": 47.3,
        "description": "AI-powered sales intelligence platform automating B2B research.",
        "pipeline_stage": "ic_review",
        "priority": "high",
        "tags": ["AI/ML", "SaaS", "Enterprise"],
        "assigned_to": "Sarah Chen",
    },
    {
        "analysis_id": "DEAL-002",
        "company_name": "GreenGrid Energy",
        "industry": "CleanTech",
        "stage": "series_b",
        "status": "completed",
        "recommendation": "Buy",
        "conviction_level": "medium",
        "overall_attractiveness_score": 7.1,
        "overall_risk_score": 4.8,
        "valuation_low": 120.0,
        "valuation_mid": 165.0,
        "valuation_high": 210.0,
        "processing_time_seconds": 52.1,
        "description": "Smart grid optimization for renewable energy providers.",
        "pipeline_stage": "diligence",
        "priority": "high",
        "tags": ["CleanTech", "Energy", "B2B"],
        "assigned_to": "Michael Torres",
    },
    {
        "analysis_id": "DEAL-003",
        "company_name": "MedAssist Pro",
        "industry": "HealthTech",
        "stage": "series_a",
        "status": "completed",
        "recommendation": "Buy",
        "conviction_level": "high",
        "overall_attractiveness_score": 7.8,
        "overall_risk_score": 4.2,
        "valuation_low": 30.0,
        "valuation_mid": 48.0,
        "valuation_high": 65.0,
        "processing_time_seconds": 39.8,
        "description": "AI clinical decision support for primary care physicians.",
        "pipeline_stage": "screening",
        "priority": "medium",
        "tags": ["HealthTech", "AI/ML", "SaaS"],
        "assigned_to": "Sarah Chen",
    },
    {
        "analysis_id": "DEAL-004",
        "company_name": "FinLedger",
        "industry": "FinTech",
        "stage": "seed",
        "status": "completed",
        "recommendation": "Pass",
        "conviction_level": "low",
        "overall_attractiveness_score": 4.5,
        "overall_risk_score": 7.2,
        "valuation_low": 8.0,
        "valuation_mid": 12.0,
        "valuation_high": 18.0,
        "processing_time_seconds": 35.6,
        "description": "Blockchain-based accounting ledger for SMBs.",
        "pipeline_stage": "passed",
        "priority": "low",
        "tags": ["FinTech", "Blockchain"],
        "assigned_to": None,
    },
    {
        "analysis_id": "DEAL-005",
        "company_name": "DataMesh Labs",
        "industry": "Data Infrastructure",
        "stage": "series_a",
        "status": "completed",
        "recommendation": "Strong Buy",
        "conviction_level": "high",
        "overall_attractiveness_score": 8.6,
        "overall_risk_score": 3.1,
        "valuation_low": 55.0,
        "valuation_mid": 78.0,
        "valuation_high": 105.0,
        "processing_time_seconds": 44.2,
        "description": "Unified data mesh platform for enterprise analytics.",
        "pipeline_stage": "term_sheet",
        "priority": "urgent",
        "tags": ["Data", "Infrastructure", "Enterprise"],
        "assigned_to": "Michael Torres",
    },
    {
        "analysis_id": "DEAL-006",
        "company_name": "EduPath",
        "industry": "EdTech",
        "stage": "pre_seed",
        "status": "completed",
        "recommendation": "Hold",
        "conviction_level": "medium",
        "overall_attractiveness_score": 5.9,
        "overall_risk_score": 5.5,
        "valuation_low": 3.0,
        "valuation_mid": 5.0,
        "valuation_high": 8.0,
        "processing_time_seconds": 31.4,
        "description": "Personalized learning pathways powered by adaptive AI.",
        "pipeline_stage": "new",
        "priority": "low",
        "tags": ["EdTech", "AI/ML", "Consumer"],
        "assigned_to": None,
    },
    {
        "analysis_id": "DEAL-007",
        "company_name": "CloudSecure",
        "industry": "Cybersecurity",
        "stage": "series_b",
        "status": "completed",
        "recommendation": "Buy",
        "conviction_level": "high",
        "overall_attractiveness_score": 7.5,
        "overall_risk_score": 3.9,
        "valuation_low": 95.0,
        "valuation_mid": 140.0,
        "valuation_high": 185.0,
        "processing_time_seconds": 48.7,
        "description": "Zero-trust cloud security platform for multi-cloud enterprises.",
        "pipeline_stage": "diligence",
        "priority": "high",
        "tags": ["Cybersecurity", "Cloud", "Enterprise"],
        "assigned_to": "Sarah Chen",
    },
    {
        "analysis_id": "DEAL-008",
        "company_name": "SupplyAI",
        "industry": "Supply Chain",
        "stage": "series_a",
        "status": "completed",
        "recommendation": "Hold",
        "conviction_level": "medium",
        "overall_attractiveness_score": 6.3,
        "overall_risk_score": 5.1,
        "valuation_low": 20.0,
        "valuation_mid": 32.0,
        "valuation_high": 45.0,
        "processing_time_seconds": 41.0,
        "description": "AI demand forecasting and inventory optimization for retailers.",
        "pipeline_stage": "screening",
        "priority": "medium",
        "tags": ["Supply Chain", "AI/ML", "Retail"],
        "assigned_to": "Michael Torres",
    },
]

# ---------------------------------------------------------------------------
# Seed Functions
# ---------------------------------------------------------------------------


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """Create sample users. Returns dict keyed by email."""
    users = {}
    for u in USERS:
        user = User(
            email=u["email"],
            hashed_password=pwd_context.hash(u["password"]),
            full_name=u["full_name"],
            organization=u["organization"],
            role=u["role"],
        )
        session.add(user)
        users[u["email"]] = user
    await session.flush()
    print(f"  Created {len(users)} users")
    return users


async def seed_analyses(session: AsyncSession) -> list[DealAnalysis]:
    """Create sample deal analyses."""
    analyses = []
    base_date = datetime.utcnow() - timedelta(days=30)

    for i, deal in enumerate(DEALS):
        created = base_date + timedelta(days=i * 3, hours=i * 2)
        completed = created + timedelta(seconds=deal["processing_time_seconds"])

        analysis = DealAnalysis(
            analysis_id=deal["analysis_id"],
            company_name=deal["company_name"],
            industry=deal["industry"],
            stage=deal["stage"],
            status=deal["status"],
            description=deal["description"],
            recommendation=deal["recommendation"],
            conviction_level=deal["conviction_level"],
            overall_attractiveness_score=deal["overall_attractiveness_score"],
            overall_risk_score=deal["overall_risk_score"],
            valuation_low=deal["valuation_low"],
            valuation_mid=deal["valuation_mid"],
            valuation_high=deal["valuation_high"],
            processing_time_seconds=deal["processing_time_seconds"],
            created_at=created,
            completed_at=completed,
            full_ic_memo={
                "summary": {
                    "recommendation": deal["recommendation"],
                    "conviction": deal["conviction_level"],
                    "analysis_score": deal["overall_attractiveness_score"],
                    "risk_score": deal["overall_risk_score"],
                },
                "valuation": {
                    "valuation_low": deal["valuation_low"],
                    "valuation_mid": deal["valuation_mid"],
                    "valuation_high": deal["valuation_high"],
                },
            },
        )
        session.add(analysis)
        analyses.append(analysis)

    await session.flush()
    print(f"  Created {len(analyses)} deal analyses")
    return analyses


async def seed_pipeline(session: AsyncSession) -> list[DealPipelineEntry]:
    """Create pipeline entries with stage history."""
    entries = []
    stage_flow = {
        "new": ["new"],
        "screening": ["new", "screening"],
        "diligence": ["new", "screening", "diligence"],
        "ic_review": ["new", "screening", "diligence", "ic_review"],
        "term_sheet": ["new", "screening", "diligence", "ic_review", "term_sheet"],
        "passed": ["new", "screening", "passed"],
    }

    base_date = datetime.utcnow() - timedelta(days=25)

    for i, deal in enumerate(DEALS):
        stage = deal["pipeline_stage"]
        stages = stage_flow.get(stage, ["new", stage])
        entered = base_date + timedelta(days=i * 3)

        history = []
        for j, s in enumerate(stages):
            t = entered + timedelta(days=j * 2)
            entry_dict = {"stage": s, "entered_at": t.isoformat()}
            if j < len(stages) - 1:
                entry_dict["exited_at"] = (t + timedelta(days=2)).isoformat()
            history.append(entry_dict)

        entry = DealPipelineEntry(
            analysis_id=deal["analysis_id"],
            company_name=deal["company_name"],
            stage=stage,
            priority=deal["priority"],
            assigned_to=deal.get("assigned_to"),
            tags=deal.get("tags", []),
            notes=f"Seed data for {deal['company_name']}",
            stage_history=history,
            stage_entered_at=entered + timedelta(days=(len(stages) - 1) * 2),
            created_at=entered,
        )
        session.add(entry)
        entries.append(entry)

    await session.flush()
    print(f"  Created {len(entries)} pipeline entries")
    return entries


async def seed_chat(session: AsyncSession) -> None:
    """Create sample chat sessions."""
    sessions_data = [
        {
            "session_id": "chat-001",
            "analysis_id": "DEAL-001",
            "messages": [
                ("user", "What are the key strengths of TechVenture AI?"),
                (
                    "assistant",
                    "TechVenture AI has several notable strengths:\n\n"
                    "1. **Strong revenue growth** at 180% YoY with $3.2M ARR\n"
                    "2. **Excellent unit economics** with 9x LTV:CAC ratio\n"
                    "3. **Experienced founding team** with Google/Stripe pedigree\n"
                    "4. **Large addressable market** ($50B TAM) with strong tailwinds",
                ),
                ("user", "What about the risks?"),
                (
                    "assistant",
                    "Key risk areas to monitor:\n\n"
                    "1. **Customer concentration** — top 3 customers are 40% of revenue\n"
                    "2. **No CFO** — financial leadership gap as they scale\n"
                    "3. **Competitive pressure** from well-funded incumbents like Gong\n"
                    "4. **Enterprise sales cycles** can be 6-9 months, impacting cash flow",
                ),
            ],
        },
        {
            "session_id": "chat-002",
            "analysis_id": "DEAL-005",
            "messages": [
                ("user", "How does DataMesh Labs compare to Databricks?"),
                (
                    "assistant",
                    "DataMesh Labs differs from Databricks in several ways:\n\n"
                    "- **Architecture**: Data mesh (decentralized) vs. lakehouse (centralized)\n"
                    "- **Target**: Mid-market enterprises vs. Databricks' large enterprise focus\n"
                    "- **Pricing**: Usage-based at ~60% lower cost point\n"
                    "- **Moat**: Domain-specific connectors vs. Databricks' compute optimization\n\n"
                    "At $78M valuation, DataMesh is significantly cheaper than Databricks' "
                    "last round ($43B), making it an attractive entry point.",
                ),
            ],
        },
    ]

    count = 0
    base_time = datetime.utcnow() - timedelta(days=5)
    for sess in sessions_data:
        for j, (role, content) in enumerate(sess["messages"]):
            msg = ChatMessage(
                session_id=sess["session_id"],
                analysis_id=sess["analysis_id"],
                role=role,
                content=content,
                created_at=base_time + timedelta(minutes=j * 2),
            )
            session.add(msg)
            count += 1

    await session.flush()
    print(f"  Created {count} chat messages across {len(sessions_data)} sessions")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the seed script."""
    print("DealFlow AI Copilot — Database Seed Script")
    print("=" * 50)

    engine = create_async_engine(settings.database_url, echo=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ready.\n")

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        try:
            print("Seeding users...")
            await seed_users(session)

            print("Seeding deal analyses...")
            await seed_analyses(session)

            print("Seeding pipeline...")
            await seed_pipeline(session)

            print("Seeding chat sessions...")
            await seed_chat(session)

            await session.commit()
            print("\nSeed data committed successfully!")
            print("\nLogin credentials:")
            for u in USERS:
                print(f"  {u['role']:>8}: {u['email']} / {u['password']}")

        except Exception as e:
            await session.rollback()
            print(f"\nError seeding data: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
