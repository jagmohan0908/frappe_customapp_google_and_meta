from __future__ import annotations

import frappe

from google_ads_kpi.google_ads_kpi.ai.api import run_ai_pipeline


def daily_ai_refresh() -> None:
    """Run daily AI generation in read-only guard mode."""
    try:
        run_ai_pipeline(days=180, horizon_days=7, persist_recommendations=1)
        frappe.logger().info("Google Ads KPI AI pipeline refreshed successfully.")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Google Ads KPI AI refresh failed")

