frappe.ui.form.on("Google Ads AI Recommendation", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button("Ask AI Analyst", () => {
			frappe.prompt(
				[
					{
						fieldname: "question",
						label: "Question about this recommendation",
						fieldtype: "Small Text",
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method: "google_ads_kpi.google_ads_kpi.ai.api.ask_recommendation_ai",
						args: {
							recommendation_name: frm.doc.name,
							question: values.question,
						},
						freeze: true,
						freeze_message: "Analyzing recommendation...",
						callback: (r) => {
							const out = r.message || {};
							frappe.msgprint({
								title: "AI Analyst",
								indicator: "blue",
								message:
									`<b>Answer:</b><br>${frappe.utils.escape_html(out.answer || "No answer returned.")}<br><br>` +
									`<b>Confidence:</b> ${out.confidence || "N/A"}`,
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

