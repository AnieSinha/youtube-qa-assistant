"""
Startup script for the YouTube Q&A Assistant API.

Usage:
    python run.py              # default: http://localhost:8000
    python run.py --port 9000  # custom port
    python run.py --reload     # auto-reload on code changes
"""

import os
import sys
import subprocess

# ------------------------------------------------------------------
# Auto-switch to the project venv on Windows.
# Uses subprocess.run (not os.execv) so PowerShell stays attached and
# Ctrl+C propagates correctly to the server process.
# ------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.abspath(__file__))
_VENV_PYTHON = os.path.join(_ROOT, "venv", "Scripts", "python.exe")

if (os.path.exists(_VENV_PYTHON) and
        os.path.normcase(os.path.abspath(sys.executable)) !=
        os.path.normcase(os.path.abspath(_VENV_PYTHON))):
    print(f"[run.py] Switching to venv Python: {_VENV_PYTHON}\n")
    result = subprocess.run([_VENV_PYTHON] + sys.argv)
    sys.exit(result.returncode)

import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Q&A Assistant API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print(f"\n  YouTube Q&A Assistant")
    print(f"  API  ->  http://localhost:{args.port}")
    print(f"  UI   ->  http://localhost:{args.port}/\n")

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
