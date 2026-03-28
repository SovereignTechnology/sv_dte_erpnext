import json

import frappe
import requests

from .auth import get_token


def transmit_document(dte_doc):
	"""Transmit a signed DTE document to the MH reception API."""
	settings = frappe.get_single("SV DTE Settings")
	token = get_token()
	url = settings.get_reception_url()

	tipo_dte = dte_doc.tipo_dte[:2]

	request_data = {
		"ambiente": settings.ambiente,
		"idEnvio": 1,
		"version": 3,
		"tipoDte": tipo_dte,
		"documento": dte_doc.signed_payload,
	}

	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json",
	}

	response = requests.post(
		url,
		json=request_data,
		headers=headers,
		timeout=60,
	)

	safe_headers = {"Authorization": "Bearer ***", "Content-Type": "application/json"}
	frappe.get_doc(
		{
			"doctype": "DTE API Log",
			"dte_document": dte_doc.name,
			"endpoint": url,
			"method": "POST",
			"request_headers": json.dumps(safe_headers),
			"request_body": json.dumps({**request_data, "documento": "...JWS..."}),
			"http_status": response.status_code,
			"response_body": response.text[:65000] if response.text else None,
			"status": "Success" if 200 <= response.status_code < 300 else "Error",
		}
	).insert(ignore_permissions=True)

	response.raise_for_status()
	return response.json()


def invalidate_document(dte_doc, reason):
	"""Send an invalidation request to MH for an accepted DTE."""
	settings = frappe.get_single("SV DTE Settings")
	token = get_token()
	url = settings.get_invalidation_url()

	from .signing import sign_document

	invalidation_payload = {
		"identificacion": {
			"version": 2,
			"ambiente": settings.ambiente,
			"codigoGeneracion": dte_doc.codigo_generacion,
			"fecAnula": frappe.utils.today(),
			"horAnula": frappe.utils.nowtime(),
		},
		"emisor": {
			"nit": settings.nit,
			"nombre": settings.nombre_emisor,
			"tipoEstablecimiento": settings.tipo_establecimiento,
			"nomEstablecimiento": settings.nombre_comercial,
			"codEstableMH": settings.cod_estable_mh,
			"codEstable": settings.cod_estable,
			"codPuntoVentaMH": settings.cod_punto_venta_mh,
			"codPuntoVenta": settings.cod_punto_venta,
			"telefono": settings.telefono,
			"correo": settings.correo,
		},
		"documento": {
			"tipoDte": dte_doc.tipo_dte[:2],
			"codigoGeneracion": dte_doc.codigo_generacion,
			"selloRecibido": dte_doc.sello_recibido,
			"numeroControl": dte_doc.numero_control,
			"fecEmi": str(dte_doc.fec_emi),
			"montoIva": float(dte_doc.total_iva or 0),
			"codigoGeneracionR": None,
			"tipoDocumento": None,
			"numDocumento": None,
			"nombre": dte_doc.receptor_nombre,
			"telefono": None,
			"correo": dte_doc.receptor_correo,
		},
		"motivo": {
			"tipoAnulacion": 1,
			"motivoAnulacion": reason,
			"nombreResponsable": settings.nombre_emisor,
			"tipDocResponsable": "36",
			"numDocResponsable": settings.nit,
			"nombreSolicita": dte_doc.receptor_nombre,
			"tipDocSolicita": "36",
			"numDocSolicita": dte_doc.receptor_nit,
		},
	}

	signed = sign_document(invalidation_payload)

	request_data = {
		"ambiente": settings.ambiente,
		"idEnvio": 1,
		"version": 2,
		"documento": signed,
	}

	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json",
	}

	response = requests.post(url, json=request_data, headers=headers, timeout=60)
	response.raise_for_status()

	result = response.json()
	if result.get("estado") == "PROCESADO":
		dte_doc.status = "Invalidated"
		dte_doc.save()

	return result
