import json

import frappe
import requests
from frappe.utils import add_to_date, now_datetime


def get_token():
	"""Get a valid JWT token from MH, using cached token if still valid."""
	settings = frappe.get_single("SV DTE Settings")

	if settings.jwt_token and settings.token_expiry:
		if now_datetime() < settings.token_expiry:
			return settings.jwt_token

	return _request_new_token(settings)


def _request_new_token(settings):
	url = settings.get_auth_url()
	payload = {
		"user": settings.nit,
		"pwd": settings.get_password("api_password"),
	}

	response = requests.post(
		url,
		data=payload,
		headers={"Content-Type": "application/x-www-form-urlencoded"},
		timeout=30,
	)

	_log_api_call(
		endpoint=url,
		method="POST",
		request_body=json.dumps({"user": settings.nit, "pwd": "***"}),
		http_status=response.status_code,
		response_body=response.text,
	)

	response.raise_for_status()
	data = response.json()

	token = data.get("body", {}).get("token") or data.get("token")
	if not token:
		frappe.throw("Failed to obtain JWT token from MH: " + response.text)

	# Testing tokens last 48h, production 24h
	hours = 48 if settings.ambiente == "00" else 24
	expiry = add_to_date(now_datetime(), hours=hours - 1)

	settings.jwt_token = token
	settings.token_expiry = expiry
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	return token


def _log_api_call(endpoint, method, request_body, http_status, response_body, dte_document=None):
	frappe.get_doc(
		{
			"doctype": "DTE API Log",
			"dte_document": dte_document,
			"endpoint": endpoint,
			"method": method,
			"request_body": request_body,
			"http_status": http_status,
			"response_body": response_body[:65000] if response_body else None,
			"status": "Success" if 200 <= http_status < 300 else "Error",
		}
	).insert(ignore_permissions=True)
