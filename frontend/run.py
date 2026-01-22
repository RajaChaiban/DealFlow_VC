#!/usr/bin/env python3
"""
DealFlow AI Copilot - Frontend Launcher

This script provides a convenient way to launch the Streamlit frontend
with proper configuration and environment setup.

Usage:
    python run.py [--port PORT] [--debug]
"""

import subprocess
import sys
import argparse
from pathlib import Path


def main():
    """Main entry point for the launcher."""
    parser = argparse.ArgumentParser(
        description="Launch DealFlow AI Copilot Frontend"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to run the Streamlit server on (default: 8501)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode with additional logging"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    # Get the directory containing this script
    script_dir = Path(__file__).parent
    app_path = script_dir / "app.py"

    # Build the Streamlit command
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port),
        "--server.headless",
        "true",
    ]

    if args.debug:
        cmd.extend(["--logger.level", "debug"])

    print(f"Starting DealFlow AI Copilot Frontend on port {args.port}...")
    print(f"Backend API URL: {args.api_url}")
    print(f"Open http://localhost:{args.port} in your browser")
    print("-" * 50)

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to start Streamlit server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
