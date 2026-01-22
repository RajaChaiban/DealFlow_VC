"""
Results Dashboard Component for DealFlow AI Copilot

Features:
- Executive Summary with recommendation badge
- Extracted company data (financials, team, market)
- Risk Assessment with severity color coding
- Valuation range visualization
- Full IC Memo display
- Download/Export options
"""

import streamlit as st
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import sys
from pathlib import Path

# Add frontend directory to path for imports
frontend_dir = Path(__file__).parent.parent
if str(frontend_dir) not in sys.path:
    sys.path.insert(0, str(frontend_dir))

from utils.styling import format_currency, format_percentage, get_theme_colors


def get_recommendation_class(recommendation: str) -> str:
    """Get CSS class for recommendation badge."""
    recommendation_lower = recommendation.lower().strip()
    if "strong" in recommendation_lower and "buy" in recommendation_lower:
        return "strong-buy"
    elif "buy" in recommendation_lower or "invest" in recommendation_lower:
        return "buy"
    elif "hold" in recommendation_lower or "monitor" in recommendation_lower:
        return "hold"
    elif "pass" in recommendation_lower or "decline" in recommendation_lower or "no" in recommendation_lower:
        return "pass"
    return "hold"


def get_risk_class(severity: str) -> str:
    """Get CSS class for risk severity."""
    severity_lower = severity.lower().strip()
    if severity_lower == "critical":
        return "critical"
    elif severity_lower == "high":
        return "high"
    elif severity_lower == "medium":
        return "medium"
    elif severity_lower == "low":
        return "low"
    return "medium"


def render_executive_summary(data: Dict[str, Any]) -> None:
    """
    Render the executive summary section.

    Args:
        data: Analysis results data
    """
    # Extract executive summary data
    exec_summary = data.get("executive_summary", {})
    if isinstance(exec_summary, str):
        exec_summary = {"summary": exec_summary}

    recommendation = exec_summary.get("recommendation", data.get("recommendation", "Under Review"))
    summary_text = exec_summary.get("summary", exec_summary.get("overview", ""))
    key_highlights = exec_summary.get("key_highlights", exec_summary.get("highlights", []))
    confidence_score = exec_summary.get("confidence_score", data.get("confidence_score"))

    rec_class = get_recommendation_class(recommendation)

    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Executive Summary</h3>
        </div>
    """, unsafe_allow_html=True)

    # Recommendation badge
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div class="recommendation-badge {rec_class}">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            {recommendation.upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Summary text
    if summary_text:
        st.markdown(f"""
        <div style="color: #e2e8f0; line-height: 1.8; margin-bottom: 1.5rem; font-size: 1rem;">
            {summary_text}
        </div>
        """, unsafe_allow_html=True)

    # Key highlights
    if key_highlights:
        st.markdown("<h4 style='color: #d4a853; margin-bottom: 0.75rem;'>Key Highlights</h4>", unsafe_allow_html=True)
        highlights_html = "<ul style='margin: 0; padding-left: 1.5rem;'>"
        for highlight in key_highlights[:5]:  # Limit to 5 highlights
            highlights_html += f"<li style='color: #94a3b8; margin-bottom: 0.5rem; line-height: 1.5;'>{highlight}</li>"
        highlights_html += "</ul>"
        st.markdown(highlights_html, unsafe_allow_html=True)

    # Confidence score if available
    if confidence_score is not None:
        score_pct = confidence_score * 100 if confidence_score <= 1 else confidence_score
        st.markdown(f"""
        <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="color: #94a3b8; font-size: 0.875rem;">Confidence Score</span>
                <span style="color: #d4a853; font-weight: 600;">{score_pct:.0f}%</span>
            </div>
            <div style="background: #1a2744; border-radius: 8px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #22c55e, #d4a853); height: 100%; width: {score_pct}%; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_company_data(data: Dict[str, Any]) -> None:
    """
    Render extracted company data section.

    Args:
        data: Analysis results data
    """
    company_data = data.get("company_data", data.get("extracted_data", {}))
    if isinstance(company_data, str):
        company_data = {"description": company_data}

    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Company Overview</h3>
        </div>
    """, unsafe_allow_html=True)

    # Create tabs for different data sections
    tabs = st.tabs(["Overview", "Financials", "Team", "Market"])

    with tabs[0]:  # Overview
        overview = company_data.get("overview", company_data.get("company_overview", {}))
        if isinstance(overview, str):
            st.markdown(f"<p style='color: #94a3b8;'>{overview}</p>", unsafe_allow_html=True)
        else:
            company_name = overview.get("name", company_data.get("name", "N/A"))
            industry = overview.get("industry", company_data.get("industry", "N/A"))
            stage = overview.get("stage", company_data.get("stage", "N/A"))
            founded = overview.get("founded", company_data.get("founded_year", "N/A"))
            location = overview.get("location", company_data.get("headquarters", "N/A"))
            description = overview.get("description", company_data.get("description", ""))

            col1, col2 = st.columns(2)
            with col1:
                render_metric_card("Company", str(company_name))
                render_metric_card("Industry", str(industry))
                render_metric_card("Stage", str(stage))
            with col2:
                render_metric_card("Founded", str(founded))
                render_metric_card("Location", str(location))

            if description:
                st.markdown(f"""
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(26, 39, 68, 0.5); border-radius: 8px;">
                    <p style="color: #94a3b8; margin: 0; line-height: 1.6;">{description}</p>
                </div>
                """, unsafe_allow_html=True)

    with tabs[1]:  # Financials
        financials = company_data.get("financials", company_data.get("financial_data", {}))
        if isinstance(financials, str):
            st.markdown(f"<p style='color: #94a3b8;'>{financials}</p>", unsafe_allow_html=True)
        elif financials:
            col1, col2, col3 = st.columns(3)

            revenue = financials.get("revenue", financials.get("arr", financials.get("annual_revenue")))
            growth = financials.get("growth_rate", financials.get("revenue_growth"))
            burn_rate = financials.get("burn_rate", financials.get("monthly_burn"))
            runway = financials.get("runway", financials.get("runway_months"))
            gross_margin = financials.get("gross_margin")
            ltv = financials.get("ltv", financials.get("customer_ltv"))

            with col1:
                if revenue:
                    render_metric_card("Revenue/ARR", format_currency(float(revenue)) if isinstance(revenue, (int, float)) else str(revenue))
                if burn_rate:
                    render_metric_card("Monthly Burn", format_currency(float(burn_rate)) if isinstance(burn_rate, (int, float)) else str(burn_rate))

            with col2:
                if growth:
                    render_metric_card("Growth Rate", format_percentage(float(growth)) if isinstance(growth, (int, float)) and growth <= 10 else f"{growth}%")
                if runway:
                    render_metric_card("Runway", f"{runway} months" if isinstance(runway, (int, float)) else str(runway))

            with col3:
                if gross_margin:
                    render_metric_card("Gross Margin", format_percentage(float(gross_margin)) if isinstance(gross_margin, (int, float)) and gross_margin <= 1 else f"{gross_margin}%")
                if ltv:
                    render_metric_card("Customer LTV", format_currency(float(ltv)) if isinstance(ltv, (int, float)) else str(ltv))

            # Additional metrics table
            other_metrics = {k: v for k, v in financials.items()
                          if k not in ["revenue", "arr", "annual_revenue", "growth_rate", "revenue_growth",
                                      "burn_rate", "monthly_burn", "runway", "runway_months", "gross_margin",
                                      "ltv", "customer_ltv"] and v is not None}
            if other_metrics:
                st.markdown("<h4 style='color: #d4a853; margin-top: 1.5rem;'>Additional Metrics</h4>", unsafe_allow_html=True)
                for key, value in other_metrics.items():
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #64748b;">{key.replace('_', ' ').title()}</span>
                        <span style="color: #f8fafc;">{value}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #64748b;'>No financial data available</p>", unsafe_allow_html=True)

    with tabs[2]:  # Team
        team = company_data.get("team", company_data.get("leadership_team", []))
        if isinstance(team, str):
            st.markdown(f"<p style='color: #94a3b8;'>{team}</p>", unsafe_allow_html=True)
        elif team:
            if isinstance(team, list):
                for member in team[:6]:  # Limit to 6 team members
                    if isinstance(member, dict):
                        name = member.get("name", "Unknown")
                        role = member.get("role", member.get("title", ""))
                        background = member.get("background", member.get("bio", ""))

                        st.markdown(f"""
                        <div style="padding: 1rem; background: rgba(26, 39, 68, 0.5); border-radius: 12px; margin-bottom: 0.75rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <span style="color: #f8fafc; font-weight: 600;">{name}</span>
                                <span style="color: #d4a853; font-size: 0.875rem;">{role}</span>
                            </div>
                            {"<p style='color: #94a3b8; font-size: 0.875rem; margin: 0;'>" + background + "</p>" if background else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color: #94a3b8;'>{member}</p>", unsafe_allow_html=True)
            elif isinstance(team, dict):
                for role, info in team.items():
                    st.markdown(f"""
                    <div style="padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #d4a853;">{role}:</span>
                        <span style="color: #f8fafc; margin-left: 0.5rem;">{info}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #64748b;'>No team data available</p>", unsafe_allow_html=True)

    with tabs[3]:  # Market
        market = company_data.get("market", company_data.get("market_analysis", {}))
        if isinstance(market, str):
            st.markdown(f"<p style='color: #94a3b8;'>{market}</p>", unsafe_allow_html=True)
        elif market:
            tam = market.get("tam", market.get("total_addressable_market"))
            sam = market.get("sam", market.get("serviceable_addressable_market"))
            som = market.get("som", market.get("serviceable_obtainable_market"))
            competitors = market.get("competitors", market.get("competition", []))
            trends = market.get("trends", market.get("market_trends", []))

            col1, col2, col3 = st.columns(3)
            with col1:
                if tam:
                    render_metric_card("TAM", format_currency(float(tam)) if isinstance(tam, (int, float)) else str(tam))
            with col2:
                if sam:
                    render_metric_card("SAM", format_currency(float(sam)) if isinstance(sam, (int, float)) else str(sam))
            with col3:
                if som:
                    render_metric_card("SOM", format_currency(float(som)) if isinstance(som, (int, float)) else str(som))

            if competitors:
                st.markdown("<h4 style='color: #d4a853; margin-top: 1.5rem;'>Key Competitors</h4>", unsafe_allow_html=True)
                if isinstance(competitors, list):
                    for comp in competitors[:5]:
                        st.markdown(f"<span class='status-badge info' style='margin: 0.25rem;'>{comp if isinstance(comp, str) else comp.get('name', str(comp))}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color: #94a3b8;'>{competitors}</p>", unsafe_allow_html=True)

            if trends:
                st.markdown("<h4 style='color: #d4a853; margin-top: 1.5rem;'>Market Trends</h4>", unsafe_allow_html=True)
                if isinstance(trends, list):
                    for trend in trends[:4]:
                        st.markdown(f"<li style='color: #94a3b8; margin-bottom: 0.25rem;'>{trend if isinstance(trend, str) else str(trend)}</li>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color: #94a3b8;'>{trends}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #64748b;'>No market data available</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_card(label: str, value: str) -> None:
    """Render a single metric card."""
    st.markdown(f"""
    <div class="metric-card" style="margin-bottom: 0.75rem;">
        <div class="metric-value" style="font-size: 1.25rem;">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_risk_assessment(data: Dict[str, Any]) -> None:
    """
    Render the risk assessment section.

    Args:
        data: Analysis results data
    """
    risks = data.get("risks", data.get("risk_assessment", data.get("risk_analysis", [])))

    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Risk Assessment</h3>
        </div>
    """, unsafe_allow_html=True)

    if isinstance(risks, str):
        st.markdown(f"<p style='color: #94a3b8;'>{risks}</p>", unsafe_allow_html=True)
    elif isinstance(risks, list) and risks:
        # Count risks by severity
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for risk in risks:
            if isinstance(risk, dict):
                severity = risk.get("severity", "medium").lower()
                risk_counts[severity] = risk_counts.get(severity, 0) + 1

        # Risk summary badges
        st.markdown("""
        <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
        """, unsafe_allow_html=True)

        if risk_counts["critical"] > 0:
            st.markdown(f'<span class="status-badge error">{risk_counts["critical"]} Critical</span>', unsafe_allow_html=True)
        if risk_counts["high"] > 0:
            st.markdown(f'<span class="status-badge warning" style="border-color: #f97316; color: #f97316;">{risk_counts["high"]} High</span>', unsafe_allow_html=True)
        if risk_counts["medium"] > 0:
            st.markdown(f'<span class="status-badge warning">{risk_counts["medium"]} Medium</span>', unsafe_allow_html=True)
        if risk_counts["low"] > 0:
            st.markdown(f'<span class="status-badge success">{risk_counts["low"]} Low</span>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Sort risks by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_risks = sorted(risks, key=lambda x: severity_order.get(x.get("severity", "medium").lower() if isinstance(x, dict) else "medium", 2))

        # Render individual risk cards
        for risk in sorted_risks:
            if isinstance(risk, dict):
                severity = risk.get("severity", "medium").lower()
                title = risk.get("title", risk.get("name", risk.get("risk", "Risk")))
                description = risk.get("description", risk.get("details", risk.get("impact", "")))
                mitigation = risk.get("mitigation", risk.get("mitigation_strategy", ""))
                risk_class = get_risk_class(severity)

                st.markdown(f"""
                <div class="risk-card {risk_class}">
                    <div class="risk-title">{title}</div>
                    <div class="risk-description">{description}</div>
                    {"<div style='margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.1);'><strong style='color: #d4a853;'>Mitigation:</strong> <span style='color: #94a3b8;'>" + mitigation + "</span></div>" if mitigation else ""}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="risk-card medium">
                    <div class="risk-description">{risk}</div>
                </div>
                """, unsafe_allow_html=True)
    elif isinstance(risks, dict):
        for category, items in risks.items():
            st.markdown(f"<h4 style='color: #d4a853; margin-top: 1rem;'>{category}</h4>", unsafe_allow_html=True)
            if isinstance(items, list):
                for item in items:
                    st.markdown(f"<li style='color: #94a3b8;'>{item}</li>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: #94a3b8;'>{items}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #64748b;'>No risks identified</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_valuation(data: Dict[str, Any]) -> None:
    """
    Render the valuation section.

    Args:
        data: Analysis results data
    """
    valuation = data.get("valuation", data.get("valuation_analysis", {}))

    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Valuation Analysis</h3>
        </div>
    """, unsafe_allow_html=True)

    if isinstance(valuation, str):
        st.markdown(f"<p style='color: #94a3b8;'>{valuation}</p>", unsafe_allow_html=True)
    elif valuation:
        # Extract valuation range
        low = valuation.get("low", valuation.get("min", valuation.get("valuation_low")))
        mid = valuation.get("mid", valuation.get("base", valuation.get("valuation_mid", valuation.get("estimated_value"))))
        high = valuation.get("high", valuation.get("max", valuation.get("valuation_high")))
        methodology = valuation.get("methodology", valuation.get("method", ""))
        comparables = valuation.get("comparables", valuation.get("comparable_companies", []))
        multiples = valuation.get("multiples", valuation.get("valuation_multiples", {}))

        # Display valuation range
        if low or mid or high:
            col1, col2, col3 = st.columns(3)
            with col1:
                if low:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Low Estimate</div>
                        <div class="metric-value" style="color: #22c55e;">{format_currency(float(low)) if isinstance(low, (int, float)) else low}</div>
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                if mid:
                    st.markdown(f"""
                    <div class="metric-card" style="border: 2px solid #d4a853;">
                        <div class="metric-label">Base Case</div>
                        <div class="metric-value">{format_currency(float(mid)) if isinstance(mid, (int, float)) else mid}</div>
                    </div>
                    """, unsafe_allow_html=True)
            with col3:
                if high:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">High Estimate</div>
                        <div class="metric-value" style="color: #f97316;">{format_currency(float(high)) if isinstance(high, (int, float)) else high}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Valuation range bar
            if low and high and isinstance(low, (int, float)) and isinstance(high, (int, float)):
                mid_val = mid if mid and isinstance(mid, (int, float)) else (low + high) / 2
                mid_pct = ((mid_val - low) / (high - low)) * 100 if high != low else 50

                st.markdown(f"""
                <div class="valuation-range" style="margin-top: 1.5rem;">
                    <div class="valuation-bar">
                        <div class="valuation-marker" style="left: {mid_pct}%;"></div>
                    </div>
                    <div class="valuation-labels">
                        <span class="valuation-label">{format_currency(float(low))}</span>
                        <span class="valuation-label" style="color: #d4a853;">Base: {format_currency(float(mid_val))}</span>
                        <span class="valuation-label">{format_currency(float(high))}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Methodology
        if methodology:
            st.markdown(f"""
            <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(26, 39, 68, 0.5); border-radius: 8px;">
                <h4 style="color: #d4a853; margin-bottom: 0.5rem;">Methodology</h4>
                <p style="color: #94a3b8; margin: 0;">{methodology}</p>
            </div>
            """, unsafe_allow_html=True)

        # Multiples
        if multiples and isinstance(multiples, dict):
            st.markdown("<h4 style='color: #d4a853; margin-top: 1.5rem;'>Valuation Multiples</h4>", unsafe_allow_html=True)
            cols = st.columns(min(len(multiples), 4))
            for i, (multiple_name, multiple_value) in enumerate(multiples.items()):
                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="font-size: 1.5rem;">{multiple_value}x</div>
                        <div class="metric-label">{multiple_name.replace('_', ' ')}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Comparables
        if comparables:
            st.markdown("<h4 style='color: #d4a853; margin-top: 1.5rem;'>Comparable Companies</h4>", unsafe_allow_html=True)
            if isinstance(comparables, list):
                comp_html = "<div style='display: flex; flex-wrap: wrap; gap: 0.5rem;'>"
                for comp in comparables[:6]:
                    comp_name = comp.get("name", comp) if isinstance(comp, dict) else comp
                    comp_html += f"<span class='status-badge info' style='margin: 0.25rem;'>{comp_name}</span>"
                comp_html += "</div>"
                st.markdown(comp_html, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #64748b;'>No valuation data available</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_ic_memo(data: Dict[str, Any]) -> None:
    """
    Render the full IC memo section.

    Args:
        data: Analysis results data
    """
    memo = data.get("ic_memo", data.get("memo", data.get("full_memo", "")))

    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Investment Committee Memo</h3>
        </div>
    """, unsafe_allow_html=True)

    if memo:
        with st.expander("View Full Memo", expanded=False):
            if isinstance(memo, str):
                st.markdown(f"""
                <div style="color: #e2e8f0; line-height: 1.8; white-space: pre-wrap;">
                    {memo}
                </div>
                """, unsafe_allow_html=True)
            elif isinstance(memo, dict):
                for section, content in memo.items():
                    st.markdown(f"<h4 style='color: #d4a853;'>{section.replace('_', ' ').title()}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #94a3b8; white-space: pre-wrap;'>{content}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #64748b;'>Full memo not available</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_export_options(data: Dict[str, Any]) -> None:
    """
    Render export/download options.

    Args:
        data: Analysis results data
    """
    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Export Options</h3>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # JSON export
    with col1:
        json_data = json.dumps(data, indent=2, default=str)
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=f"dealflow_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_json"
        )

    # Memo text export
    with col2:
        memo = data.get("ic_memo", data.get("memo", ""))
        if isinstance(memo, dict):
            memo_text = "\n\n".join([f"## {k}\n{v}" for k, v in memo.items()])
        else:
            memo_text = str(memo) if memo else "No memo available"

        st.download_button(
            label="Download Memo",
            data=memo_text,
            file_name=f"ic_memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_memo"
        )

    # Summary export
    with col3:
        exec_summary = data.get("executive_summary", {})
        if isinstance(exec_summary, dict):
            summary_text = f"Recommendation: {exec_summary.get('recommendation', 'N/A')}\n\n"
            summary_text += f"Summary: {exec_summary.get('summary', 'N/A')}\n\n"
            if exec_summary.get("key_highlights"):
                summary_text += "Key Highlights:\n"
                for h in exec_summary.get("key_highlights", []):
                    summary_text += f"- {h}\n"
        else:
            summary_text = str(exec_summary)

        st.download_button(
            label="Download Summary",
            data=summary_text,
            file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_summary"
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_results_dashboard(data: Dict[str, Any]) -> None:
    """
    Render the complete results dashboard.

    Args:
        data: Full analysis results data from the API
    """
    if not data:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5" style="margin-bottom: 1rem;">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <h3 style="color: #94a3b8;">No Analysis Results</h3>
            <p style="color: #64748b;">Upload documents and run analysis to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Render all dashboard sections
    render_executive_summary(data)
    render_company_data(data)
    render_risk_assessment(data)
    render_valuation(data)
    render_ic_memo(data)
    render_export_options(data)
