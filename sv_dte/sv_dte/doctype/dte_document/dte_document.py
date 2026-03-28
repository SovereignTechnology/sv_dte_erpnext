import json
import uuid

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, today, nowtime


class DTEDocument(Document):
	def before_insert(self):
		if not self.codigo_generacion:
			self.codigo_generacion = str(uuid.uuid4()).upper()
		if not self.numero_control:
			self.numero_control = self._generate_numero_control()
		if not self.fec_emi:
			self.fec_emi = today()
		if not self.hor_emi:
			self.hor_emi = nowtime()

		settings = frappe.get_single("SV DTE Settings")
		self.ambiente = settings.ambiente

	def _generate_numero_control(self):
		settings = frappe.get_single("SV DTE Settings")
		tipo_dte = self.tipo_dte[:2]
		cod_estable = settings.cod_estable or "0000"
		cod_punto_venta = settings.cod_punto_venta or "0000"

		last = frappe.db.sql(
			"""
			SELECT numero_control FROM `tabDTE Document`
			WHERE tipo_dte LIKE %s
			ORDER BY creation DESC LIMIT 1
			""",
			(f"{tipo_dte}%",),
			as_dict=True,
		)

		if last and last[0].numero_control:
			parts = last[0].numero_control.split("-")
			correlativo = int(parts[-1]) + 1
		else:
			correlativo = 1

		return f"DTE-{tipo_dte}-{cod_estable}{cod_punto_venta}-{correlativo:015d}"

	@frappe.whitelist()
	def build_dte_json(self):
		from sv_dte.sv_dte.api.dte_builder import build_ccf, build_factura

		tipo = self.tipo_dte[:2]
		if tipo == "03":
			payload = build_ccf(self)
		elif tipo == "01":
			payload = build_factura(self)
		else:
			frappe.throw(_("DTE type {0} not yet implemented").format(tipo))

		self.dte_json = json.dumps(payload, indent=2, ensure_ascii=False)
		self.save()
		return payload

	@frappe.whitelist()
	def sign_dte(self):
		from sv_dte.sv_dte.api.signing import sign_document

		if not self.dte_json:
			frappe.throw(_("Build the DTE JSON first"))

		payload = json.loads(self.dte_json)
		signed = sign_document(payload)
		self.signed_payload = signed
		self.status = "Signed"
		self.save()
		return signed

	@frappe.whitelist()
	def transmit_dte(self):
		from sv_dte.sv_dte.api.transmission import transmit_document

		if not self.signed_payload:
			frappe.throw(_("Sign the DTE first"))

		response = transmit_document(self)

		self.mh_response_json = json.dumps(response, indent=2, ensure_ascii=False)
		self.fecha_procesamiento = response.get("fhProcesamiento")
		self.codigo_msg = response.get("codigoMsg")
		self.descripcion_msg = response.get("descripcionMsg")

		if response.get("estado") == "PROCESADO":
			self.sello_recibido = response.get("selloRecibido")
			self.status = "Accepted"
		else:
			self.status = "Rejected"

		self.save()
		return response

	@frappe.whitelist()
	def full_send(self):
		self.build_dte_json()
		self.sign_dte()
		return self.transmit_dte()
