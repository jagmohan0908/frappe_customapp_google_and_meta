# Frappe Custom Apps: Google + Meta KPI

Production-ready bundle containing two Frappe apps:

- `google_ads_kpi`
- `meta_marketing_kpi`

Use this repository when handing over to another developer for live-server setup.

## What Is Included

- Both app source folders with doctypes, JS, reports, workspaces, and AI helpers.
- Live installation script: `deploy/live_install.sh`
- Post-install verification script: `deploy/verify_install.sh`
- Site config template for AI and workers: `deploy/site_config.example.json`
- Sample import data (CSV): `samples/`

## Server Compatibility

- Frappe `15.x` or `16.x`
- ERPNext recommended (both apps are KPI-focused; Google app references ERPNext entities in some flows)
- Python dependency: `requests` (used for OpenAI calls)

## Quick Live Install

```bash
cd /home/frappe/frappe-bench
bench get-app https://github.com/jagmohan0908/frappe_customapp_google_and_meta.git --branch main
bench --site <your-site> install-app google_ads_kpi
bench --site <your-site> install-app meta_marketing_kpi
bench --site <your-site> migrate
bench build
sudo supervisorctl restart all
```

Or run the guided script:

```bash
cd /home/frappe/frappe-bench
bash apps/frappe_customapp_google_and_meta/deploy/live_install.sh <your-site> main
```

## Required AI Configuration

Both apps use OpenAI only when `openai_api_key` is available in site config.

1. Copy values from `deploy/site_config.example.json`
2. Add them into:
   - `/home/frappe/frappe-bench/sites/<your-site>/site_config.json`
3. Run:

```bash
bench --site <your-site> clear-cache
bench --site <your-site> migrate
```

If `openai_api_key` is missing, apps return fallback rule-based answers instead of model answers.

## Verification

Run smoke checks after installation:

```bash
cd /home/frappe/frappe-bench
bash apps/frappe_customapp_google_and_meta/deploy/verify_install.sh <your-site>
```

This checks:

- apps are installed
- doctypes are available
- AI endpoints are callable
- KPI rows exist (warns if no data)

## Sample Data Import

Use Data Import in Frappe to upload:

- `samples/google_ads_campaign_kpi_sample.csv` to `Google Ads Campaign KPI`
- `samples/meta_marketing_kpi_sample.csv` to `Meta Marketing KPI`

After importing, test:

- Google app: `Ask AI Campaign Analyst`
- Meta app: `Ask AI Campaign Analyst`

## Notes For Handover

- AI actions are role-protected in app code. Use a user with `System Manager` role for AI operations.
- Ensure outbound HTTPS to `https://api.openai.com` is allowed on the live server.
