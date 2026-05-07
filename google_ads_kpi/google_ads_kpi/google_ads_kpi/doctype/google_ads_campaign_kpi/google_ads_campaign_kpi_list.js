frappe.listview_settings["Google Ads Campaign KPI"] = {
	onload(listview) {
		listview.page.add_inner_button("Ask AI Campaign Analyst", () => {
			frappe.call({
				method: "google_ads_kpi.google_ads_kpi.ai.api.get_kpi_filter_options",
				callback: (r) => {
					const data = r.message || {};
					const accountOptions = (data.google_ads_accounts || []).filter(Boolean);
					const accountCampaignsMap = data.account_campaigns_map || {};

					if (!accountOptions.length) {
						frappe.msgprint("No Google Ads accounts found in KPI data.");
						return;
					}

					openGoogleAISelector(accountOptions, accountCampaignsMap);
				},
			});
		});
	},
};

function openGoogleAISelector(accountOptions, accountCampaignsMap) {
	const dialog = new frappe.ui.Dialog({
		title: "Ask AI Campaign Analyst",
		fields: [
			{
				fieldname: "google_ads_account",
				label: "Google Ads Account",
				fieldtype: "Select",
				reqd: 1,
				options: accountOptions.join("\n"),
				default: accountOptions[0],
			},
			{
				fieldname: "campaign_name",
				label: "Campaign Name",
				fieldtype: "Select",
				reqd: 1,
			},
			{
				fieldname: "select_multiple_campaigns",
				label: "Select Multiple Campaigns",
				fieldtype: "Check",
				default: 0,
			},
			{
				fieldname: "campaign_names",
				label: "Campaign Names",
				fieldtype: "MultiCheck",
				columns: 1,
				hidden: 1,
			},
			{
				fieldname: "question",
				label: "Question",
				fieldtype: "Small Text",
				reqd: 1,
				default: "Is this campaign running good or not? What should I improve?",
			},
		],
		primary_action_label: "Open Chat",
		primary_action: (values) => {
			const multiEnabled = !!values.select_multiple_campaigns;
			const selectedCampaigns = Array.isArray(values.campaign_names)
				? values.campaign_names.filter(Boolean)
				: values.campaign_names
					? [values.campaign_names]
					: [];
			if (multiEnabled && !selectedCampaigns.length) {
				frappe.msgprint("Please select at least one campaign.");
				return;
			}
			openCampaignAIChat({
				campaignName: values.campaign_name,
				campaignNames: multiEnabled ? selectedCampaigns : [],
				googleAdsAccount: values.google_ads_account || null,
				initialQuestion: values.question,
				days: 60,
			});
			dialog.hide();
		},
	});

	const refreshCampaignOptions = (account) => {
		const campaigns = (accountCampaignsMap[account] || []).filter(Boolean);
		const options = ["All", ...campaigns];
		dialog.set_df_property("campaign_name", "options", options.join("\n"));
		dialog.set_value("campaign_name", options[0] || "All");
		dialog.set_df_property(
			"campaign_names",
			"options",
			campaigns.map((label) => ({ label, value: label, checked: 0 }))
		);
		dialog.set_value("campaign_names", []);
	};

	const refreshMode = () => {
		const multiEnabled = !!dialog.get_value("select_multiple_campaigns");
		dialog.set_df_property("campaign_name", "hidden", multiEnabled ? 1 : 0);
		dialog.set_df_property("campaign_name", "reqd", multiEnabled ? 0 : 1);
		dialog.set_df_property("campaign_names", "hidden", multiEnabled ? 0 : 1);
		if (multiEnabled) {
			dialog.set_value("campaign_name", "All");
		} else {
			dialog.set_value("campaign_names", []);
		}
	};

	dialog.show();
	refreshCampaignOptions(dialog.get_value("google_ads_account"));
	refreshMode();
	dialog.get_field("google_ads_account").$input.on("change", () => {
		refreshCampaignOptions(dialog.get_value("google_ads_account"));
	});
	dialog.get_field("select_multiple_campaigns").$input.on("change", () => {
		refreshMode();
	});
}

function openCampaignAIChat({
	campaignName,
	campaignNames = [],
	googleAdsAccount = null,
	days = 60,
	initialQuestion = "",
}) {
	const messages = [];
	const selectedCampaigns = campaignNames.length ? campaignNames : campaignName && campaignName !== "All" ? [campaignName] : [];
	const scopeText = selectedCampaigns.length
		? selectedCampaigns.join(", ")
		: campaignName === "All"
			? "All campaigns under selected account"
			: "Not specified";
	const dialog = new frappe.ui.Dialog({
		title: `AI Campaign Chat - ${campaignNames.length ? `${campaignNames.length} Campaigns` : campaignName || "Campaign"}`,
		size: "large",
		fields: [
			{ fieldtype: "HTML", fieldname: "selection_html" },
			{ fieldtype: "HTML", fieldname: "chat_html" },
			{
				fieldtype: "Small Text",
				fieldname: "question",
				label: "Ask a follow-up",
				reqd: 1,
				default: initialQuestion,
			},
		],
		primary_action_label: "Send",
		primary_action: () => sendQuestion(),
	});

	const selectionField = dialog.get_field("selection_html");
	const chatField = dialog.get_field("chat_html");
	const selectionHtml = selectionField && selectionField.$wrapper ? selectionField.$wrapper : null;
	const chatHtml = chatField && chatField.$wrapper ? chatField.$wrapper : null;
	if (!chatHtml || !selectionHtml) {
		frappe.msgprint("Unable to open AI chat view. Please refresh and try again.");
		return;
	}
	selectionHtml.html(
		`<div style="margin-bottom:8px;padding:10px 12px;border:1px solid #e5e7eb;border-radius:8px;background:#f8fafc;">
			<div style="font-size:12px;color:#6b7280;">Analyzing Scope</div>
			<div style="font-size:14px;color:#111827;"><b>Account:</b> ${escapeHtml(googleAdsAccount || "N/A")}<br><b>Campaign(s):</b> ${escapeHtml(scopeText)}</div>
		</div>`
	);
	chatHtml.css({
		maxHeight: "420px",
		overflowY: "auto",
		border: "1px solid #e5e7eb",
		borderRadius: "8px",
		padding: "12px",
		marginBottom: "8px",
		background: "#f8fafc",
	});

	const renderMessages = () => {
		const html = messages
			.map((item) => {
				if (item.role === "user") {
					return `<div style="text-align:right;margin:8px 0;"><div style="display:inline-block;background:#dbeafe;color:#1e3a8a;padding:8px 12px;border-radius:12px;max-width:85%;text-align:left;"><b>You:</b><br>${escapeHtml(item.text)}</div></div>`;
				}
				return `<div style="text-align:left;margin:8px 0;"><div style="display:inline-block;background:#ffffff;color:#111827;padding:10px 12px;border-radius:12px;max-width:90%;border:1px solid #e5e7eb;"><b>AI:</b><br>${formatAiAnswer(item.text)}<div style="margin-top:8px;color:#6b7280;font-size:12px;">Confidence: ${item.confidence || "N/A"}</div></div></div>`;
			})
			.join("");
		chatHtml.html(html || "<div style='color:#6b7280'>Start the conversation...</div>");
		chatHtml.scrollTop(chatHtml[0].scrollHeight);
	};

	const sendQuestion = () => {
		const question = (dialog.get_value("question") || "").trim();
		if (!question) return;

		messages.push({ role: "user", text: question });
		dialog.set_value("question", "");
		renderMessages();

		const composedQuestion = buildThreadQuestion(messages);
		frappe.call({
			method: "google_ads_kpi.google_ads_kpi.ai.api.ask_campaign_ai",
			args: {
				campaign_name: campaignName,
				campaign_names: campaignNames,
				google_ads_account: googleAdsAccount || null,
				question: buildScopedQuestion(composedQuestion, googleAdsAccount, selectedCampaigns, campaignName),
				days,
			},
			freeze: true,
			freeze_message: "Analyzing campaign with KPI context...",
			callback: (r) => {
				const out = r.message || {};
				messages.push({ role: "assistant", text: out.answer || "No answer returned.", confidence: out.confidence });
				renderMessages();
			},
		});
	};

	dialog.show();
	renderMessages();
}

function buildThreadQuestion(messages) {
	const recent = messages.slice(-8);
	const lines = recent.map((item) => `${item.role === "user" ? "User" : "Assistant"}: ${item.text}`);
	lines.push("Answer the latest user question with campaign-specific KPI evidence from context.");
	return lines.join("\n");
}

function buildScopedQuestion(baseQuestion, googleAdsAccount, selectedCampaigns, campaignName) {
	const scopeLine = selectedCampaigns.length
		? `Selected campaign names: ${selectedCampaigns.join(", ")}`
		: campaignName === "All"
			? "Selected campaign names: ALL CAMPAIGNS under selected account."
			: `Selected campaign names: ${campaignName || "N/A"}`;
	return [
		`Google Ads Account: ${googleAdsAccount || "N/A"}`,
		scopeLine,
		"Important: mention selected campaign names explicitly in your analysis.",
		baseQuestion,
	].join("\n");
}

function formatAiAnswer(text) {
	const safe = escapeHtml(text || "");
	const withHeadings = safe.replace(/^###\s*(.+)$/gm, "<h5 style='margin:8px 0 4px;'>$1</h5>");
	const withBold = withHeadings.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
	const lines = withBold.split("\n").map((line) => line.trim());
	let inList = false;
	let out = "";
	lines.forEach((line) => {
		if (!line) return;
		if (/^\d+\.\s+/.test(line) || /^-\s+/.test(line)) {
			if (!inList) {
				out += "<ul style='margin:6px 0 6px 18px;'>";
				inList = true;
			}
			out += `<li>${line.replace(/^\d+\.\s+/, "").replace(/^-\s+/, "")}</li>`;
		} else {
			if (inList) {
				out += "</ul>";
				inList = false;
			}
			out += `<p style='margin:4px 0;'>${line}</p>`;
		}
	});
	if (inList) out += "</ul>";
	return out;
}

function escapeHtml(value) {
	return (value || "")
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;")
		.replaceAll('"', "&quot;")
		.replaceAll("'", "&#39;");
}

