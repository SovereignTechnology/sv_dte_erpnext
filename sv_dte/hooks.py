app_name = "sv_dte"
app_title = "SV DTE"
app_publisher = "Sovereign Technology"
app_description = "El Salvador DTE (Documento Tributario Electronico) integration for ERPNext"
app_email = "services@sovtech.pro"
app_license = "AGPL-3.0-or-later"

required_apps = ["frappe", "erpnext"]

# DocType JS additions - add DTE button to Sales Invoice
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
}

# Scheduled tasks
scheduler_events = {
	"daily": [
		"sv_dte.sv_dte.api.auth.get_token",
	],
}
