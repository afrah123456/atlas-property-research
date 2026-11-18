import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
port = os.getenv("PORT", "7860")

os.execv(
    sys.executable,
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(root / "app.py"),
        f"--server.port={port}",
        "--server.address=0.0.0.0",
        "--server.headless=true",
    ],
)
