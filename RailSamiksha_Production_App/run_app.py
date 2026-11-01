"""
RailSamiksha Standalone Launcher
================================
Launches the Streamlit application with automatic thread control and
Windows connection lost suppression.
"""

import os
import sys

# Limit threads for CPU inference stability
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Prevent Windows [WinError 10054] ConnectionResetError on browser disconnect
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _patched_call_connection_lost(self, exc):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _patched_call_connection_lost
    except Exception:
        pass

from streamlit.web import cli as stcli

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",
        "--server.headless=true",
        "--server.address=localhost",
    ]
    sys.exit(stcli.main())

