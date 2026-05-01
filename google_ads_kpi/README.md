### Google Ads KPI

Google Ads integration

### AI Capabilities (Advanced Roadmap Implementation)

This app now includes a built-in AI layer for advanced KPI operations:

- Data quality checks and training dataset generation from campaign KPI history.
- Feature engineering with lag/rolling metrics for forecasting and diagnostics.
- Anomaly detection for cost spikes, CTR drop, and conversion-rate collapse.
- 7/14/30 style forecasting primitives for spend, conversions, and ROAS.
- Ranked recommendation engine with expected lift, confidence, and risk.
- LLM-style analyst summary + Q&A endpoints for natural-language insight.
- Human-in-the-loop workflow with recommendation status (`Draft -> Approved -> Applied/Rejected`).
- Guarded automation controls and audit logging via dedicated doctypes.

### New DocTypes

- `Google Ads AI Settings` (Single): objectives, risk tolerance, and guardrails.
- `Google Ads AI Recommendation`: generated actions and review workflow.
- `Google Ads AI Audit Log`: approval/apply/reject history.

### Key API Methods

These whitelisted methods can be called from desk scripts or integrations:

- `google_ads_kpi.google_ads_kpi.ai.api.run_ai_pipeline`
- `google_ads_kpi.google_ads_kpi.ai.api.ask_ai_analyst`
- `google_ads_kpi.google_ads_kpi.ai.api.approve_recommendation`
- `google_ads_kpi.google_ads_kpi.ai.api.reject_recommendation`
- `google_ads_kpi.google_ads_kpi.ai.api.apply_recommendation`

### Scheduled Automation

- Daily scheduler job: `google_ads_kpi.google_ads_kpi.tasks.daily_ai_refresh`

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app google_ads_kpi
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/google_ads_kpi
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
