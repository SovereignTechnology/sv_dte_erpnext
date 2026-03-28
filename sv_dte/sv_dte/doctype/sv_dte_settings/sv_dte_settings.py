import frappe
from frappe.model.document import Document


class SVDTESettings(Document):
	def get_base_url(self):
		if self.ambiente == "00":
			return "https://apitest.dtes.mh.gob.sv"
		return "https://api.dtes.mh.gob.sv"

	def get_auth_url(self):
		return f"{self.get_base_url()}/seguridad/auth/"

	def get_reception_url(self):
		return f"{self.get_base_url()}/fesv/recepciondte"

	def get_invalidation_url(self):
		return f"{self.get_base_url()}/fesv/anulardte"

	def get_contingency_url(self):
		return f"{self.get_base_url()}/fesv/contingencia"

	def get_batch_url(self):
		return f"{self.get_base_url()}/fesv/recepcionlote/"
