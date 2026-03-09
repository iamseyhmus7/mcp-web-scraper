import os
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any

# According to AGENTS.md, screenshot path should be under /tmp
# We will use tempfile to be cross-platform compatible but maintain structure.
temp_dir = tempfile.gettempdir()
SCREENSHOT_DIR = Path(temp_dir) / "mcp-scraper" / "screenshots"

# In-memory storage for jobs
jobs: Dict[str, Any] = {}

def ensure_screenshot_dir():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_screenshot(job_id: str, data: bytes) -> str:
    """Save a screenshot and return its path."""
    ensure_screenshot_dir()
    path = SCREENSHOT_DIR / f"{job_id}.png"
    path.write_bytes(data)
    return str(path)

def get_base64_screenshot(path: str) -> str:
    """Read a screenshot and return base64 encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
