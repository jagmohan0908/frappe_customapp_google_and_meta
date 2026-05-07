from __future__ import annotations

from collections import defaultdict
from statistics import mean

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate


def fetch_campaign_rows(
    days: int = 90,
    google_ads_account: str | None = None,
    campaign_name: str | None = None,
) -> list[dict]:
    from_date = add_days(nowdate(), -abs(days))
    filters: dict = {"date": [">=", from_date]}
    if google_ads_account:
        filters["google_ads_account"] = google_ads_account
    if campaign_name:
        # Partial match helps users get a specific report quickly.
        filters["campaign_name"] = ["like", f"%{campaign_name}%"]

    return frappe.get_all(
        "Google Ads Campaign KPI",
        fields=[
            "name",
            "date",
            "google_ads_account",
            "campaign_id",
            "campaign_name",
            "impressions",
            "clicks",
            "cost",
            "conversions",
            "revenue",
        ],
        filters=filters,
        order_by="date asc",
    )


def validate_campaign_rows(rows: list[dict]) -> dict:
    duplicate_guard: set[tuple] = set()
    issues = {
        "missing_required": 0,
        "invalid_values": 0,
        "duplicates": 0,
        "valid_rows": 0,
    }
    required = ("date", "campaign_id", "cost", "clicks", "impressions")
    for row in rows:
        key = (row.get("date"), row.get("campaign_id"), row.get("google_ads_account"))
        if key in duplicate_guard:
            issues["duplicates"] += 1
            continue
        duplicate_guard.add(key)
        if any(row.get(field) in (None, "") for field in required):
            issues["missing_required"] += 1
            continue
        if flt(row.get("cost")) < 0 or flt(row.get("clicks")) < 0 or flt(row.get("impressions")) < 0:
            issues["invalid_values"] += 1
            continue
        issues["valid_rows"] += 1
    return issues


def build_feature_store(rows: list[dict]) -> dict[str, list[dict]]:
    by_campaign: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_campaign[row.get("campaign_id")].append(row)

    feature_store: dict[str, list[dict]] = {}
    for campaign_id, campaign_rows in by_campaign.items():
        campaign_rows.sort(key=lambda item: getdate(item.get("date")))
        features = []
        for idx, row in enumerate(campaign_rows):
            history = campaign_rows[max(0, idx - 30) : idx]
            last7 = history[-7:]
            last30 = history[-30:]
            cost = flt(row.get("cost"))
            conversions = flt(row.get("conversions"))
            clicks = flt(row.get("clicks"))
            impressions = flt(row.get("impressions"))
            ctr = (clicks / impressions) if impressions else 0
            cvr = (conversions / clicks) if clicks else 0
            roas = (flt(row.get("revenue")) / cost) if cost else 0
            features.append(
                {
                    "date": row.get("date"),
                    "campaign_id": campaign_id,
                    "campaign_name": row.get("campaign_name"),
                    "cost": cost,
                    "conversions": conversions,
                    "roas": roas,
                    "ctr": ctr,
                    "cvr": cvr,
                    "lag_cost_d1": flt(history[-1].get("cost")) if history else 0,
                    "lag_conversions_d1": flt(history[-1].get("conversions")) if history else 0,
                    "ma_cost_d7": mean([flt(item.get("cost")) for item in last7]) if last7 else 0,
                    "ma_cost_d30": mean([flt(item.get("cost")) for item in last30]) if last30 else 0,
                    "ma_conv_d7": mean([flt(item.get("conversions")) for item in last7]) if last7 else 0,
                    "ma_roas_d7": mean(
                        [
                            (flt(item.get("revenue")) / flt(item.get("cost")))
                            for item in last7
                            if flt(item.get("cost"))
                        ]
                    )
                    if last7
                    else 0,
                }
            )
        feature_store[campaign_id] = features
    return feature_store


def get_training_dataset(
    days: int = 180,
    google_ads_account: str | None = None,
    campaign_name: str | None = None,
) -> dict:
    days = cint(days) or 180
    rows = fetch_campaign_rows(
        days=days,
        google_ads_account=(google_ads_account or "").strip() or None,
        campaign_name=(campaign_name or "").strip() or None,
    )
    validation = validate_campaign_rows(rows)
    feature_store = build_feature_store(rows)
    flattened = [item for campaign_items in feature_store.values() for item in campaign_items]
    return {
        "meta": {
            "window_days": days,
            "rows": len(rows),
            "feature_rows": len(flattened),
            "campaigns": len(feature_store),
            "google_ads_account_filter": google_ads_account,
            "campaign_name_filter": campaign_name,
            "quality": validation,
        },
        "data": flattened,
    }

