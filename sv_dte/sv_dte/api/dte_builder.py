import frappe
from frappe import _


def build_ccf(dte_doc):
	"""Build a Credito Fiscal (type 03) JSON payload from a DTE Document linked to a Sales Invoice."""
	settings = frappe.get_single("SV DTE Settings")

	if not dte_doc.sales_invoice:
		frappe.throw(_("Sales Invoice is required to build a CCF"))

	invoice = frappe.get_doc("Sales Invoice", dte_doc.sales_invoice)
	customer = frappe.get_doc("Customer", invoice.customer)

	identificacion = _build_identificacion(dte_doc, settings, tipo_dte="03")
	emisor = _build_emisor(settings)
	receptor = _build_receptor_ccf(dte_doc, customer)
	cuerpo, totals = _build_cuerpo_ccf(invoice)
	resumen = _build_resumen_ccf(invoice, totals, dte_doc)

	dte_doc.total_gravada = totals["totalGravada"]
	dte_doc.total_iva = totals["totalIva"]
	dte_doc.monto_total_operacion = resumen["montoTotalOperacion"]

	return {
		"identificacion": identificacion,
		"documentoRelacionado": None,
		"emisor": emisor,
		"receptor": receptor,
		"otrosDocumentos": None,
		"ventaTercero": None,
		"cuerpoDocumento": cuerpo,
		"resumen": resumen,
		"extension": None,
		"apendice": None,
	}


def build_factura(dte_doc):
	"""Build a Factura (type 01) JSON payload from a DTE Document linked to a Sales Invoice."""
	settings = frappe.get_single("SV DTE Settings")

	if not dte_doc.sales_invoice:
		frappe.throw(_("Sales Invoice is required to build a Factura"))

	invoice = frappe.get_doc("Sales Invoice", dte_doc.sales_invoice)
	customer = frappe.get_doc("Customer", invoice.customer)

	identificacion = _build_identificacion(dte_doc, settings, tipo_dte="01")
	emisor = _build_emisor(settings)
	receptor = _build_receptor_factura(dte_doc, customer)
	cuerpo, totals = _build_cuerpo_factura(invoice)
	resumen = _build_resumen_factura(invoice, totals, dte_doc)

	dte_doc.total_gravada = totals["totalGravada"]
	dte_doc.total_iva = totals["totalIva"]
	dte_doc.monto_total_operacion = resumen["montoTotalOperacion"]

	return {
		"identificacion": identificacion,
		"documentoRelacionado": None,
		"emisor": emisor,
		"receptor": receptor,
		"otrosDocumentos": None,
		"ventaTercero": None,
		"cuerpoDocumento": cuerpo,
		"resumen": resumen,
		"extension": None,
		"apendice": None,
	}


def _build_identificacion(dte_doc, settings, tipo_dte):
	return {
		"version": 3,
		"ambiente": settings.ambiente,
		"tipoDte": tipo_dte,
		"numeroControl": dte_doc.numero_control,
		"codigoGeneracion": dte_doc.codigo_generacion,
		"tipoModelo": 1,
		"tipoOperacion": 1,
		"tipoContingencia": None,
		"motivoContin": None,
		"fecEmi": str(dte_doc.fec_emi),
		"horEmi": str(dte_doc.hor_emi),
		"tipoMoneda": "USD",
	}


def _build_emisor(settings):
	return {
		"nit": settings.nit,
		"nrc": settings.nrc,
		"nombre": settings.nombre_emisor,
		"codActividad": settings.cod_actividad,
		"descActividad": settings.desc_actividad,
		"nombreComercial": settings.nombre_comercial or settings.nombre_emisor,
		"tipoEstablecimiento": settings.tipo_establecimiento,
		"direccion": {
			"departamento": settings.departamento,
			"municipio": settings.municipio,
			"complemento": settings.complemento_direccion,
		},
		"telefono": settings.telefono,
		"correo": settings.correo,
		"codEstableMH": settings.cod_estable_mh,
		"codEstable": settings.cod_estable,
		"codPuntoVentaMH": settings.cod_punto_venta_mh,
		"codPuntoVenta": settings.cod_punto_venta,
	}


def _build_receptor_ccf(dte_doc, customer):
	return {
		"nit": dte_doc.receptor_nit,
		"nrc": dte_doc.receptor_nrc,
		"nombre": dte_doc.receptor_nombre or customer.customer_name,
		"codActividad": customer.get("sv_cod_actividad") or "00000",
		"descActividad": customer.get("sv_desc_actividad") or "",
		"nombreComercial": customer.get("sv_nombre_comercial") or customer.customer_name,
		"direccion": {
			"departamento": customer.get("sv_departamento") or "06",
			"municipio": customer.get("sv_municipio") or "14",
			"complemento": customer.get("sv_direccion_complemento") or "",
		},
		"telefono": customer.get("mobile_no") or customer.get("phone") or "",
		"correo": dte_doc.receptor_correo or "",
	}


def _build_receptor_factura(dte_doc, customer):
	receptor = {
		"tipoDocumento": None,
		"numDocumento": None,
		"nombre": dte_doc.receptor_nombre or customer.customer_name,
		"codActividad": None,
		"descActividad": None,
		"direccion": None,
		"telefono": None,
		"correo": dte_doc.receptor_correo or "",
	}

	if dte_doc.receptor_nit:
		receptor["tipoDocumento"] = "36"
		receptor["numDocumento"] = dte_doc.receptor_nit

	return receptor


def _build_cuerpo_ccf(invoice):
	"""Build line items for CCF. Prices are IVA-exclusive."""
	items = []
	total_gravada = 0
	total_iva = 0

	for i, item in enumerate(invoice.items, 1):
		net_amount = float(item.net_amount or item.amount)
		iva = round(net_amount * 0.13, 2)

		line = {
			"numItem": i,
			"tipoItem": 2 if item.get("is_service_item") else 1,
			"numeroDocumento": None,
			"cantidad": float(item.qty),
			"codigo": item.item_code or "",
			"codTributo": None,
			"uniMedida": 59,
			"descripcion": item.item_name or item.description or "",
			"precioUni": round(float(item.rate), 2),
			"montoDescu": round(float(item.discount_amount or 0), 2),
			"ventaNoSuj": 0,
			"ventaExenta": 0,
			"ventaGravada": round(net_amount, 2),
			"tributos": ["20"],
			"psv": 0,
			"noGravado": 0,
			"ivaItem": iva,
		}
		items.append(line)
		total_gravada += net_amount
		total_iva += iva

	totals = {
		"totalGravada": round(total_gravada, 2),
		"totalIva": round(total_iva, 2),
	}
	return items, totals


def _build_cuerpo_factura(invoice):
	"""Build line items for Factura. Prices are IVA-inclusive."""
	items = []
	total_gravada = 0
	total_iva = 0

	for i, item in enumerate(invoice.items, 1):
		gross_amount = float(item.amount or item.net_amount)
		iva = round(gross_amount - (gross_amount / 1.13), 2)
		net = round(gross_amount - iva, 2)

		line = {
			"numItem": i,
			"tipoItem": 2 if item.get("is_service_item") else 1,
			"numeroDocumento": None,
			"cantidad": float(item.qty),
			"codigo": item.item_code or "",
			"codTributo": None,
			"uniMedida": 59,
			"descripcion": item.item_name or item.description or "",
			"precioUni": round(float(item.rate), 2),
			"montoDescu": round(float(item.discount_amount or 0), 2),
			"ventaNoSuj": 0,
			"ventaExenta": 0,
			"ventaGravada": round(gross_amount, 2),
			"psv": 0,
			"noGravado": 0,
		}
		items.append(line)
		total_gravada += gross_amount
		total_iva += iva

	totals = {
		"totalGravada": round(total_gravada, 2),
		"totalIva": round(total_iva, 2),
	}
	return items, totals


def _build_resumen_ccf(invoice, totals, dte_doc):
	total_gravada = totals["totalGravada"]
	total_iva = totals["totalIva"]
	monto_total = round(total_gravada + total_iva, 2)

	condicion = int(dte_doc.condicion_operacion or 1)

	return {
		"totalNoSuj": 0,
		"totalExenta": 0,
		"totalGravada": total_gravada,
		"subTotalVentas": total_gravada,
		"descuNoSuj": 0,
		"descuExenta": 0,
		"descuGravada": 0,
		"porcentajeDescuento": 0,
		"totalDescu": 0,
		"tributos": [
			{
				"codigo": "20",
				"descripcion": "Impuesto al Valor Agregado 13%",
				"valor": total_iva,
			}
		],
		"subTotal": total_gravada,
		"ivaPerci1": 0,
		"ivaRete1": 0,
		"reteRenta": 0,
		"montoTotalOperacion": monto_total,
		"totalNoGravado": 0,
		"totalPagar": monto_total,
		"totalLetras": _amount_to_words(monto_total),
		"totalIva": total_iva,
		"saldoFavor": 0,
		"condicionOperacion": condicion,
		"pagos": [
			{
				"codigo": "01" if condicion == 1 else "02",
				"montoPago": monto_total,
				"referencia": None,
				"plazo": None,
				"periodo": None,
			}
		],
		"numPagoElectronico": None,
	}


def _build_resumen_factura(invoice, totals, dte_doc):
	total_gravada = totals["totalGravada"]
	total_iva = totals["totalIva"]
	condicion = int(dte_doc.condicion_operacion or 1)

	return {
		"totalNoSuj": 0,
		"totalExenta": 0,
		"totalGravada": total_gravada,
		"subTotalVentas": total_gravada,
		"descuNoSuj": 0,
		"descuExenta": 0,
		"descuGravada": 0,
		"porcentajeDescuento": 0,
		"totalDescu": 0,
		"subTotal": total_gravada,
		"ivaRete1": 0,
		"reteRenta": 0,
		"montoTotalOperacion": total_gravada,
		"totalNoGravado": 0,
		"totalPagar": total_gravada,
		"totalLetras": _amount_to_words(total_gravada),
		"totalIva": total_iva,
		"condicionOperacion": condicion,
		"pagos": [
			{
				"codigo": "01" if condicion == 1 else "02",
				"montoPago": total_gravada,
				"referencia": None,
				"plazo": None,
				"periodo": None,
			}
		],
		"numPagoElectronico": None,
	}


def _amount_to_words(amount):
	"""Convert amount to Spanish words for DTE totalLetras field."""
	ones = [
		"", "UN", "DOS", "TRES", "CUATRO", "CINCO",
		"SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ",
		"ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE",
		"DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE", "VEINTE",
	]
	tens = [
		"", "", "VEINTI", "TREINTA", "CUARENTA", "CINCUENTA",
		"SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
	]
	hundreds = [
		"", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
		"QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
	]

	def _convert_group(n):
		if n == 0:
			return ""
		if n == 100:
			return "CIEN"
		if n <= 20:
			return ones[n]
		if n < 30:
			return "VEINTI" + ones[n - 20]

		h = n // 100
		remainder = n % 100
		t = remainder // 10
		u = remainder % 10

		parts = []
		if h:
			parts.append(hundreds[h])
		if remainder:
			if remainder <= 20:
				parts.append(ones[remainder])
			else:
				if u:
					parts.append(tens[t] + " Y " + ones[u])
				else:
					parts.append(tens[t])
		return " ".join(parts)

	integer_part = int(amount)
	cents = round((amount - integer_part) * 100)

	if integer_part == 0:
		words = "CERO"
	elif integer_part == 1:
		words = "UN"
	else:
		millions = integer_part // 1000000
		thousands = (integer_part % 1000000) // 1000
		remainder = integer_part % 1000

		parts = []
		if millions:
			if millions == 1:
				parts.append("UN MILLON")
			else:
				parts.append(_convert_group(millions) + " MILLONES")
		if thousands:
			if thousands == 1:
				parts.append("MIL")
			else:
				parts.append(_convert_group(thousands) + " MIL")
		if remainder:
			parts.append(_convert_group(remainder))

		words = " ".join(parts)

	return f"{words} {cents:02d}/100 DOLARES"
