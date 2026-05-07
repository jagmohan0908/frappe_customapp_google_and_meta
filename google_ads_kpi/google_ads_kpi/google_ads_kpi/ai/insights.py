from __future__ import annotations

from statistics import mean, pstdev

from frappe.utils import flt


def detect_anomalies(feature_rows: list[dict]) -> list[dict]:
    by_campaign: dict[str, list[dict]] = {}
    for row in feature_rows:
        by_campaign.setdefault(row.get("campaign_id"), []).append(row)

    alerts = []
    for campaign_id, rows in by_campaign.items():
        if len(rows) < 8:
            continue
        rows = sorted(rows, key=lambda item: item.get("date"))
        costs = [flt(item.get("cost")) for item in rows]
        cvr_values = [flt(item.get("cvr")) for item in rows]
        ctr_values = [flt(item.get("ctr")) for item in rows]

        last = rows[-1]
        base_cost_mean = mean(costs[:-1])
        base_cost_std = pstdev(costs[:-1]) if len(costs) > 2 else 0
        base_cvr_mean = mean(cvr_values[:-1])
        base_ctr_mean = mean(ctr_values[:-1])

        if base_cost_std and flt(last.get("cost")) > (base_cost_mean + 2.5 * base_cost_std):
            alerts.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": last.get("campaign_name"),
                    "date": last.get("date"),
                    "severity": "high",
                    "alert_type": "cost_spike",
                    "message": "Spend spiked significantly versus recent baseline.",
                }
            )
        if base_cvr_mean and flt(last.get("cvr")) < (base_cvr_mean * 0.65):
            alerts.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": last.get("campaign_name"),
                    "date": last.get("date"),
                    "severity": "high",
                    "alert_type": "conversion_rate_drop",
                    "message": "Conversion rate dropped sharply versus historical trend.",
                }
            )
        if base_ctr_mean and flt(last.get("ctr")) < (base_ctr_mean * 0.7):
            alerts.append(
                {
                    "campaign_id": campaign_id,
                    "campaign_name": last.get("campaign_name"),
                    "date": last.get("date"),
                    "severity": "medium",
                    "alert_type": "ctr_drop",
                    "message": "CTR is materially below baseline, review ad relevance.",
                }
            )
    return alerts


def forecast_campaigns(feature_rows: list[dict], horizon_days: int = 7) -> list[dict]:
    by_campaign: dict[str, list[dict]] = {}
    for row in feature_rows:
        by_campaign.setdefault(row.get("campaign_id"), []).append(row)

    forecasts = []
    for campaign_id, rows in by_campaign.items():
        rows = sorted(rows, key=lambda item: item.get("date"))
        recent = rows[-14:] if len(rows) >= 14 else rows
        if not recent:
            continue

        avg_cost = mean([flt(item.get("cost")) for item in recent])
        avg_conv = mean([flt(item.get("conversions")) for item in recent])
        avg_roas = mean([flt(item.get("roas")) for item in recent])
        forecasts.append(
            {
                "campaign_id": campaign_id,
                "campaign_name": rows[-1].get("campaign_name"),
                "horizon_days": horizon_days,
                "predicted_cost": round(avg_cost * horizon_days, 2),
                "predicted_conversions": round(avg_conv * horizon_days, 2),
                "predicted_roas": round(avg_roas, 3),
                "confidence": 0.78 if len(recent) >= 10 else 0.62,
            }
        )
    return forecasts

