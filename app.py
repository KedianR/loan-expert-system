"""
Vercel deployment entrypoint for LoanCheck UI.

Exposes the ASGI FastAPI `app` instance at the repository root.
Spec: docs/05-architecture.md, vercel.json
"""

import sys
from pathlib import Path

# Ensure the repository root is on sys.path for local runs and Vercel serverless environment
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ui.app import app  # noqa: E402

__all__ = ["app"]
