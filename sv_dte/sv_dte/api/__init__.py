import frappe


@frappe.whitelist()
def create_dte_from_invoice(sales_invoice, tipo_dte, receptor_nit=None, receptor_nrc=None, receptor_correo=None, condicion_operacion="1"):
	"""Create a DTE Document from a submitted Sales Invoice."""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)

	if invoice.docstatus != 1:
		frappe.throw("Sales Invoice must be submitted")

	dte = frappe.get_doc(
		{
			"doctype": "DTE Document",
			"tipo_dte": tipo_dte,
			"sales_invoice": sales_invoice,
			"company": invoice.company,
			"receptor_nit": receptor_nit,
			"receptor_nrc": receptor_nrc,
			"receptor_nombre": invoice.customer_name,
			"receptor_correo": receptor_correo,
			"condicion_operacion": condicion_operacion,
		}
	)
	dte.insert()
	return dte.name
