#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-}"
BRANCH="${2:-main}"
REPO_URL="https://github.com/jagmohan0908/frappe_customapp_google_and_meta.git"
APP_ALIAS="frappe_customapp_google_and_meta"

if [[ -z "$SITE_NAME" ]]; then
  echo "Usage: bash deploy/live_install.sh <site-name> [branch]"
  exit 1
fi

if ! command -v bench >/dev/null 2>&1; then
  echo "Error: bench command not found."
  exit 1
fi

echo "==> Installing bundle app source from ${REPO_URL} (${BRANCH})"
if [[ ! -d "apps/${APP_ALIAS}" ]]; then
  bench get-app "$REPO_URL" --branch "$BRANCH"
else
  echo "apps/${APP_ALIAS} already exists; skipping get-app."
fi

echo "==> Ensuring python dependency requests"
./env/bin/pip install requests

echo "==> Installing Google Ads KPI on ${SITE_NAME}"
bench --site "$SITE_NAME" install-app google_ads_kpi || true

echo "==> Installing Meta Marketing KPI on ${SITE_NAME}"
bench --site "$SITE_NAME" install-app meta_marketing_kpi || true

echo "==> Running migration and build"
bench --site "$SITE_NAME" migrate
bench build
bench --site "$SITE_NAME" clear-cache

echo "==> Restarting processes"
if command -v supervisorctl >/dev/null 2>&1; then
  supervisorctl restart all || true
else
  bench restart || true
fi

echo
echo "Installation complete for site: ${SITE_NAME}"
echo "Next: update sites/${SITE_NAME}/site_config.json using deploy/site_config.example.json"
echo "Then run: bash apps/${APP_ALIAS}/deploy/verify_install.sh ${SITE_NAME}"
