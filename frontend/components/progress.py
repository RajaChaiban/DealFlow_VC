"""
Progress Indicator Component for DealFlow AI Copilot

Features:
- Multi-step progress visualization
- Real-time status updates
- Animated transitions
- Agent status display (Extraction, Analysis, Risk, Valuation)
"""

import streamlit as st
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class StepStatus(Enum):
    """Status of each analysis step."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AnalysisStep:
    """Represents a single step in the analysis pipeline."""
    id: str
    name: str
    description: str
    icon: str
    status: StepStatus = StepStatus.PENDING


# Define the analysis pipeline steps
ANALYSIS_STEPS = [
    AnalysisStep(
        id="extraction",
        name="Extraction",
        description="Processing documents and extracting key data",
        icon="""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>"""
    ),
    AnalysisStep(
        id="analysis",
        name="Analysis",
        description="Analyzing business model and market opportunity",
        icon="""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>"""
    ),
    AnalysisStep(
        id="risk",
        name="Risk Assessment",
        description="Evaluating risks and red flags",
        icon="""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>"""
    ),
    AnalysisStep(
        id="valuation",
        name="Valuation",
        description="Computing valuation and generating IC memo",
        icon="""<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>"""
    ),
]


def get_step_status_class(status: StepStatus) -> str:
    """Get CSS class for step status."""
    return {
        StepStatus.PENDING: "pending",
        StepStatus.ACTIVE: "active",
        StepStatus.COMPLETED: "completed",
        StepStatus.ERROR: "error"
    }.get(status, "pending")


def get_step_icon(status: StepStatus) -> str:
    """Get icon for step status."""
    if status == StepStatus.COMPLETED:
        return """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
        </svg>"""
    elif status == StepStatus.ERROR:
        return """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>"""
    else:
        return ""


def map_api_status_to_steps(api_status: Optional[Dict]) -> List[AnalysisStep]:
    """
    Map API status response to step statuses.

    Args:
        api_status: Status response from the API

    Returns:
        List of AnalysisStep objects with updated statuses
    """
    steps = [AnalysisStep(**{**s.__dict__}) for s in ANALYSIS_STEPS]

    if not api_status:
        return steps

    current_stage = api_status.get("current_stage", "")
    progress = api_status.get("progress", 0)
    status = api_status.get("status", "pending")

    # Map stage names to step IDs
    stage_mapping = {
        "extraction": 0,
        "document_processing": 0,
        "analysis": 1,
        "business_analysis": 1,
        "market_analysis": 1,
        "risk": 2,
        "risk_assessment": 2,
        "valuation": 3,
        "memo_generation": 3,
        "completed": 4,
    }

    current_step_idx = stage_mapping.get(current_stage.lower(), 0)

    # Update step statuses based on progress
    for i, step in enumerate(steps):
        if status == "completed":
            step.status = StepStatus.COMPLETED
        elif status == "failed":
            if i < current_step_idx:
                step.status = StepStatus.COMPLETED
            elif i == current_step_idx:
                step.status = StepStatus.ERROR
            else:
                step.status = StepStatus.PENDING
        else:
            if i < current_step_idx:
                step.status = StepStatus.COMPLETED
            elif i == current_step_idx:
                step.status = StepStatus.ACTIVE
            else:
                step.status = StepStatus.PENDING

    return steps


def render_progress_indicator(
    current_step: int = 0,
    api_status: Optional[Dict] = None,
    show_details: bool = True
) -> None:
    """
    Render the progress indicator component.

    Args:
        current_step: Index of the current step (0-based)
        api_status: Optional API status response for dynamic updates
        show_details: Whether to show step descriptions
    """
    # Map API status to steps if provided
    if api_status:
        steps = map_api_status_to_steps(api_status)
    else:
        steps = [AnalysisStep(**{**s.__dict__}) for s in ANALYSIS_STEPS]
        for i, step in enumerate(steps):
            if i < current_step:
                step.status = StepStatus.COMPLETED
            elif i == current_step:
                step.status = StepStatus.ACTIVE
            else:
                step.status = StepStatus.PENDING

    # Render progress container
    st.markdown("""
    <div class="glass-card fade-in">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Analysis Progress</h3>
        </div>
    """, unsafe_allow_html=True)

    # Build progress steps HTML
    steps_html = '<div class="progress-container">'

    for i, step in enumerate(steps):
        status_class = get_step_status_class(step.status)
        step_icon = get_step_icon(step.status)

        # Determine connector class
        connector_class = ""
        if i < len(steps) - 1:
            if step.status == StepStatus.COMPLETED:
                connector_class = "completed"
            elif step.status == StepStatus.ACTIVE:
                connector_class = "active"

        steps_html += f"""
        <div class="progress-step {connector_class}">
            <div class="step-circle {status_class}">
                {step_icon if step_icon else i + 1}
            </div>
            <div class="step-label {status_class}">{step.name}</div>
        </div>
        """

    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)

    # Show current step details
    if show_details:
        active_step = next((s for s in steps if s.status == StepStatus.ACTIVE), None)
        if active_step:
            st.markdown(f"""
            <div style="text-align: center; margin-top: 1rem; padding: 1rem; background: rgba(212, 168, 83, 0.1); border-radius: 12px;">
                <div style="color: #d4a853; font-weight: 500; margin-bottom: 0.25rem;">
                    Currently Processing
                </div>
                <div style="color: #94a3b8; font-size: 0.875rem;">
                    {active_step.description}
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif all(s.status == StepStatus.COMPLETED for s in steps):
            st.markdown("""
            <div style="text-align: center; margin-top: 1rem; padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 12px;">
                <div style="color: #22c55e; font-weight: 500;">
                    Analysis Complete
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_loading_spinner(message: str = "Analyzing...") -> None:
    """
    Render a loading spinner with message.

    Args:
        message: Loading message to display
    """
    spinner_html = f"""
    <div class="glass-card" style="text-align: center; padding: 3rem;">
        <div class="loading-spinner" style="margin: 0 auto 1.5rem;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
                <line x1="12" y1="2" x2="12" y2="6"/>
                <line x1="12" y1="18" x2="12" y2="22"/>
                <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
                <line x1="2" y1="12" x2="6" y2="12"/>
                <line x1="18" y1="12" x2="22" y2="12"/>
                <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
                <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
            </svg>
        </div>
        <div style="color: #f8fafc; font-size: 1.25rem; font-weight: 500; margin-bottom: 0.5rem;">
            {message}
        </div>
        <div style="color: #94a3b8; font-size: 0.875rem;">
            This may take a few minutes for comprehensive analysis
        </div>
    </div>

    <style>
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
    </style>
    """
    st.markdown(spinner_html, unsafe_allow_html=True)


def render_error_state(error_message: str, retry_callback=None) -> None:
    """
    Render an error state with optional retry button.

    Args:
        error_message: Error message to display
        retry_callback: Optional callback function for retry button
    """
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid #ef4444;">
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <div style="color: #ef4444;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
            </div>
            <div style="flex: 1;">
                <div style="color: #ef4444; font-weight: 600; margin-bottom: 0.5rem;">
                    Analysis Failed
                </div>
                <div style="color: #94a3b8; font-size: 0.875rem;">
                    {error_message}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if retry_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Retry Analysis", key="retry_btn"):
                retry_callback()


def render_status_badge(status: str) -> str:
    """
    Get HTML for a status badge.

    Args:
        status: Status string (processing, completed, failed, pending)

    Returns:
        HTML string for the badge
    """
    status_config = {
        "processing": ("info", "Processing"),
        "completed": ("success", "Completed"),
        "failed": ("error", "Failed"),
        "pending": ("warning", "Pending"),
    }

    badge_class, label = status_config.get(status.lower(), ("info", status))

    return f'<span class="status-badge {badge_class}">{label}</span>'
