"""
Signal replay loader.
Reads pre-captured signals from a JSON file (local or S3).
Used when SIGNAL_MODE=replay.

See docs/DATA_SOURCES.md for the curated demo snapshot format.
"""

import json
import os
import time
import uuid
import logging
from pathlib import Path

from backend.services.market_engine.models import SignalEvent

logger = logging.getLogger(__name__)

# Default curated snapshot bundled with the repo for offline demo
DEFAULT_SNAPSHOT_PATH = Path(__file__).parent / "demo_signals.json"


def load_signals_from_file(path: str | None = None) -> list[SignalEvent]:
    """Load signals from a local JSON snapshot file."""
    file_path = Path(path) if path else DEFAULT_SNAPSHOT_PATH

    if not file_path.exists():
        logger.warning(f"Snapshot file not found: {file_path}. Using built-in demo signals.")
        return _builtin_demo_signals()

    with open(file_path) as f:
        raw = json.load(f)

    signals = []
    for item in raw:
        signals.append(SignalEvent(
            signal_id=item.get("id", str(uuid.uuid4())[:8]),
            source=item["source"],
            signal_type=item["type"],
            timestamp=item.get("timestamp", time.time()),
            severity_hint=item.get("severity_hint", 0.5),
            metadata=item.get("metadata", {}),
            raw=item,
        ))
    logger.info(f"Loaded {len(signals)} signals from {file_path}")
    return signals


def _builtin_demo_signals() -> list[SignalEvent]:
    """
    Hardcoded demo signals for when no snapshot file is available.
    These produce interesting, predictable shocks for the demo.
    """
    now = time.time()
    return [
        SignalEvent(
            signal_id="demo_01",
            source="GDELT",
            signal_type="NEWS",
            timestamp=now - 600,
            severity_hint=0.72,
            metadata={
                "title": "EU AI Act enforcement begins — fines for non-compliance announced",
                "themes": ["REGULATION", "AI_GOVERNANCE"],
                "tone": -7.2,
            },
        ),
        SignalEvent(
            signal_id="demo_02",
            source="USGS",
            signal_type="EARTHQUAKE",
            timestamp=now - 300,
            severity_hint=0.55,
            metadata={
                "magnitude": 5.5,
                "location": "Near Singapore Strait",
                "lat": 1.29,
                "lon": 103.85,
            },
        ),
        SignalEvent(
            signal_id="demo_03",
            source="FX",
            signal_type="FX_MOVE",
            timestamp=now - 120,
            severity_hint=0.40,
            metadata={
                "pair": "USD/EUR",
                "delta_pct": -0.82,
                "rate": 0.918,
            },
        ),
        SignalEvent(
            signal_id="demo_04",
            source="GDELT",
            signal_type="NEWS",
            timestamp=now - 60,
            severity_hint=0.65,
            metadata={
                "title": "OFAC announces new sanctions package targeting fintech operators",
                "themes": ["SANCTIONS", "FINTECH"],
                "tone": -5.8,
            },
        ),
    ]
