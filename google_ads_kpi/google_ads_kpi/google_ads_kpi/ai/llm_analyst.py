from __future__ import annotations

from statistics import mean

import frappe
import requests
from frappe.utils import flt


def _ensure_solution_prefix(text: str) -> str:
    out = (text or "").strip()
    if not out:
        return "Here is the solution:\nNo answer returned."
    if out.lower().startswith("here is the solution:"):
        return out
    return f"Here is the solution:\n{out}"


def generate_summary(forecasts: list[dict], alerts: list[dict], recommendations: list[dict]) -> dict:
    avg_roas = round(mean([flt(item.get("predicted_roas")) for item in forecasts]), 3) if forecasts else 0
    high_alerts = [item for item in alerts if item.get("severity") == "high"]
    top_actions = recommendations[:3]

    lines = [
        f"Forecast baseline ROAS across active campaigns is {avg_roas}.",
        f"{len(alerts)} anomalies detected, including {len(high_alerts)} high-severity signals.",
        f"Top recommendation count: {len(top_actions)} actions prioritized for immediate review.",
    ]
    return {
        "headline": "AI Performance Brief",
        "narrative": " ".join(lines),
        "top_actions": top_actions,
    }


def answer_question(question: str, context: dict) -> dict:
    ai_answer = _answer_with_openai(question, context, "You are a Google Ads KPI analyst.")
    if ai_answer:
        return ai_answer

    q = (question or "").lower()
    if "roas" in q and "drop" in q:
        return {
            "answer": _ensure_solution_prefix(
                "ROAS drop is usually tied to conversion-rate decline or sudden CPC increase. "
                "Check campaigns in current high-severity anomaly list first, then reduce wasted spend "
                "by tightening targeting and pausing low-converting assets."
            ),
            "confidence": 0.76,
        }
    if "budget" in q and ("increase" in q or "shift" in q):
        return {
            "answer": _ensure_solution_prefix(
                "Increase budget first for campaigns with high predicted ROAS and no active cost-spike alert. "
                "Keep per-change limits within configured guardrails, and recheck CTR/CVR after 48 hours before scaling further."
            ),
            "confidence": 0.81,
        }
    return {
        "answer": _ensure_solution_prefix(
            "Use the recommendation list sorted by priority and expected lift, then approve guarded actions in workflow mode. "
            "Start with one high-confidence change, measure impact, and roll out gradually."
        ),
        "confidence": 0.64,
    }


def answer_contextual_question(question: str, context: dict, role_hint: str) -> dict:
    ai_answer = _answer_with_openai(question, context, role_hint)
    if ai_answer:
        return ai_answer
    return {
        "answer": _ensure_solution_prefix(
            "Not enough signal from current context. Check recent cost, conversions, CTR, and conversion-rate trends before deciding. "
            "Then test one controlled change in budget, audience, or ad creative and compare 7-day results."
        ),
        "confidence": 0.58,
    }


def _answer_with_openai(question: str, context: dict, role_hint: str) -> dict | None:
    api_key = frappe.conf.get("openai_api_key")
    if not api_key:
        return None

    prompt = (
        f"{role_hint} Answer using only the provided KPI context. "
        "Do not give generic advice. Use campaign-specific numbers from context and mention at least 3 metrics. "
        "ALWAYS start with: 'Here is the solution:' and format in markdown with sections:\n"
        "### Verdict\n### Why (with metrics)\n### Action Plan (3-5 bullet steps)\n### Next Checkpoint\n"
        "If data is missing, explicitly state which metric is unavailable."
        f"\nQuestion: {question}"
        f"\nContext: {context}"
    )

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=20,
        )
        response.raise_for_status()
        body = response.json()
        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return None
        return {"answer": _ensure_solution_prefix(content), "confidence": 0.86}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "OpenAI analyst call failed")
        return None

