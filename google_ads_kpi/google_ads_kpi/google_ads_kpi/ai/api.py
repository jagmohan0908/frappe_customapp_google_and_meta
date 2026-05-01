from __future__ import annotations

import frappe
from frappe.utils import flt, now

from google_ads_kpi.google_ads_kpi.ai.data_pipeline import get_training_dataset
from google_ads_kpi.google_ads_kpi.ai.insights import detect_anomalies, forecast_campaigns
from google_ads_kpi.google_ads_kpi.ai.llm_analyst import (
    answer_contextual_question,
    answer_question,
    generate_summary,
)
from google_ads_kpi.google_ads_kpi.ai.recommendations import rank_recommendations


def _create_recommendation_doc(item: dict) -> str:
    doc = frappe.get_doc(
        {
            "doctype": "Google Ads AI Recommendation",
            "campaign_id": item.get("campaign_id"),
            "campaign_name": item.get("campaign_name"),
            "priority": item.get("priority"),
            "action_type": item.get("action_type"),
            "expected_lift_percent": item.get("expected_lift_percent"),
            "risk_score": item.get("risk_score"),
            "confidence_score": item.get("confidence_score"),
            "evidence": item.get("evidence"),
            "reason": item.get("reason"),
            "status": "Draft",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _create_audit_log(recommendation: str, action: str, details: str) -> None:
    audit = frappe.get_doc(
        {
            "doctype": "Google Ads AI Audit Log",
            "recommendation": recommendation,
            "action": action,
            "details": details,
            "action_time": now(),
            "actor": frappe.session.user,
        }
    )
    audit.insert(ignore_permissions=True)


@frappe.whitelist()
def run_ai_pipeline(
    days: int = 180,
    horizon_days: int = 7,
    persist_recommendations: int = 1,
    filter_mode: str = "all",
    google_ads_account: str | None = None,
    campaign_name: str | None = None,
) -> dict:
    use_filters = (filter_mode or "all") == "filtered"
    dataset = get_training_dataset(
        days=int(days),
        google_ads_account=google_ads_account if use_filters else None,
        campaign_name=campaign_name if use_filters else None,
    )
    feature_rows = dataset.get("data", [])
    alerts = detect_anomalies(feature_rows)
    forecasts = forecast_campaigns(feature_rows, horizon_days=int(horizon_days))
    recommendations = rank_recommendations(alerts)
    saved = []
    if int(persist_recommendations):
        for item in recommendations:
            saved.append(_create_recommendation_doc(item))
    summary = generate_summary(forecasts, alerts, recommendations)
    return {
        "filter_mode": "filtered" if use_filters else "all",
        "dataset_meta": dataset.get("meta"),
        "alerts": alerts,
        "forecasts": forecasts,
        "recommendations": recommendations,
        "saved_recommendations": saved,
        "summary": summary,
    }


@frappe.whitelist()
def ask_ai_analyst(question: str) -> dict:
    pipeline = run_ai_pipeline(days=90, horizon_days=7, persist_recommendations=0)
    return answer_question(question, pipeline)


@frappe.whitelist()
def smoke_ai_analyst() -> dict:
    return ask_ai_analyst("Why did ROAS drop yesterday?")


@frappe.whitelist()
def create_sample_recommendations() -> dict:
    samples = [
        {
            "campaign_id": "SAMPLE-1001",
            "campaign_name": "Sample Campaign Approved",
            "priority": "P1",
            "action_type": "reduce_bid",
            "expected_lift_percent": 9.5,
            "risk_score": 0.5,
            "confidence_score": 0.86,
            "evidence": "Sample alert: cost spike with weak conversion trend.",
            "reason": "Demonstration record for approval flow.",
            "status": "Draft",
        },
        {
            "campaign_id": "SAMPLE-1002",
            "campaign_name": "Sample Campaign Rejected",
            "priority": "P2",
            "action_type": "refresh_ad_copy",
            "expected_lift_percent": 6.2,
            "risk_score": 0.42,
            "confidence_score": 0.78,
            "evidence": "Sample alert: CTR downtrend in last 7 days.",
            "reason": "Demonstration record for rejection flow.",
            "status": "Draft",
        },
    ]
    names = [_create_recommendation_doc(item) for item in samples]
    return {"recommendations": names}


@frappe.whitelist()
def get_ai_verification_snapshot() -> dict:
    recommendations = frappe.get_all(
        "Google Ads AI Recommendation",
        fields=["name", "campaign_id", "status", "reviewer_notes"],
        order_by="creation desc",
        limit=10,
    )
    audit_logs = frappe.get_all(
        "Google Ads AI Audit Log",
        fields=["name", "recommendation", "action", "details", "actor"],
        order_by="creation desc",
        limit=20,
    )
    return {"recommendations": recommendations, "audit_logs": audit_logs}


@frappe.whitelist()
def run_sample_audit_flow() -> dict:
    approved = frappe.db.get_value(
        "Google Ads AI Recommendation",
        {"campaign_id": "SAMPLE-1001"},
        "name",
    )
    rejected = frappe.db.get_value(
        "Google Ads AI Recommendation",
        {"campaign_id": "SAMPLE-1002"},
        "name",
    )
    out = {}
    if approved:
        out["approved"] = approve_recommendation(approved, "Approved via UI test flow")
    if rejected:
        out["rejected"] = reject_recommendation(rejected, "Rejected via UI test flow")
    out["snapshot"] = get_ai_verification_snapshot()
    return out


@frappe.whitelist()
def approve_recommendation(recommendation_name: str, notes: str | None = None) -> dict:
    rec = frappe.get_doc("Google Ads AI Recommendation", recommendation_name)
    rec.status = "Approved"
    rec.reviewer_notes = notes
    rec.save(ignore_permissions=True)
    _create_audit_log(rec.name, "approve", notes or "Approved by reviewer")
    return {"name": rec.name, "status": rec.status}


@frappe.whitelist()
def reject_recommendation(recommendation_name: str, notes: str | None = None) -> dict:
    rec = frappe.get_doc("Google Ads AI Recommendation", recommendation_name)
    rec.status = "Rejected"
    rec.reviewer_notes = notes
    rec.save(ignore_permissions=True)
    _create_audit_log(rec.name, "reject", notes or "Rejected by reviewer")
    return {"name": rec.name, "status": rec.status}


@frappe.whitelist()
def apply_recommendation(recommendation_name: str) -> dict:
    rec = frappe.get_doc("Google Ads AI Recommendation", recommendation_name)
    settings = frappe.get_single("Google Ads AI Settings")
    if not settings.auto_execution_enabled:
        frappe.throw("Auto execution is disabled. Enable it in Google Ads AI Settings.")
    if rec.status != "Approved":
        frappe.throw("Only approved recommendations can be applied.")

    rec.status = "Applied"
    rec.applied_on = now()
    rec.save(ignore_permissions=True)
    _create_audit_log(rec.name, "apply", "Marked as applied (guarded workflow).")
    return {"name": rec.name, "status": rec.status}


@frappe.whitelist()
def configure_ai_settings(
    objective: str = "maximize_roas",
    risk_tolerance: str = "medium",
    auto_execution_enabled: int = 0,
) -> dict:
    settings = frappe.get_single("Google Ads AI Settings")
    settings.objective = objective
    settings.risk_tolerance = risk_tolerance
    settings.auto_execution_enabled = int(auto_execution_enabled)
    settings.save(ignore_permissions=True)
    return {
        "objective": settings.objective,
        "risk_tolerance": settings.risk_tolerance,
        "auto_execution_enabled": settings.auto_execution_enabled,
    }


@frappe.whitelist()
def get_kpi_filter_options() -> dict:
    account_rows = frappe.get_all(
        "Google Ads Campaign KPI",
        fields=["google_ads_account"],
        filters={"google_ads_account": ["is", "set"]},
        group_by="google_ads_account",
        order_by="google_ads_account asc",
    )
    campaign_rows = frappe.get_all(
        "Google Ads Campaign KPI",
        fields=["campaign_name"],
        filters={"campaign_name": ["is", "set"]},
        group_by="campaign_name",
        order_by="campaign_name asc",
    )
    return {
        "google_ads_accounts": [row.get("google_ads_account") for row in account_rows if row.get("google_ads_account")],
        "campaign_names": [row.get("campaign_name") for row in campaign_rows if row.get("campaign_name")],
    }


@frappe.whitelist()
def ask_recommendation_ai(recommendation_name: str, question: str) -> dict:
    rec = frappe.get_doc("Google Ads AI Recommendation", recommendation_name)
    context = {
        "recommendation_name": rec.name,
        "campaign_id": rec.campaign_id,
        "campaign_name": rec.campaign_name,
        "priority": rec.priority,
        "action_type": rec.action_type,
        "expected_lift_percent": rec.expected_lift_percent,
        "risk_score": rec.risk_score,
        "confidence_score": rec.confidence_score,
        "status": rec.status,
        "evidence": rec.evidence,
        "reason": rec.reason,
    }
    return answer_contextual_question(question, context, "You are a Google Ads recommendation analyst.")


@frappe.whitelist()
def ask_campaign_ai(
    campaign_name: str,
    question: str,
    google_ads_account: str | None = None,
    days: int = 60,
) -> dict:
    filters = {"campaign_name": campaign_name}
    if google_ads_account:
        filters["google_ads_account"] = google_ads_account

    rows = frappe.get_all(
        "Google Ads Campaign KPI",
        fields=["date", "google_ads_account", "campaign_id", "campaign_name", "impressions", "clicks", "cost", "conversions", "revenue"],
        filters=filters,
        order_by="date desc",
        limit=max(14, int(days)),
    )
    if not rows:
        frappe.throw("No Google Ads campaign KPI records found for the selected campaign/account.")

    recent = rows[:7]
    previous = rows[7:14]

    def aggregate(items: list[dict]) -> dict:
        impressions = sum(flt(item.get("impressions")) for item in items)
        clicks = sum(flt(item.get("clicks")) for item in items)
        cost = sum(flt(item.get("cost")) for item in items)
        conversions = sum(flt(item.get("conversions")) for item in items)
        revenue = sum(flt(item.get("revenue")) for item in items)
        return {
            "impressions": impressions,
            "clicks": clicks,
            "cost": round(cost, 2),
            "conversions": round(conversions, 2),
            "revenue": round(revenue, 2),
            "ctr": round((clicks / impressions) * 100, 3) if impressions else 0,
            "cvr": round((conversions / clicks) * 100, 3) if clicks else 0,
            "roas": round((revenue / cost), 3) if cost else 0,
            "cpa": round((cost / conversions), 2) if conversions else 0,
        }

    recent_summary = aggregate(recent)
    previous_summary = aggregate(previous) if previous else {}
    deltas = {}
    if previous_summary:
        for key in ("impressions", "clicks", "cost", "conversions", "revenue", "ctr", "cvr", "roas", "cpa"):
            deltas[key] = round(flt(recent_summary.get(key)) - flt(previous_summary.get(key)), 3)

    latest_points = [
        {
            "date": row.get("date"),
            "impressions": flt(row.get("impressions")),
            "clicks": flt(row.get("clicks")),
            "cost": round(flt(row.get("cost")), 2),
            "conversions": round(flt(row.get("conversions")), 2),
            "revenue": round(flt(row.get("revenue")), 2),
        }
        for row in rows[:14]
    ]

    context = {
        "campaign_name": campaign_name,
        "google_ads_account": google_ads_account,
        "records_used": len(rows),
        "recent_7_days": recent_summary,
        "previous_7_days": previous_summary,
        "delta_recent_vs_previous": deltas,
        "latest_daily_points": latest_points,
    }
    return answer_contextual_question(question, context, "You are a senior Google Ads campaign performance analyst.")

