"""
Document Upload Component for DealFlow AI Copilot

Features:
- Drag & drop PDF upload with visual feedback
- Multiple file support
- File validation and preview
- Company name input option
- File size and type checking
"""

import streamlit as st
from typing import List, Tuple, Optional
import base64


# Constants
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = [".pdf"]
MAX_FILES = 10


def validate_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate an uploaded file.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "No file provided"

    # Check file extension
    file_name = uploaded_file.name.lower()
    if not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."

    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."

    return True, ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes} bytes"


def render_file_preview(files: List) -> None:
    """
    Render preview cards for uploaded files.

    Args:
        files: List of uploaded file objects
    """
    for i, file in enumerate(files):
        is_valid, error = validate_file(file)

        # Determine status styling
        if is_valid:
            status_class = "success"
            status_icon = "check_circle"
        else:
            status_class = "error"
            status_icon = "error"

        file_html = f"""
        <div class="file-preview fade-in" style="animation-delay: {i * 0.1}s;">
            <div class="file-icon">PDF</div>
            <div class="file-info">
                <div class="file-name">{file.name}</div>
                <div class="file-size">{format_file_size(file.size)}</div>
                {"<div style='color: #ef4444; font-size: 0.75rem; margin-top: 0.25rem;'>" + error + "</div>" if not is_valid else ""}
            </div>
            <div class="status-badge {status_class}" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                {"Valid" if is_valid else "Invalid"}
            </div>
        </div>
        """
        st.markdown(file_html, unsafe_allow_html=True)


def render_upload_zone() -> None:
    """Render the drag & drop upload zone."""
    upload_html = """
    <div class="upload-zone" id="upload-zone">
        <div class="upload-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
        </div>
        <div class="upload-text">Drag & drop your pitch deck here</div>
        <div class="upload-subtext">or click to browse files</div>
        <div class="upload-subtext" style="margin-top: 0.5rem;">
            Supported: PDF files up to 50MB
        </div>
    </div>
    """
    st.markdown(upload_html, unsafe_allow_html=True)


def render_upload_section() -> Tuple[Optional[List], Optional[str]]:
    """
    Render the complete upload section.

    Returns:
        Tuple of (uploaded_files, company_name)
    """
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
            <h3 class="glass-card-title" style="margin: 0;">Document Upload</h3>
        </div>
    """, unsafe_allow_html=True)

    # Render upload zone visual
    render_upload_zone()

    # Streamlit file uploader (actual functionality)
    uploaded_files = st.file_uploader(
        "Upload pitch deck PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader",
        help="Upload one or more PDF files containing the company pitch deck, financials, or other relevant documents.",
        label_visibility="collapsed"
    )

    # File count indicator
    if uploaded_files:
        valid_count = sum(1 for f in uploaded_files if validate_file(f)[0])
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(34, 197, 94, 0.1); border-radius: 8px; border-left: 3px solid #22c55e;">
            <span style="color: #22c55e; font-weight: 500;">{valid_count} of {len(uploaded_files)} file(s) ready for analysis</span>
        </div>
        """, unsafe_allow_html=True)

        # Render file previews
        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
        render_file_preview(uploaded_files)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Company name input section
    st.markdown("""
    <div class="glass-card fade-in" style="margin-top: 1.5rem;">
        <div class="glass-card-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <h3 class="glass-card-title" style="margin: 0;">Company Information</h3>
        </div>
        <p style="color: #94a3b8; font-size: 0.875rem; margin-bottom: 1rem;">
            Optionally provide the company name for enhanced web research and market analysis.
        </p>
    """, unsafe_allow_html=True)

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g., Acme Technologies, Inc.",
        help="Enter the company name to enable additional web research and market intelligence gathering.",
        key="company_name_input"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Return validated files and company name
    valid_files = []
    if uploaded_files:
        for f in uploaded_files:
            is_valid, _ = validate_file(f)
            if is_valid:
                valid_files.append(f)

    return valid_files if valid_files else None, company_name if company_name else None


def get_file_data(files: List) -> List[Tuple[str, bytes, str]]:
    """
    Prepare file data for API upload.

    Args:
        files: List of Streamlit UploadedFile objects

    Returns:
        List of tuples (filename, file_bytes, content_type)
    """
    file_data = []
    for f in files:
        # Reset file pointer to beginning
        f.seek(0)
        file_bytes = f.read()
        file_data.append((f.name, file_bytes, "application/pdf"))
        # Reset again for potential re-read
        f.seek(0)

    return file_data


def render_upload_help() -> None:
    """Render help information for the upload section."""
    with st.expander("Upload Guidelines", expanded=False):
        st.markdown("""
        ### Supported Documents

        - **Pitch Decks**: Company presentations, investor decks
        - **Financial Statements**: Income statements, balance sheets, cash flow
        - **Market Analysis**: Industry reports, competitive analysis
        - **Team Information**: Founder bios, org charts

        ### Best Practices

        1. **High-quality PDFs**: Ensure text is selectable (not scanned images)
        2. **Complete documents**: Upload all relevant sections
        3. **Recent data**: Use the most up-to-date financials available
        4. **Clear formatting**: Well-structured documents yield better analysis

        ### File Requirements

        - Format: PDF only
        - Size: Maximum 50MB per file
        - Count: Up to 10 files per analysis
        """)
