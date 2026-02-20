"""
Correlation ID (run_id) generator and propagation.

Every user-initiated action (shock inject, analysis, risk, test) gets a run_id.
Every market tick also gets a run_id.
run_id is propagated into Datadog tags, events, and API responses.
"""

import uuid
import contextvars
import logging

logger = logging.getLogger(__name__)

_current_run_id: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="")


def new_run_id(prefix: str = "run") -> str:
    """Generate a short, prefixed correlation ID."""
    rid = f"{prefix}-{uuid.uuid4().hex[:12]}"
    _current_run_id.set(rid)
    return rid


def get_run_id() -> str:
    return _current_run_id.get()


def set_run_id(rid: str) -> None:
    _current_run_id.set(rid)


def run_id_tags() -> list[str]:
    """Return run_id as a Datadog tag list (empty if no active run_id)."""
    rid = _current_run_id.get()
    return [f"run_id:{rid}"] if rid else []
