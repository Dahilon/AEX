from services.market_engine.models import ShockType, Sector

# ── Sector Beta Matrix ────────────────────────────────────────────────────────
# How sensitive each sector is to each shock type.
# Positive = benefits from shock. Negative = hurt by shock.
# See docs/MARKET_MODEL.md for rationale.

SECTOR_BETAS: dict[ShockType, dict[Sector, float]] = {
    ShockType.REGULATION: {
        Sector.FRAUD_AML:   -0.60,   # tighter rules = harder for fraud detection biz
        Sector.COMPLIANCE:  +0.80,   # compliance agents WIN from regulation
        Sector.GEO_OSINT:  -0.20,
    },
    ShockType.CYBER: {
        Sector.FRAUD_AML:  +0.50,   # cyber incidents → demand for fraud agents
        Sector.COMPLIANCE: -0.30,
        Sector.GEO_OSINT:  +0.70,   # geo/OSINT agents track cyber threats
    },
    ShockType.FX_SHOCK: {
        Sector.FRAUD_AML:  -0.40,
        Sector.COMPLIANCE: -0.20,   # slightly resilient
        Sector.GEO_OSINT:  -0.30,
    },
    ShockType.EARTHQUAKE: {
        Sector.FRAUD_AML:  -0.20,
        Sector.COMPLIANCE: -0.10,
        Sector.GEO_OSINT:  +0.60,   # disaster = demand for geo intel
    },
    ShockType.SANCTIONS: {
        Sector.FRAUD_AML:  +0.30,
        Sector.COMPLIANCE: +0.70,   # sanctions = compliance goldmine
        Sector.GEO_OSINT:  +0.50,
    },
}

# Max single-tick impact (clamped). Shock decays over 4 ticks.
MAX_TICK_IMPACT = 0.15

# Decay schedule (fraction of original impact per tick)
DECAY_SCHEDULE = [1.0, 0.6, 0.3, 0.1]


def get_beta(shock_type: ShockType, sector: Sector) -> float:
    return SECTOR_BETAS.get(shock_type, {}).get(sector, 0.0)
