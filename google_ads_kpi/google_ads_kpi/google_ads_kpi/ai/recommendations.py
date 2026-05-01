from __future__ import annotations

from frappe.utils import flt

from google_ads_kpi.google_ads_kpi.ai.constants import (
    DEFAULT_OBJECTIVE,
    DEFAULT_RISK_TOLERANCE,
    RISK_TOLERANCE_MULTIPLIER,
)


def load_ai_settings() -> dict:
    if not __import__("frappe").frappe.db.exists("DocType", "Google Ads AI Settings"):
        return {"objective": DEFAULT_OBJECTIVE, "risk_tolerance": DEFAULT_RISK_TOLERANCE}
    settings = __import__("frappe").frappe.get_single("Google Ads AI Settings")
    return {
        "objective": settings.objective or DEFAULT_OBJECTIVE,
        "risk_tolerance": settings.risk_tolerance or DEFAULT_RISK_TOLERANCE,
        "max_budget_increase_percent": flt(settings.max_budget_increase_percent or 20),
        "max_bid_change_percent": flt(settings.max_bid_change_percent or 15),
        "minimum_data_days": settings.minimum_data_days or 14,
        "auto_execution_enabled": settings.auto_execution_enabled,
    }


def _recommendation_from_alert(alert: dict, settings: dict) -> dict:
    risk_factor = RISK_TOLERANCE_MULTIPLIER.get(settings.get("risk_tolerance"), 1.0)
    action = "review"
    impact = 0.0
    reason = "Manual review suggested."
    if alert.get("alert_type") == "cost_spike":
        action = "reduce_bid"
        impact = 0.08 * risk_factor
        reason = "Cost spike with unstable efficiency; reduce bids to control burn."
    elif alert.get("alert_type") == "conversion_rate_drop":
        action = "pause_low_quality_terms"
        impact = 0.12 * risk_factor
        reason = "CVR dropped; likely poor intent traffic or weak landing relevance."
    elif alert.get("alert_type") == "ctr_drop":
        action = "refresh_ad_copy"
        impact = 0.06 * risk_factor
        reason = "CTR downtrend points to ad fatigue or weaker message-match."

    return {
        "campaign_id": alert.get("campaign_id"),
        "campaign_name": alert.get("campaign_name"),
        "priority": "P1" if alert.get("severity") == "high" else "P2",
        "action_type": action,
        "expected_lift_percent": round(impact * 100, 2),
        "risk_score": round((1.0 / risk_factor) * (0.8 if alert.get("severity") == "high" else 0.5), 2),
        "confidence_score": 0.82 if alert.get("severity") == "high" else 0.7,
        "evidence": alert.get("message"),
        "status": "Draft",
        "reason": reason,
    }


def rank_recommendations(alerts: list[dict]) -> list[dict]:
    settings = load_ai_settings()
    recommendations = [_recommendation_from_alert(alert, settings) for alert in alerts]
    recommendations.sort(
        key=lambda item: (
            0 if item.get("priority") == "P1" else 1,
            -flt(item.get("expected_lift_percent")),
            -flt(item.get("confidence_score")),
        )
    )
    return recommendations

