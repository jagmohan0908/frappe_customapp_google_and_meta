import frappe

def create_doctypes():
    module_name = "Google Ads KPI"
    
    # Ensure module exists
    if not frappe.db.exists("Module Def", module_name):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": "google_ads_kpi"
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    doctypes_to_create = [
        {
            "name": "Google Ads Campaign KPI",
            "fields": [
                {"fieldname": "date", "label": "Date", "fieldtype": "Date", "reqd": 1, "in_list_view": 1},
                {"fieldname": "campaign_id", "label": "Campaign ID", "fieldtype": "Data", "reqd": 1},
                {"fieldname": "campaign_name", "label": "Campaign Name", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "impressions", "label": "Impressions", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "clicks", "label": "Clicks", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "cost", "label": "Cost", "fieldtype": "Currency", "in_list_view": 1},
                {"fieldname": "conversions", "label": "Conversions", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "revenue", "label": "Revenue", "fieldtype": "Currency"},
                {"fieldname": "source", "label": "Source", "fieldtype": "Link", "options": "SR Lead Source", "in_list_view": 1}
            ]
        },
        {
            "name": "Google Ads Ad KPI",
            "fields": [
                {"fieldname": "date", "label": "Date", "fieldtype": "Date", "in_list_view": 1},
                {"fieldname": "ad_id", "label": "Ad ID", "fieldtype": "Data", "reqd": 1},
                {"fieldname": "campaign_name", "label": "Campaign Name", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "ad_group", "label": "Ad Group", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "impressions", "label": "Impressions", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "clicks", "label": "Clicks", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "cost", "label": "Cost", "fieldtype": "Currency", "in_list_view": 1},
                {"fieldname": "conversions", "label": "Conversions", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "source", "label": "Source", "fieldtype": "Link", "options": "SR Lead Source", "in_list_view": 1}
            ]
        },
        {
            "name": "Google Ads Keyword KPI",
            "fields": [
                {"fieldname": "date", "label": "Date", "fieldtype": "Date", "in_list_view": 1},
                {"fieldname": "keyword", "label": "Keyword", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"fieldname": "impressions", "label": "Impressions", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "clicks", "label": "Clicks", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "cost", "label": "Cost", "fieldtype": "Currency", "in_list_view": 1},
                {"fieldname": "conversions", "label": "Conversions", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "source", "label": "Source", "fieldtype": "Link", "options": "SR Lead Source", "in_list_view": 1}
            ]
        },
        {
            "name": "Google Ads Search Term KPI",
            "fields": [
                {"fieldname": "date", "label": "Date", "fieldtype": "Date", "in_list_view": 1},
                {"fieldname": "search_term", "label": "Search Term", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"fieldname": "impressions", "label": "Impressions", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "clicks", "label": "Clicks", "fieldtype": "Int", "in_list_view": 1},
                {"fieldname": "cost", "label": "Cost", "fieldtype": "Currency", "in_list_view": 1},
                {"fieldname": "conversions", "label": "Conversions", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "source", "label": "Source", "fieldtype": "Link", "options": "SR Lead Source", "in_list_view": 1}
            ]
        }
    ]

    for dt in doctypes_to_create:
        if not frappe.db.exists("DocType", dt["name"]):
            doc = frappe.get_doc({
                "doctype": "DocType",
                "name": dt["name"],
                "module": module_name,
                "custom": 0,
                "fields": dt["fields"],
                "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}],
                "name_case": "Title Case",
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Created DocType: {dt['name']}")
        else:
            print(f"DocType already exists: {dt['name']}")

    workspace_name = "Google Ads KPI"
    if not frappe.db.exists("Workspace", workspace_name):
        ws_doc = frappe.get_doc({
            "doctype": "Workspace",
            "name": workspace_name,
            "title": workspace_name,
            "module": module_name,
            "is_standard": 1,
            "public": 1,
            "content": '[{"id":"header1","type":"header","data":{"text":"Google Ads","level":3}},{"id":"S1","type":"shortcut","data":{"shortcut_name":"Campaign Performance","col":3}},{"id":"S2","type":"shortcut","data":{"shortcut_name":"Ad Performance","col":3}},{"id":"S3","type":"shortcut","data":{"shortcut_name":"Keyword Metrics","col":3}},{"id":"S4","type":"shortcut","data":{"shortcut_name":"Search Terms","col":3}}]'
        })
        
        # Create Shortcuts
        shortcuts = [
            {"type": "DocType", "link_to": "Google Ads Campaign KPI", "label": "Campaign Performance"},
            {"type": "DocType", "link_to": "Google Ads Ad KPI", "label": "Ad Performance"},
            {"type": "DocType", "link_to": "Google Ads Keyword KPI", "label": "Keyword Metrics"},
            {"type": "DocType", "link_to": "Google Ads Search Term KPI", "label": "Search Terms"}
        ]
        
        for sc in shortcuts:
            ws_doc.append("shortcuts", sc)
            
        ws_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created Workspace and Shortcuts for {workspace_name}")
