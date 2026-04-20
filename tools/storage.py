"""
tools/storage.py
Simple JSON-backed key-value store for the learning loop memory.
"""

import json
import os
from pathlib import Path
from datetime import datetime

MEMORY_PATH = Path(os.getenv("MEMORY_PATH", "output/memory.json"))


def load_memory() -> dict:
    if MEMORY_PATH.exists():
        with open(MEMORY_PATH) as f:
            return json.load(f)
    return {
        "runs": [],
        "reply_style_notes": [],
        "subreddit_notes": {},
        "competitor_intel": {},
        "last_updated": None,
    }


def save_memory(memory: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory["last_updated"] = datetime.utcnow().isoformat()
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def append_run(run_summary: dict) -> None:
    memory = load_memory()
    memory["runs"].append({**run_summary, "timestamp": datetime.utcnow().isoformat()})
    # Keep only last 20 runs to avoid unbounded growth
    memory["runs"] = memory["runs"][-20:]
    save_memory(memory)
