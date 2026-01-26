"""
DealFlow AI Copilot - Simplified Streamlit Frontend

Clean, tabbed interface for multi-file deal analysis.
"""

import streamlit as st
import requests
import json
from typing import Any, Dict, Optional
from datetime import datetime

# Page config
st.set_page_config(
    page_title="DealFlow AI Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for clean styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #d4a853;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #94a3b8;
    }
    .metric-card {
        background: #1e293b;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #f8fafc;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
    }
    .score-high { color: #22c55e; }
    .score-medium { color: #f59e0b; }
    .score-low { color: #ef4444; }
    .recommendation-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.25rem;
    }
    .rec-strong-buy { background: #166534; color: #bbf7d0; }
    .rec-buy { background: #15803d; color: #dcfce7; }
    .rec-hold { background: #a16207; color: #fef3c7; }
    .rec-pass { background: #991b1b; color: #fecaca; }
    .risk-critical { border-left: 4px solid #ef4444; }
    .risk-high { border-left: 4px solid #f97316; }
    .risk-medium { border-left: 4px solid #f59e0b; }
    .risk-low { border-left: 4px solid #22c55e; }
    .methodology-box {
        background: #1e293b;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #d4a853;
        margin-bottom: 1rem;
    }
    .methodology-box h4 {
        color: #d4a853;
        margin-bottom: 0.5rem;
    }
    .methodology-box p {
        color: #94a3b8;
        font-size: 0.875rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"


def analyze_files(files: list, company_name: Optional[str] = None) -> Dict[str, Any]:
    """Call the simplified analysis API."""
    url = f"{API_BASE_URL}/api/v2/analyze/"

    # Prepare multipart form data
    files_data = []
    for file in files:
        files_data.append(("files", (file.name, file.getvalue(), file.type)))

    data = {}
    if company_name:
        data["company_name"] = company_name

    response = requests.post(url, files=files_data, data=data, timeout=300)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>📊 DealFlow AI Copilot</h1>
        <p>Upload your pitch deck and supporting documents for AI-powered analysis</p>
    </div>
    """, unsafe_allow_html=True)


def render_upload_section():
    """Render the file upload section."""
    st.markdown("### 📁 Upload Documents")

    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_files = st.file_uploader(
            "Drop files here or click to browse",
            type=["pdf", "docx", "xlsx"],
            accept_multiple_files=True,
            help="Supported formats: PDF (pitch decks), DOCX (memos), XLSX (financials)"
        )

    with col2:
        company_name = st.text_input(
            "Company Name (optional)",
            placeholder="e.g., TechCo Inc.",
            help="Helps improve extraction accuracy"
        )

    if uploaded_files:
        st.info(f"📎 {len(uploaded_files)} file(s) selected: {', '.join([f.name for f in uploaded_files])}")

    return uploaded_files, company_name


def render_summary_tab(summary: Dict):
    """Render the Summary tab."""
    st.markdown(f"## {summary['company_name']}")
    st.markdown(f"*{summary['headline']}*")

    # Recommendation badge
    rec = summary['recommendation'].lower().replace(" ", "-")
    rec_class = f"rec-{rec.replace('_', '-')}"
    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        <span class="recommendation-badge {rec_class}">{summary['recommendation']}</span>
        <span style="margin-left: 1rem; color: #94a3b8;">Conviction: {summary['conviction']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    st.markdown("### Key Metrics")
    metrics = summary.get('key_metrics', {})
    if metrics:
        cols = st.columns(min(len(metrics), 5))
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % len(cols)]:
                st.metric(label, value)

    # Scores
    col1, col2 = st.columns(2)
    with col1:
        score = summary['analysis_score']
        score_class = "score-high" if score >= 7 else "score-medium" if score >= 5 else "score-low"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {score_class}">{score:.1f}/10</div>
            <div class="metric-label">Analysis Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        risk = summary['risk_score']
        # For risk, lower is better
        risk_class = "score-high" if risk <= 4 else "score-medium" if risk <= 6 else "score-low"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {risk_class}">{risk:.1f}/10</div>
            <div class="metric-label">Risk Score (lower is better)</div>
        </div>
        """, unsafe_allow_html=True)

    # Valuation
    st.markdown("### Valuation")
    st.markdown(f"**Our Estimate:** {summary['valuation_range']}")
    if summary.get('valuation_vs_ask'):
        st.markdown(f"**vs Company Ask:** {summary['valuation_vs_ask']}")

    # Two columns: Reasons to invest & Key concerns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Reasons to Invest")
        for reason in summary.get('reasons_to_invest', []):
            st.markdown(f"- {reason}")

    with col2:
        st.markdown("### ⚠️ Key Concerns")
        for concern in summary.get('key_concerns', []):
            st.markdown(f"- {concern}")

    # Due diligence
    if summary.get('diligence_priorities'):
        st.markdown("### 📋 Due Diligence Priorities")
        for item in summary['diligence_priorities']:
            st.markdown(f"- {item}")


def render_extraction_tab(extraction: Dict):
    """Render the Extraction tab."""
    # Methodology explanation
    st.markdown("""
    <div class="methodology-box">
        <h4>🔍 How Extraction Works</h4>
        <p>{}</p>
    </div>
    """.format(extraction.get('methodology', '')), unsafe_allow_html=True)

    # Company basics
    st.markdown("### Company Overview")
    company = extraction.get('company', {})
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Company:** {company.get('name', 'N/A')}")
        st.markdown(f"**Industry:** {company.get('industry', 'N/A')}")
        st.markdown(f"**Stage:** {company.get('stage', 'N/A')}")

    with col2:
        st.markdown(f"**Business Model:** {company.get('business_model', 'N/A')}")
        st.markdown(f"**Founded:** {company.get('founded_year', 'N/A')}")
        st.markdown(f"**Location:** {company.get('headquarters', 'N/A')}")

    # Financials
    st.markdown("### Financial Metrics")
    fin = extraction.get('financials', {})

    col1, col2, col3 = st.columns(3)
    with col1:
        if fin.get('revenue_arr'):
            st.metric("ARR", f"${fin['revenue_arr']}M")
        if fin.get('burn_rate'):
            st.metric("Monthly Burn", f"${fin['burn_rate']}M")

    with col2:
        if fin.get('growth_rate'):
            st.metric("Growth Rate", f"{fin['growth_rate']}%")
        if fin.get('runway_months'):
            st.metric("Runway", f"{fin['runway_months']} months")

    with col3:
        if fin.get('gross_margin'):
            st.metric("Gross Margin", f"{fin['gross_margin']}%")
        if fin.get('valuation_ask'):
            st.metric("Valuation Ask", f"${fin['valuation_ask']}M")

    # Team
    st.markdown("### Team")
    team = extraction.get('team', [])
    if team:
        for member in team:
            st.markdown(f"- **{member.get('name', 'Unknown')}** - {member.get('role', 'Founder')}")
    if extraction.get('team_size'):
        st.markdown(f"*Total team size: {extraction['team_size']} employees*")

    # Data gaps
    gaps = extraction.get('data_gaps', [])
    if gaps:
        st.warning(f"**Data Gaps:** {', '.join(gaps)}")

    st.info(f"Documents processed: {extraction.get('documents_processed', 0)}")


def render_analysis_tab(analysis: Dict):
    """Render the Analysis tab."""
    # Methodology
    st.markdown("""
    <div class="methodology-box">
        <h4>📊 How Analysis Works</h4>
        <p>{}</p>
    </div>
    """.format(analysis.get('methodology', '')), unsafe_allow_html=True)

    st.markdown(f"### Overall Score: {analysis.get('overall_score', 0):.1f}/10")

    # Score cards
    scores = [
        ('business_model_score', 'Business Model'),
        ('market_score', 'Market'),
        ('competitive_score', 'Competitive Position'),
        ('growth_score', 'Growth'),
    ]

    for score_key, label in scores:
        score_data = analysis.get(score_key, {})
        score = score_data.get('score', 5) if isinstance(score_data, dict) else score_data
        reasoning = score_data.get('reasoning', '') if isinstance(score_data, dict) else ''

        score_class = "score-high" if score >= 7 else "score-medium" if score >= 5 else "score-low"

        st.markdown(f"""
        **{label}:** <span class="{score_class}">{score:.1f}/10</span>

        *{reasoning}*
        """, unsafe_allow_html=True)
        st.markdown("---")

    # SWOT
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💪 Strengths")
        for s in analysis.get('strengths', []):
            st.markdown(f"- {s}")

        st.markdown("### 🚀 Opportunities")
        for o in analysis.get('opportunities', []):
            st.markdown(f"- {o}")

    with col2:
        st.markdown("### 😟 Weaknesses")
        for w in analysis.get('weaknesses', []):
            st.markdown(f"- {w}")

        st.markdown("### ⚡ Threats")
        for t in analysis.get('threats', []):
            st.markdown(f"- {t}")


def render_risks_tab(risks: Dict):
    """Render the Risks tab."""
    # Methodology
    st.markdown("""
    <div class="methodology-box">
        <h4>⚠️ How Risk Assessment Works</h4>
        <p>{}</p>
    </div>
    """.format(risks.get('methodology', '')), unsafe_allow_html=True)

    # Risk summary
    st.markdown(f"### Overall Risk Score: {risks.get('overall_risk_score', 5):.1f}/10")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Critical", risks.get('critical_count', 0), delta_color="inverse")
    with col2:
        st.metric("High", risks.get('high_count', 0), delta_color="inverse")
    with col3:
        st.metric("Medium", risks.get('medium_count', 0), delta_color="off")
    with col4:
        st.metric("Low", risks.get('low_count', 0), delta_color="normal")

    # Deal breakers
    deal_breakers = risks.get('deal_breakers', [])
    if deal_breakers:
        st.error("**🚫 Deal Breakers:**")
        for db in deal_breakers:
            st.markdown(f"- {db}")

    # Individual risks
    st.markdown("### Identified Risks")

    for risk in risks.get('risks', []):
        severity = risk.get('severity', 'medium')
        risk_class = f"risk-{severity}"

        st.markdown(f"""
        <div style="background: #1e293b; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;" class="{risk_class}">
            <strong>{risk.get('title', 'Risk')}</strong>
            <span style="float: right; color: #94a3b8;">{severity.upper()} | {risk.get('category', 'general')}</span>
            <p style="margin: 0.5rem 0 0 0; color: #94a3b8;">{risk.get('description', '')}</p>
            {f"<p style='margin: 0.5rem 0 0 0; color: #22c55e;'><strong>Mitigation:</strong> {risk.get('mitigation', '')}</p>" if risk.get('mitigation') else ''}
        </div>
        """, unsafe_allow_html=True)

    # Must verify
    must_verify = risks.get('must_verify', [])
    if must_verify:
        st.markdown("### 🔍 Must Verify in Due Diligence")
        for item in must_verify:
            st.checkbox(item, key=f"verify_{item[:20]}")


def render_valuation_tab(valuation: Dict):
    """Render the Valuation tab."""
    # Methodology
    st.markdown("""
    <div class="methodology-box">
        <h4>💰 How Valuation Works</h4>
        <p>{}</p>
    </div>
    """.format(valuation.get('methodology', '')), unsafe_allow_html=True)

    # Final valuation range
    st.markdown("### Valuation Range")

    low = valuation.get('valuation_low', 0)
    mid = valuation.get('valuation_mid', 0)
    high = valuation.get('valuation_high', 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Low", f"${low:.0f}M")
    with col2:
        st.metric("Base Case", f"${mid:.0f}M", delta=None)
    with col3:
        st.metric("High", f"${high:.0f}M")

    # Comparison to ask
    ask = valuation.get('company_ask')
    if ask:
        st.markdown(f"**Company's Ask:** ${ask:.0f}M")
        verdict = valuation.get('ask_vs_our_value', 'N/A')
        premium = valuation.get('premium_discount_pct')

        if verdict == "Attractive":
            st.success(f"✅ Ask is **ATTRACTIVE** ({abs(premium):.0f}% below our estimate)")
        elif verdict == "Expensive":
            st.error(f"⚠️ Ask is **EXPENSIVE** ({premium:.0f}% premium to our estimate)")
        else:
            st.info(f"➡️ Ask appears **FAIR**")

    # Individual methods
    st.markdown("### Valuation Methods")

    for method in valuation.get('methods', []):
        with st.expander(f"{method['method_name']}: ${method['value_mid']:.0f}M"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Low:** ${method['value_low']:.0f}M")
            with col2:
                st.markdown(f"**Mid:** ${method['value_mid']:.0f}M")
            with col3:
                st.markdown(f"**High:** ${method['value_high']:.0f}M")

            st.markdown("**Key Assumptions:**")
            for assumption in method.get('key_assumptions', []):
                st.markdown(f"- {assumption}")


def render_results(data: Dict):
    """Render the full results in tabs."""
    # Tabs for each section
    tabs = st.tabs([
        "📋 Summary",
        "🔍 Extraction",
        "📊 Analysis",
        "⚠️ Risks",
        "💰 Valuation",
        "📄 Raw JSON"
    ])

    with tabs[0]:
        render_summary_tab(data.get('summary', {}))

    with tabs[1]:
        render_extraction_tab(data.get('extraction', {}))

    with tabs[2]:
        render_analysis_tab(data.get('analysis', {}))

    with tabs[3]:
        render_risks_tab(data.get('risks', {}))

    with tabs[4]:
        render_valuation_tab(data.get('valuation', {}))

    with tabs[5]:
        st.json(data)


def main():
    """Main application."""
    render_header()

    # Check if we have results in session state
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    if st.session_state.analysis_results:
        # Show results
        render_results(st.session_state.analysis_results)

        # Reset button
        if st.button("🔄 Start New Analysis", type="secondary"):
            st.session_state.analysis_results = None
            st.rerun()

    else:
        # Show upload interface
        uploaded_files, company_name = render_upload_section()

        if uploaded_files:
            if st.button("🚀 Analyze Deal", type="primary", use_container_width=True):
                with st.spinner("Analyzing documents... This may take 30-60 seconds."):
                    try:
                        results = analyze_files(uploaded_files, company_name)
                        st.session_state.analysis_results = results
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    main()
