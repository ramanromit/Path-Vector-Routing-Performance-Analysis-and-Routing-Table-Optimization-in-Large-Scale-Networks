"""
OBSIDIAN Path Vector Demo Launcher
===================================
One-click launcher for the BGP Path Vector Routing Telemetry Dashboard.

Usage:
    python start_demo.py
    python start_demo.py --port 8080
    python start_demo.py --no-browser
"""

import argparse
import os
import sys
import time
import threading
import webbrowser


def check_dependencies():
    """Verify all critical imports are available."""
    missing = []
    for mod in ["fastapi", "uvicorn", "networkx", "numpy", "matplotlib", "pandas"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"[ERROR] Missing packages: {', '.join(missing)}")
        print(f"[FIX]   Run: pip install -r requirements.txt")
        sys.exit(1)

    print("[OK] All dependencies verified.")


def open_browser(port, delay=2.5):
    """Opens the dashboard in the default browser after a short delay."""
    time.sleep(delay)
    url = f"http://localhost:{port}"
    print(f"\n[BROWSER] Opening {url} ...")
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="Launch the Obsidian BGP Telemetry Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open the browser")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    args = parser.parse_args()

    # Ensure we run from project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("=" * 60)
    print("  OBSIDIAN // Path Vector Routing Telemetry Dashboard")
    print("  BGP-4 Simulation & Routing Table Optimization Console")
    print("=" * 60)
    print()

    check_dependencies()

    import socket

    def get_free_port(host, preferred_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, preferred_port)) != 0:
                return preferred_port
        for p in range(preferred_port + 1, preferred_port + 20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((host, p)) != 0:
                    print(f"[PORT] Port {preferred_port} in use, automatically selecting port {p}.")
                    return p
        return preferred_port

    active_port = get_free_port(args.host, args.port)

    print(f"[SERVER] Starting on http://{args.host}:{active_port}")
    print(f"[SERVER] Dashboard will be served at http://localhost:{active_port}")
    print(f"[SERVER] Press Ctrl+C to stop.\n")

    # Auto-open browser in background thread
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(active_port,), daemon=True).start()

    # Launch uvicorn
    import uvicorn
    uvicorn.run(
        "src.server:app",
        host=args.host,
        port=active_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
