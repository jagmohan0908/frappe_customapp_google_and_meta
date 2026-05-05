#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-}"

if [[ -z "$SITE_NAME" ]]; then
  echo "Usage: bash deploy/verify_install.sh <site-name>"
  exit 1
fi

echo "==> Installed apps"
bench --site "$SITE_NAME" list-apps

echo
echo "==> Verifying doctypes exist"
bench --site "$SITE_NAME" execute frappe.db.exists --kwargs "{'doctype':'DocType','filters':'Google Ads Campaign KPI'}"
bench --site "$SITE_NAME" execute frappe.db.exists --kwargs "{'doctype':'DocType','filters':'Meta Marketing KPI'}"

echo
echo "==> Checking basic AI endpoint calls (permission depends on current user context)"
bench --site "$SITE_NAME" execute google_ads_kpi.google_ads_kpi.ai.api.get_kpi_filter_options
bench --site "$SITE_NAME" execute meta_marketing_kpi.meta_marketing_kpi.ai.api.get_meta_filter_options

echo
echo "==> Checking data presence"
bench --site "$SITE_NAME" execute frappe.db.count --kwargs "{'doctype':'Google Ads Campaign KPI'}"
bench --site "$SITE_NAME" execute frappe.db.count --kwargs "{'doctype':'Meta Marketing KPI'}"

echo
echo "If counts are 0, import sample CSVs from apps/frappe_customapp_google_and_meta/samples/"
