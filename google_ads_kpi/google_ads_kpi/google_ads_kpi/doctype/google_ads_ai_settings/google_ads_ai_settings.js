frappe.ui.form.on("Google Ads AI Settings", {
	refresh(frm) {
		loadFilterOptions(frm);
		frm.add_custom_button("Run AI Pipeline", () => {
			if (frm.__ai_pipeline_running) {
				frappe.show_alert({ message: "AI pipeline is already running...", indicator: "orange" });
				return;
			}

			const filterMode = frm.doc.filter_mode || "all";
			const accountFilter = (frm.doc.google_ads_account_filter || "").trim();
			const campaignFilter = (frm.doc.campaign_name_filter || "").trim();
			if (filterMode === "filtered" && !accountFilter && !campaignFilter) {
				frappe.msgprint(
					"Select at least one filter (Google Ads Account or Campaign Name), or set Report Scope to 'all'."
				);
				return;
			}
			frm.__ai_pipeline_running = true;
			frappe.call({
				method: "google_ads_kpi.google_ads_kpi.ai.api.run_ai_pipeline",
				args: {
					days: 180,
					horizon_days: 7,
					persist_recommendations: 1,
					filter_mode: filterMode,
					google_ads_account: accountFilter || null,
					campaign_name: campaignFilter || null,
				},
				freeze: true,
				freeze_message: "Running AI pipeline...",
				callback: (r) => {
					const data = r.message || {};
					const forecastCount = (data.forecasts || []).length;
					const alertCount = (data.alerts || []).length;
					const recommendationCount = (data.recommendations || []).length;
					const scope = (data.filter_mode || "all").toUpperCase();
					frappe.show_alert(
						{
							message:
								`AI done | Scope: ${scope} | Forecasts: ${forecastCount} | Alerts: ${alertCount} | Recommendations: ${recommendationCount}`,
							indicator: "green",
						},
						8
					);
				},
				error: () => {
					frappe.show_alert({ message: "AI pipeline failed. Check error log.", indicator: "red" }, 8);
				},
				always: () => {
					frm.__ai_pipeline_running = false;
				},
			});
		});

		frm.add_custom_button("Ask AI Analyst", () => {
			frappe.prompt(
				[
					{
						fieldname: "question",
						label: "Question",
						fieldtype: "Small Text",
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method: "google_ads_kpi.google_ads_kpi.ai.api.ask_ai_analyst",
						args: {
							question: values.question,
						},
						freeze: true,
						freeze_message: "Asking AI analyst...",
						callback: (r) => {
							const result = r.message || {};
							frappe.msgprint({
								title: "AI Analyst Response",
								indicator: "blue",
								message:
									`<b>Answer:</b><br>${frappe.utils.escape_html(result.answer || "No answer returned.")}<br><br>` +
									`<b>Confidence:</b> ${result.confidence || "N/A"}`,
							});
						},
					});
				},
				"Ask AI Analyst",
				"Ask"
			);
		});
	},
});

function loadFilterOptions(frm) {
	frappe.call({
		method: "google_ads_kpi.google_ads_kpi.ai.api.get_kpi_filter_options",
		callback: (r) => {
			const data = r.message || {};
			const accountOptions = ["", ...(data.google_ads_accounts || [])].join("\n");
			const campaignOptions = ["", ...(data.campaign_names || [])].join("\n");

			frm.set_df_property("google_ads_account_filter", "options", accountOptions);
			frm.set_df_property("campaign_name_filter", "options", campaignOptions);
		},
	});
}

