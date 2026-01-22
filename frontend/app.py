"""
DealFlow AI Copilot - Streamlit Frontend

A production-grade web interface for AI-powered investment deal analysis.
Provides document upload, real-time analysis progress tracking, and comprehensive
results dashboard for investment committee memos.

Author: DealFlow Team
Version: 1.0.0
"""

import streamlit as st
import time
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add the frontend directory to path for imports
frontend_dir = Path(__file__).parent
if str(frontend_dir) not in sys.path:
    sys.path.insert(0, str(frontend_dir))

# Import components and utilities
from utils.api_client import DealFlowAPIClient, get_api_client
from utils.styling import get_custom_css, get_skeleton_html
from components.upload import render_upload_section, get_file_data, render_upload_help
from components.progress import (
    render_progress_indicator,
    render_loading_spinner,
    render_error_state,
    map_api_status_to_steps
)
from components.results import render_results_dashboard


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="DealFlow AI Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/dealflow/support",
        "Report a bug": "https://github.com/dealflow/issues",
        "About": "DealFlow AI Copilot - Intelligent Investment Analysis Platform"
    }
)


# ============================================================================
# INJECT CUSTOM CSS
# ============================================================================

st.markdown(get_custom_css(), unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    if "analysis_in_progress" not in st.session_state:
        st.session_state.analysis_in_progress = False

    if "analysis_status" not in st.session_state:
        st.session_state.analysis_status = None

    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None

    if "api_client" not in st.session_state:
        st.session_state.api_client = None

    if "backend_status" not in st.session_state:
        st.session_state.backend_status = "unknown"

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0


init_session_state()


# ============================================================================
# API CLIENT SETUP
# ============================================================================

@st.cache_resource
def get_cached_api_client(base_url: str) -> DealFlowAPIClient:
    """Get a cached API client instance."""
    return get_api_client(base_url)


def check_backend_health() -> bool:
    """Check if the backend API is healthy."""
    try:
        client = get_cached_api_client(st.session_state.get("api_base_url", "http://localhost:8000"))
        response = client.health_check()
        return response.success
    except Exception:
        return False


# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    """Render the sidebar with settings and information."""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <h1 style="font-size: 1.5rem; margin-top: 0.5rem; background: linear-gradient(135deg, #f8fafc 0%, #d4a853 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                DealFlow AI
            </h1>
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;">
                Investment Analysis Copilot
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Backend settings
        st.markdown("### Settings")

        api_base_url = st.text_input(
            "API Base URL",
            value=st.session_state.get("api_base_url", "http://localhost:8000"),
            help="Backend API server URL",
            key="api_url_input"
        )

        if api_base_url != st.session_state.get("api_base_url"):
            st.session_state.api_base_url = api_base_url
            st.cache_resource.clear()

        # Health check
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("Check Connection", key="health_check_btn"):
                with st.spinner("Checking..."):
                    is_healthy = check_backend_health()
                    st.session_state.backend_status = "healthy" if is_healthy else "unhealthy"

        with col2:
            if st.session_state.backend_status == "healthy":
                st.markdown('<span class="status-badge success" style="font-size: 0.7rem;">Online</span>', unsafe_allow_html=True)
            elif st.session_state.backend_status == "unhealthy":
                st.markdown('<span class="status-badge error" style="font-size: 0.7rem;">Offline</span>', unsafe_allow_html=True)

        st.markdown("---")

        # Analysis options
        st.markdown("### Analysis Options")

        analysis_mode = st.radio(
            "Analysis Mode",
            options=["Synchronous", "Asynchronous"],
            index=0,
            help="Sync: Wait for complete results. Async: Track progress in real-time.",
            key="analysis_mode"
        )

        st.session_state.use_async = analysis_mode == "Asynchronous"

        st.markdown("---")

        # Help section
        with st.expander("Quick Guide", expanded=False):
            st.markdown("""
            **How to use DealFlow AI:**

            1. **Upload** your pitch deck PDF(s)
            2. **Enter** company name (optional)
            3. **Click** "Analyze Deal"
            4. **Review** the AI-generated IC memo

            **What you'll get:**
            - Executive summary with recommendation
            - Key financial metrics
            - Risk assessment
            - Valuation analysis
            - Full investment memo
            """)

        # Footer
        st.markdown("""
        <div style="position: fixed; bottom: 1rem; left: 1rem; right: 1rem; text-align: center;">
            <p style="color: #475569; font-size: 0.75rem;">
                v1.0.0 | Built with Streamlit
            </p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# MAIN CONTENT
# ============================================================================

def run_analysis(files: list, company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the deal analysis via the API.

    Args:
        files: List of uploaded files
        company_name: Optional company name

    Returns:
        Analysis results dictionary
    """
    client = get_cached_api_client(st.session_state.get("api_base_url", "http://localhost:8000"))

    # Prepare file data
    file_data = get_file_data(files)

    if st.session_state.use_async:
        # Async analysis with polling
        # First upload files
        upload_response = client.upload_documents(file_data)
        if not upload_response.success:
            raise Exception(f"File upload failed: {upload_response.error}")

        file_ids = upload_response.data.get("file_ids", [])

        # Start async analysis
        analysis_response = client.analyze_async(file_ids=file_ids, company_name=company_name)
        if not analysis_response.success:
            raise Exception(f"Analysis start failed: {analysis_response.error}")

        analysis_id = analysis_response.data.get("analysis_id")

        # Poll for results
        def status_callback(status_data):
            st.session_state.analysis_status = status_data
            st.session_state.current_step = _get_step_from_status(status_data)

        result = client.poll_analysis(
            analysis_id=analysis_id,
            poll_interval=2,
            max_wait=300,
            callback=status_callback
        )

        if not result.success:
            raise Exception(f"Analysis failed: {result.error}")

        return result.data

    else:
        # Sync analysis
        response = client.analyze_sync(
            uploaded_files=file_data,
            company_name=company_name
        )

        if not response.success:
            raise Exception(f"Analysis failed: {response.error}")

        return response.data


def _get_step_from_status(status_data: Dict) -> int:
    """Get the current step index from status data."""
    stage = status_data.get("current_stage", "").lower()
    stage_mapping = {
        "extraction": 0,
        "document_processing": 0,
        "analysis": 1,
        "business_analysis": 1,
        "risk": 2,
        "risk_assessment": 2,
        "valuation": 3,
        "memo_generation": 3,
    }
    return stage_mapping.get(stage, 0)


def render_main_content():
    """Render the main content area."""
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem;">
        <h1>DealFlow AI Copilot</h1>
        <p style="color: #94a3b8; font-size: 1.125rem; max-width: 600px; margin: 0 auto;">
            AI-powered investment analysis for venture capital and private equity.
            Upload your pitch deck and get a comprehensive IC memo in minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Check backend status on first load
    if st.session_state.backend_status == "unknown":
        st.session_state.backend_status = "healthy" if check_backend_health() else "unhealthy"

    # Show warning if backend is offline
    if st.session_state.backend_status == "unhealthy":
        st.markdown("""
        <div class="glass-card" style="border-left: 4px solid #f59e0b; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <div>
                    <strong style="color: #f59e0b;">Backend Offline</strong>
                    <p style="color: #94a3b8; margin: 0; font-size: 0.875rem;">
                        Unable to connect to the API server. Please ensure the backend is running at the configured URL.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main layout - two columns
    if st.session_state.analysis_results:
        # Show results if available
        st.markdown("## Analysis Results")
        render_results_dashboard(st.session_state.analysis_results)

        # Option to start new analysis
        st.markdown("---")
        if st.button("Start New Analysis", key="new_analysis_btn"):
            st.session_state.analysis_results = None
            st.session_state.analysis_status = None
            st.session_state.analysis_error = None
            st.session_state.current_step = 0
            st.rerun()

    elif st.session_state.analysis_in_progress:
        # Show progress
        st.markdown("## Analysis in Progress")
        render_progress_indicator(
            current_step=st.session_state.current_step,
            api_status=st.session_state.analysis_status
        )
        render_loading_spinner("Analyzing your deal...")

        # Auto-refresh for async mode
        if st.session_state.use_async:
            time.sleep(2)
            st.rerun()

    elif st.session_state.analysis_error:
        # Show error state
        render_error_state(
            st.session_state.analysis_error,
            retry_callback=lambda: setattr(st.session_state, 'analysis_error', None)
        )

    else:
        # Show upload interface
        col1, col2 = st.columns([2, 1])

        with col1:
            # Upload section
            files, company_name = render_upload_section()

            # Analyze button
            st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)

            analyze_disabled = not files or st.session_state.backend_status == "unhealthy"

            if st.button(
                "Analyze Deal",
                key="analyze_btn",
                disabled=analyze_disabled,
                type="primary",
                use_container_width=True
            ):
                if files:
                    st.session_state.analysis_in_progress = True
                    st.session_state.analysis_error = None

                    try:
                        # Run analysis
                        with st.spinner("Starting analysis..."):
                            results = run_analysis(files, company_name)

                        st.session_state.analysis_results = results
                        st.session_state.analysis_in_progress = False
                        st.rerun()

                    except Exception as e:
                        st.session_state.analysis_in_progress = False
                        st.session_state.analysis_error = str(e)
                        st.rerun()

            if not files:
                st.markdown("""
                <p style="color: #64748b; font-size: 0.875rem; text-align: center; margin-top: 0.5rem;">
                    Upload at least one PDF to enable analysis
                </p>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            # Help and info section
            render_upload_help()

            # Feature highlights
            st.markdown("""
            <div class="glass-card" style="margin-top: 1rem;">
                <h4 style="color: #d4a853; margin-bottom: 1rem;">Analysis Includes</h4>
                <ul style="color: #94a3b8; padding-left: 1.25rem; margin: 0;">
                    <li style="margin-bottom: 0.5rem;">Executive Summary</li>
                    <li style="margin-bottom: 0.5rem;">Financial Analysis</li>
                    <li style="margin-bottom: 0.5rem;">Market Assessment</li>
                    <li style="margin-bottom: 0.5rem;">Risk Evaluation</li>
                    <li style="margin-bottom: 0.5rem;">Valuation Range</li>
                    <li style="margin-bottom: 0.5rem;">Investment Recommendation</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# MAIN APP ENTRY POINT
# ============================================================================

def main():
    """Main application entry point."""
    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_content()


if __name__ == "__main__":
    main()
