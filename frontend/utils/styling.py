"""
Custom CSS Styling for DealFlow AI Copilot
Professional financial services design with glassmorphism effects.

Design Principles:
- Clean, sophisticated aesthetics for financial services
- Deep navy, slate gray, muted gold accents
- Glassmorphism and soft shadows
- WCAG 2.1 AA accessibility compliance
"""

from typing import Dict


def get_theme_colors() -> Dict[str, str]:
    """
    Get the color palette for the DealFlow theme.

    Returns:
        Dictionary of color names to hex values
    """
    return {
        # Primary colors
        "navy_primary": "#0a1628",
        "navy_secondary": "#1a2744",
        "navy_light": "#2a3b5c",

        # Neutral colors
        "slate_dark": "#334155",
        "slate_medium": "#475569",
        "slate_light": "#64748b",
        "gray_100": "#f1f5f9",
        "gray_200": "#e2e8f0",
        "gray_300": "#cbd5e1",

        # Accent colors
        "gold_primary": "#d4a853",
        "gold_light": "#e6c87a",
        "gold_muted": "#a08432",

        # Status colors (accessible)
        "success": "#22c55e",
        "success_bg": "#052e16",
        "warning": "#f59e0b",
        "warning_bg": "#451a03",
        "error": "#ef4444",
        "error_bg": "#450a0a",
        "info": "#3b82f6",
        "info_bg": "#172554",

        # Risk severity colors
        "risk_critical": "#dc2626",
        "risk_high": "#f97316",
        "risk_medium": "#eab308",
        "risk_low": "#22c55e",

        # Text colors
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",

        # Glass effect colors
        "glass_bg": "rgba(26, 39, 68, 0.7)",
        "glass_border": "rgba(255, 255, 255, 0.1)",
        "glass_shadow": "rgba(0, 0, 0, 0.3)",
    }


def get_custom_css() -> str:
    """
    Get the complete custom CSS for the application.

    Returns:
        CSS string for Streamlit markdown injection
    """
    colors = get_theme_colors()

    return f"""
    <style>
        /* ================================================
           ROOT VARIABLES & RESETS
           ================================================ */
        :root {{
            --navy-primary: {colors['navy_primary']};
            --navy-secondary: {colors['navy_secondary']};
            --navy-light: {colors['navy_light']};
            --slate-dark: {colors['slate_dark']};
            --slate-medium: {colors['slate_medium']};
            --slate-light: {colors['slate_light']};
            --gold-primary: {colors['gold_primary']};
            --gold-light: {colors['gold_light']};
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --glass-bg: {colors['glass_bg']};
            --glass-border: {colors['glass_border']};
        }}

        /* ================================================
           GLOBAL STYLES
           ================================================ */
        .stApp {{
            background: linear-gradient(135deg, {colors['navy_primary']} 0%, {colors['navy_secondary']} 50%, {colors['navy_light']} 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        /* Main content area */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}

        /* ================================================
           TYPOGRAPHY
           ================================================ */
        h1, h2, h3, h4, h5, h6 {{
            color: {colors['text_primary']} !important;
            font-weight: 600;
        }}

        h1 {{
            font-size: 2.5rem !important;
            background: linear-gradient(135deg, {colors['text_primary']} 0%, {colors['gold_primary']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem !important;
        }}

        h2 {{
            font-size: 1.75rem !important;
            border-bottom: 2px solid {colors['gold_primary']};
            padding-bottom: 0.5rem;
            margin-top: 2rem !important;
        }}

        h3 {{
            font-size: 1.25rem !important;
            color: {colors['gold_light']} !important;
        }}

        p, span, div {{
            color: {colors['text_secondary']};
        }}

        /* ================================================
           GLASS CARD COMPONENT
           ================================================ */
        .glass-card {{
            background: {colors['glass_bg']};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {colors['glass_border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px {colors['glass_shadow']};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px {colors['glass_shadow']};
        }}

        .glass-card-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid {colors['glass_border']};
        }}

        .glass-card-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: {colors['text_primary']};
            margin: 0;
        }}

        /* ================================================
           UPLOAD ZONE
           ================================================ */
        .upload-zone {{
            border: 2px dashed {colors['slate_medium']};
            border-radius: 16px;
            padding: 3rem 2rem;
            text-align: center;
            background: {colors['glass_bg']};
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .upload-zone:hover {{
            border-color: {colors['gold_primary']};
            background: rgba(212, 168, 83, 0.1);
        }}

        .upload-zone.drag-over {{
            border-color: {colors['gold_primary']};
            background: rgba(212, 168, 83, 0.15);
            transform: scale(1.02);
        }}

        .upload-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            color: {colors['gold_primary']};
        }}

        .upload-text {{
            font-size: 1.125rem;
            color: {colors['text_secondary']};
            margin-bottom: 0.5rem;
        }}

        .upload-subtext {{
            font-size: 0.875rem;
            color: {colors['text_muted']};
        }}

        /* ================================================
           FILE PREVIEW
           ================================================ */
        .file-preview {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: {colors['glass_bg']};
            border: 1px solid {colors['glass_border']};
            border-radius: 12px;
            margin: 0.5rem 0;
        }}

        .file-icon {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, {colors['error']} 0%, #dc2626 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 0.75rem;
        }}

        .file-info {{
            flex: 1;
        }}

        .file-name {{
            font-weight: 500;
            color: {colors['text_primary']};
            margin-bottom: 0.25rem;
        }}

        .file-size {{
            font-size: 0.875rem;
            color: {colors['text_muted']};
        }}

        .file-remove {{
            color: {colors['error']};
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 8px;
            transition: background 0.2s;
        }}

        .file-remove:hover {{
            background: {colors['error_bg']};
        }}

        /* ================================================
           BUTTONS
           ================================================ */
        .stButton > button {{
            background: linear-gradient(135deg, {colors['gold_primary']} 0%, {colors['gold_muted']} 100%) !important;
            color: {colors['navy_primary']} !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 16px rgba(212, 168, 83, 0.3) !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 24px rgba(212, 168, 83, 0.4) !important;
        }}

        .stButton > button:active {{
            transform: translateY(0) !important;
        }}

        /* Secondary button style */
        .secondary-btn > button {{
            background: transparent !important;
            border: 2px solid {colors['gold_primary']} !important;
            color: {colors['gold_primary']} !important;
        }}

        .secondary-btn > button:hover {{
            background: rgba(212, 168, 83, 0.1) !important;
        }}

        /* ================================================
           PROGRESS INDICATOR
           ================================================ */
        .progress-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem;
            background: {colors['glass_bg']};
            border-radius: 16px;
            margin: 1.5rem 0;
        }}

        .progress-step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
        }}

        .progress-step:not(:last-child)::after {{
            content: '';
            position: absolute;
            top: 20px;
            left: 60%;
            width: 80%;
            height: 2px;
            background: {colors['slate_medium']};
        }}

        .progress-step.completed:not(:last-child)::after {{
            background: {colors['success']};
        }}

        .progress-step.active:not(:last-child)::after {{
            background: linear-gradient(90deg, {colors['success']} 50%, {colors['slate_medium']} 50%);
        }}

        .step-circle {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            z-index: 1;
        }}

        .step-circle.pending {{
            background: {colors['slate_dark']};
            color: {colors['text_muted']};
            border: 2px solid {colors['slate_medium']};
        }}

        .step-circle.active {{
            background: {colors['gold_primary']};
            color: {colors['navy_primary']};
            border: 2px solid {colors['gold_light']};
            animation: pulse 1.5s infinite;
        }}

        .step-circle.completed {{
            background: {colors['success']};
            color: white;
            border: 2px solid {colors['success']};
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}

        .step-label {{
            font-size: 0.75rem;
            color: {colors['text_secondary']};
            text-align: center;
            max-width: 80px;
        }}

        .step-label.active {{
            color: {colors['gold_primary']};
            font-weight: 500;
        }}

        /* ================================================
           STATUS BADGES
           ================================================ */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .status-badge.success {{
            background: {colors['success_bg']};
            color: {colors['success']};
            border: 1px solid {colors['success']};
        }}

        .status-badge.warning {{
            background: {colors['warning_bg']};
            color: {colors['warning']};
            border: 1px solid {colors['warning']};
        }}

        .status-badge.error {{
            background: {colors['error_bg']};
            color: {colors['error']};
            border: 1px solid {colors['error']};
        }}

        .status-badge.info {{
            background: {colors['info_bg']};
            color: {colors['info']};
            border: 1px solid {colors['info']};
        }}

        /* Recommendation badges */
        .recommendation-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-size: 1.125rem;
            font-weight: 600;
        }}

        .recommendation-badge.strong-buy {{
            background: linear-gradient(135deg, #14532d 0%, #052e16 100%);
            color: {colors['success']};
            border: 2px solid {colors['success']};
        }}

        .recommendation-badge.buy {{
            background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
            color: #4ade80;
            border: 2px solid #4ade80;
        }}

        .recommendation-badge.hold {{
            background: linear-gradient(135deg, #422006 0%, #451a03 100%);
            color: {colors['warning']};
            border: 2px solid {colors['warning']};
        }}

        .recommendation-badge.pass {{
            background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
            color: {colors['error']};
            border: 2px solid {colors['error']};
        }}

        /* ================================================
           RISK CARDS
           ================================================ */
        .risk-card {{
            padding: 1rem 1.25rem;
            border-radius: 12px;
            margin: 0.75rem 0;
            border-left: 4px solid;
        }}

        .risk-card.critical {{
            background: rgba(220, 38, 38, 0.1);
            border-left-color: {colors['risk_critical']};
        }}

        .risk-card.high {{
            background: rgba(249, 115, 22, 0.1);
            border-left-color: {colors['risk_high']};
        }}

        .risk-card.medium {{
            background: rgba(234, 179, 8, 0.1);
            border-left-color: {colors['risk_medium']};
        }}

        .risk-card.low {{
            background: rgba(34, 197, 94, 0.1);
            border-left-color: {colors['risk_low']};
        }}

        .risk-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .risk-card.critical .risk-title {{ color: {colors['risk_critical']}; }}
        .risk-card.high .risk-title {{ color: {colors['risk_high']}; }}
        .risk-card.medium .risk-title {{ color: {colors['risk_medium']}; }}
        .risk-card.low .risk-title {{ color: {colors['risk_low']}; }}

        .risk-description {{
            font-size: 0.875rem;
            color: {colors['text_secondary']};
            line-height: 1.5;
        }}

        /* ================================================
           METRICS DISPLAY
           ================================================ */
        .metric-card {{
            background: {colors['glass_bg']};
            border: 1px solid {colors['glass_border']};
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {colors['gold_primary']};
            margin-bottom: 0.25rem;
        }}

        .metric-label {{
            font-size: 0.875rem;
            color: {colors['text_muted']};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .metric-change {{
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }}

        .metric-change.positive {{
            color: {colors['success']};
        }}

        .metric-change.negative {{
            color: {colors['error']};
        }}

        /* ================================================
           VALUATION CHART
           ================================================ */
        .valuation-range {{
            background: {colors['glass_bg']};
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}

        .valuation-bar {{
            height: 24px;
            background: linear-gradient(90deg,
                {colors['risk_low']} 0%,
                {colors['gold_primary']} 50%,
                {colors['risk_high']} 100%);
            border-radius: 12px;
            position: relative;
            margin: 1rem 0;
        }}

        .valuation-marker {{
            position: absolute;
            top: -8px;
            width: 4px;
            height: 40px;
            background: {colors['text_primary']};
            border-radius: 2px;
            transform: translateX(-50%);
        }}

        .valuation-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
        }}

        .valuation-label {{
            font-size: 0.875rem;
            color: {colors['text_secondary']};
        }}

        /* ================================================
           DATA TABLES
           ================================================ */
        .stDataFrame {{
            background: {colors['glass_bg']} !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }}

        .stDataFrame table {{
            color: {colors['text_secondary']} !important;
        }}

        .stDataFrame th {{
            background: {colors['navy_secondary']} !important;
            color: {colors['text_primary']} !important;
            font-weight: 600 !important;
        }}

        .stDataFrame td {{
            border-color: {colors['glass_border']} !important;
        }}

        /* ================================================
           EXPANDERS
           ================================================ */
        .streamlit-expanderHeader {{
            background: {colors['glass_bg']} !important;
            border: 1px solid {colors['glass_border']} !important;
            border-radius: 12px !important;
            color: {colors['text_primary']} !important;
        }}

        .streamlit-expanderHeader:hover {{
            border-color: {colors['gold_primary']} !important;
        }}

        .streamlit-expanderContent {{
            background: {colors['glass_bg']} !important;
            border: 1px solid {colors['glass_border']} !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
        }}

        /* ================================================
           SKELETON LOADERS
           ================================================ */
        .skeleton {{
            background: linear-gradient(90deg,
                {colors['navy_secondary']} 25%,
                {colors['navy_light']} 50%,
                {colors['navy_secondary']} 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
        }}

        @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        .skeleton-text {{
            height: 1rem;
            margin: 0.5rem 0;
        }}

        .skeleton-title {{
            height: 2rem;
            width: 60%;
            margin: 1rem 0;
        }}

        .skeleton-card {{
            height: 150px;
            margin: 1rem 0;
        }}

        /* ================================================
           INPUT FIELDS
           ================================================ */
        .stTextInput > div > div > input {{
            background: {colors['glass_bg']} !important;
            border: 1px solid {colors['glass_border']} !important;
            border-radius: 12px !important;
            color: {colors['text_primary']} !important;
            padding: 0.75rem 1rem !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {colors['gold_primary']} !important;
            box-shadow: 0 0 0 2px rgba(212, 168, 83, 0.2) !important;
        }}

        .stTextInput > label {{
            color: {colors['text_secondary']} !important;
        }}

        /* ================================================
           SIDEBAR
           ================================================ */
        section[data-testid="stSidebar"] {{
            background: {colors['navy_primary']} !important;
            border-right: 1px solid {colors['glass_border']} !important;
        }}

        section[data-testid="stSidebar"] .stMarkdown {{
            color: {colors['text_secondary']} !important;
        }}

        /* ================================================
           ALERTS & MESSAGES
           ================================================ */
        .stAlert {{
            background: {colors['glass_bg']} !important;
            border: 1px solid {colors['glass_border']} !important;
            border-radius: 12px !important;
        }}

        /* Success message */
        div[data-testid="stAlert"][data-baseweb="notification"] {{
            background: {colors['success_bg']} !important;
            border-left: 4px solid {colors['success']} !important;
        }}

        /* Error message */
        .stException {{
            background: {colors['error_bg']} !important;
            border: 1px solid {colors['error']} !important;
            border-radius: 12px !important;
            color: {colors['text_primary']} !important;
        }}

        /* ================================================
           TABS
           ================================================ */
        .stTabs [data-baseweb="tab-list"] {{
            background: {colors['glass_bg']} !important;
            border-radius: 12px !important;
            padding: 0.25rem !important;
            gap: 0.25rem !important;
        }}

        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            border-radius: 8px !important;
            color: {colors['text_secondary']} !important;
            font-weight: 500 !important;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            background: {colors['navy_light']} !important;
        }}

        .stTabs [aria-selected="true"] {{
            background: {colors['gold_primary']} !important;
            color: {colors['navy_primary']} !important;
        }}

        /* ================================================
           DOWNLOAD BUTTONS
           ================================================ */
        .stDownloadButton > button {{
            background: transparent !important;
            border: 2px solid {colors['gold_primary']} !important;
            color: {colors['gold_primary']} !important;
        }}

        .stDownloadButton > button:hover {{
            background: rgba(212, 168, 83, 0.1) !important;
        }}

        /* ================================================
           DIVIDERS
           ================================================ */
        hr {{
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg,
                transparent 0%,
                {colors['gold_primary']} 50%,
                transparent 100%) !important;
            margin: 2rem 0 !important;
        }}

        /* ================================================
           SCROLLBAR
           ================================================ */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: {colors['navy_primary']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {colors['slate_medium']};
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {colors['gold_primary']};
        }}

        /* ================================================
           ACCESSIBILITY: FOCUS STATES
           ================================================ */
        *:focus-visible {{
            outline: 2px solid {colors['gold_primary']} !important;
            outline-offset: 2px !important;
        }}

        /* ================================================
           ANIMATIONS
           ================================================ */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.3s ease-out;
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(-20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .slide-in {{
            animation: slideIn 0.3s ease-out;
        }}
    </style>
    """


def get_skeleton_html(variant: str = "card") -> str:
    """
    Generate skeleton loader HTML.

    Args:
        variant: Type of skeleton ("card", "text", "title", "metric")

    Returns:
        HTML string for skeleton loader
    """
    skeletons = {
        "card": '<div class="skeleton skeleton-card"></div>',
        "text": '<div class="skeleton skeleton-text"></div>',
        "title": '<div class="skeleton skeleton-title"></div>',
        "metric": '''
            <div class="metric-card">
                <div class="skeleton skeleton-title" style="width: 40%; margin: 0 auto;"></div>
                <div class="skeleton skeleton-text" style="width: 60%; margin: 0.5rem auto;"></div>
            </div>
        ''',
        "multi": '''
            <div class="glass-card">
                <div class="skeleton skeleton-title"></div>
                <div class="skeleton skeleton-text"></div>
                <div class="skeleton skeleton-text" style="width: 80%;"></div>
                <div class="skeleton skeleton-text" style="width: 60%;"></div>
            </div>
        '''
    }
    return skeletons.get(variant, skeletons["card"])


def format_currency(value: float, currency: str = "USD") -> str:
    """
    Format a number as currency.

    Args:
        value: The numeric value
        currency: Currency code

    Returns:
        Formatted currency string
    """
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """
    Format a number as percentage.

    Args:
        value: The numeric value (0.15 = 15%)

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.1f}%"
