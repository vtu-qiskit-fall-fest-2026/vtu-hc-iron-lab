"""Entry point for the Q-GibberLink Quantum Security Platform.

Launches the Streamlit dashboard on port 8501.

Usage:
    python main.py
"""

import subprocess
import sys
import os

# Port for the Streamlit dashboard — configurable via environment variable.
DASHBOARD_PORT = os.environ.get("QGIBBERLINK_PORT", "8501")
DASHBOARD_SCRIPT = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")


def main() -> None:
    """Launch the Streamlit dashboard."""
    print("=" * 60)
    print("  Iron Lab: Hybrid QKD + Kyber768 Quantum AI Agent Platform")
    print("  Attack Marketplace & Security Platform")
    print("=" * 60)
    print(f"  Launching dashboard on port {DASHBOARD_PORT}...")
    print(f"  Open http://localhost:{DASHBOARD_PORT} in your browser.")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        DASHBOARD_SCRIPT,
        "--server.port",
        DASHBOARD_PORT,
        "--server.headless",
        "true",
        "--theme.base",
        "light",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down Q-GibberLink dashboard...")
    except FileNotFoundError:
        print(
            "ERROR: Streamlit is not installed.\n"
            "Install dependencies with: pip install -r requirements.txt"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
