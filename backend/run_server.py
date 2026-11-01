"""
RailSamiksha AI — Backend Server Launcher
=========================================
Runs Uvicorn ASGI server with Starlette app on port 8000.
"""

import os
import sys

# Prevent OpenMP thread heap contention on multi-core CPU
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import uvicorn
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    print("=" * 70)
    print("🚆 RailSamiksha AI — Full-Stack Backend & Inference Server")
    print("   • Serving REST API & RT-DETR-L on: http://localhost:8000")
    print("   • Serving Integrated Web Frontend on: http://localhost:8000/")
    print("   • SQLite TMS Database: database/railsamiksha.db")
    print("=" * 70)

    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

