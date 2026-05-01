from __future__ import annotations

DEFAULT_OBJECTIVE = "maximize_roas"
DEFAULT_RISK_TOLERANCE = "medium"

OBJECTIVE_OPTIONS = {
    "maximize_roas": "Maximize ROAS",
    "maximize_conversions": "Maximize Conversions",
    "balanced_growth": "Balanced Growth",
}

RISK_TOLERANCE_MULTIPLIER = {
    "low": 0.6,
    "medium": 1.0,
    "high": 1.4,
}

