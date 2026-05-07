# Google Ads KPI AI Guide

This guide explains exactly what to do next from your current state.

## 1) Open the AI settings page

In Frappe Desk:

1. Open Awesome Bar (`Ctrl + G`).
2. Search `Google Ads AI Settings`.
3. Open the record.

Set values:

- `Objective`: `maximize_roas`
- `Risk Tolerance`: `medium`
- `Max Budget Increase Percent`: `20`
- `Max Bid Change Percent`: `15`
- `Minimum Data Days`: `14`
- `Auto Execution Enabled`: OFF (manual approval mode)

Click `Save`.

## 2) Run AI pipeline to generate insights

From terminal:

```bash
bench --site site1.local execute google_ads_kpi.google_ads_kpi.ai.api.run_ai_pipeline
```

What this does:

- Reads campaign KPI data
- Runs data quality checks
- Builds features
- Detects anomalies
- Creates forecasts
- Generates recommendations

## 3) Review recommendations in UI

1. Open Awesome Bar (`Ctrl + G`).
2. Search `Google Ads AI Recommendation`.
3. Open the list.
4. Open each recommendation and review:
   - `Priority`
   - `Expected Lift Percent`
   - `Risk Score`
   - `Confidence Score`
   - `Evidence`
   - `Reason`

## 4) Approve or reject recommendations

Inside each recommendation record:

1. Change `Status`:
   - `Approved` for accepted actions
   - `Rejected` for declined actions
2. Add `Reviewer Notes`.
3. Click `Save`.

## 5) Verify audit trail

1. Open Awesome Bar (`Ctrl + G`).
2. Search `Google Ads AI Audit Log`.
3. Confirm entries show:
   - `Recommendation`
   - `Action` (`approve` / `reject` / `apply`)
   - `Actor`
   - `Action Time`

## 6) Ask AI analyst questions

Use terminal:

```bash
bench --site site1.local execute google_ads_kpi.google_ads_kpi.ai.api.smoke_ai_analyst
```

This returns an AI-generated answer and confidence score.

## 7) Daily operating routine

Do this every day:

1. Run pipeline.
2. Open recommendations.
3. Approve/reject.
4. Check audit log.
5. Track outcomes in campaign performance.

## Useful commands

Run AI pipeline:

```bash
bench --site site1.local execute google_ads_kpi.google_ads_kpi.ai.api.run_ai_pipeline
```

Create sample recommendations (testing only):

```bash
bench --site site1.local execute google_ads_kpi.google_ads_kpi.ai.api.create_sample_recommendations
```

Run sample approve/reject + snapshot (testing only):

```bash
bench --site site1.local execute google_ads_kpi.google_ads_kpi.ai.api.run_sample_audit_flow
```

---

If recommendations are empty, it usually means no anomalies were detected in the current window. In that case, keep running daily and tune thresholds later based on real campaign volatility.
