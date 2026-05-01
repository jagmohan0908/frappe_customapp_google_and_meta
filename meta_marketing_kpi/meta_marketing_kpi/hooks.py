app_name = "meta_marketing_kpi"
app_title = "Meta Marketing KPI"
app_publisher = "SAI"
app_description = "Meta marketing KPI dashboard for ERPNext"
app_email = "sai@example.com"
app_license = "mit"

fixtures = [
    {
        "dt": "Workspace",
        "filters": [["module", "=", "Meta Marketing KPI"]],
    },
    {
        "dt": "Report",
        "filters": [["module", "=", "Meta Marketing KPI"]],
    },
]

doctype_js = {
    "Meta Marketing KPI": "meta_marketing_kpi/doctype/meta_marketing_kpi/meta_marketing_kpi.js",
}

doctype_list_js = {
    "Meta Marketing KPI": "meta_marketing_kpi/doctype/meta_marketing_kpi/meta_marketing_kpi_list.js",
}
