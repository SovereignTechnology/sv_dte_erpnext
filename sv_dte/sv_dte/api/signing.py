import json

import frappe
import requests


def sign_document(dte_payload):
	"""Send the DTE JSON to the local firmador service and return the JWS string."""
	settings = frappe.get_single("SV DTE Settings")

	firmador_url = settings.firmador_url
	if not firmador_url.endswith("/"):
		firmador_url += "/"

	request_data = {
		"nit": settings.nit,
		"activo": True,
		"passwordPri": settings.get_password("certificate_password"),
		"dteJson": dte_payload,
	}

	response = requests.post(
		firmador_url,
		json=request_data,
		timeout=30,
	)

	# Log without the certificate password
	safe_log = {
		"nit": settings.nit,
		"activo": True,
		"passwordPri": "***",
		"dteJson": "...",
	}
	_log_signing(firmador_url, safe_log, response)

	response.raise_for_status()
	data = response.json()

	signed_body = data.get("body") or data.get("documento")
	if not signed_body:
		frappe.throw("Firmador did not return a signed document: " + response.text)

	return signed_body


def check_firmador_status():
	"""Check if the local firmador service is running."""
	settings = frappe.get_single("SV DTE Settings")
	firmador_url = settings.firmador_url.rstrip("/")
	status_url = firmador_url.replace("/firmardocumento", "/firmardocumento/status")
	if not status_url.endswith("/"):
		status_url += "/"

	try:
		response = requests.get(status_url, timeout=5)
		return {"online": True, "status": response.status_code, "body": response.text}
	except requests.ConnectionError:
		return {"online": False, "error": "Firmador service not reachable"}


def _log_signing(url, safe_request, response):
	frappe.get_doc(
		{
			"doctype": "DTE API Log",
			"endpoint": url,
			"method": "POST",
			"request_body": json.dumps(safe_request),
			"http_status": response.status_code,
			"response_body": response.text[:65000] if response.text else None,
			"status": "Success" if 200 <= response.status_code < 300 else "Error",
		}
	).insert(ignore_permissions=True)
