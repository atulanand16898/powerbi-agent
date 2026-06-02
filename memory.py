"""
Disk-based session memory for the Power BI Specialist Agent.
Conversations are saved as JSON files under ./sessions/
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path(__file__).parent / "sessions"


def _ensure_dir():
    SESSIONS_DIR.mkdir(exist_ok=True)


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]


def save_session(session_id: str, messages: list, title: str = "") -> None:
    """Persist a conversation to disk."""
    _ensure_dir()
    path = SESSIONS_DIR / f"{session_id}.json"
    data = {
        "session_id": session_id,
        "title": title or _auto_title(messages),
        "updated_at": datetime.now().isoformat(),
        "messages": messages,
    }
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_session(session_id: str) -> dict | None:
    """Load a saved session. Returns None if not found."""
    _ensure_dir()
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions() -> list[dict]:
    """Return metadata for all saved sessions, newest first."""
    _ensure_dir()
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data["session_id"],
                "title": data.get("title", "Untitled"),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", [])),
            })
        except Exception:
            continue
    return sessions


def delete_session(session_id: str) -> bool:
    """Delete a session file. Returns True if deleted."""
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def _auto_title(messages: list) -> str:
    """Generate a title from the first user message."""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content[:60] + ("..." if len(content) > 60 else "")
    return "New conversation"
