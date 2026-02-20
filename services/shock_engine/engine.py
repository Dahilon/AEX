import uuid
import logging
from services.market_engine.models import SignalEvent, ShockEvent, ShockType

logger = logging.getLogger(__name__)

# Maps signal source + type → likely shock type
SIGNAL_TO_SHOCK_MAP: dict[str, ShockType] = {
    "REGULATION": ShockType.REGULATION,
    "SANCTIONS":  ShockType.SANCTIONS,
    "CYBER":      ShockType.CYBER,
    "HACK":       ShockType.CYBER,
    "EARTHQUAKE": ShockType.EARTHQUAKE,
    "FX_MOVE":    ShockType.FX_SHOCK,
}

# GDELT themes → shock type keywords
GDELT_THEME_MAP: dict[str, ShockType] = {
    "TAX":        ShockType.REGULATION,
    "REGULATION": ShockType.REGULATION,
    "SANCTION":   ShockType.SANCTIONS,
    "CYBER":      ShockType.CYBER,
    "HACK":       ShockType.CYBER,
    "ECON":       ShockType.FX_SHOCK,
}


def convert_signal_to_shock(signal: SignalEvent) -> ShockEvent | None:
    """
    Convert a normalized SignalEvent into a ShockEvent.
    Returns None if the signal doesn't warrant a shock (severity too low).

    TODO (Person A):
    - Parse signal.metadata for GDELT themes, USGS magnitude, FX delta_pct
    - Map to shock type using SIGNAL_TO_SHOCK_MAP or GDELT_THEME_MAP
    - Compute severity from signal.severity_hint + metadata
    - Return ShockEvent or None
    """
    MIN_SEVERITY = 0.15

    if signal.severity_hint < MIN_SEVERITY:
        logger.debug(f"Signal {signal.signal_id} below severity threshold, skipping")
        return None

    shock_type = _resolve_shock_type(signal)
    if shock_type is None:
        return None

    description = _build_description(signal)

    return ShockEvent(
        shock_id=str(uuid.uuid4())[:8],
        shock_type=shock_type,
        severity=min(1.0, signal.severity_hint),
        description=description,
        timestamp=signal.timestamp,
        source=signal.source,
    )


def _resolve_shock_type(signal: SignalEvent) -> ShockType | None:
    """Determine shock type from signal metadata."""
    # Direct type mapping
    direct = SIGNAL_TO_SHOCK_MAP.get(signal.signal_type.upper())
    if direct:
        return direct

    # GDELT theme-based mapping
    themes: list[str] = signal.metadata.get("themes", [])
    for theme in themes:
        for keyword, shock_type in GDELT_THEME_MAP.items():
            if keyword in theme.upper():
                return shock_type

    # FX source fallback
    if signal.source == "FX":
        return ShockType.FX_SHOCK

    # USGS always earthquake
    if signal.source == "USGS":
        return ShockType.EARTHQUAKE

    logger.debug(f"Could not resolve shock type for signal {signal.signal_id}")
    return None


def _build_description(signal: SignalEvent) -> str:
    if signal.source == "GDELT":
        return signal.metadata.get("title", "News event detected")
    if signal.source == "USGS":
        mag = signal.metadata.get("magnitude", "?")
        loc = signal.metadata.get("location", "unknown region")
        return f"M{mag} earthquake near {loc}"
    if signal.source == "FX":
        pair = signal.metadata.get("pair", "USD/EUR")
        delta = signal.metadata.get("delta_pct", 0)
        return f"FX spike: {pair} moved {delta:+.2f}%"
    return "External signal event"
