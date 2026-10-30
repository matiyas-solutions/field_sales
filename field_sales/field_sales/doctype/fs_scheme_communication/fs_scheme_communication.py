from frappe.model.document import Document

from field_sales.utils import ensure_client_id


class FSSchemeCommunication(Document):
	def before_naming(self):
		ensure_client_id(self)
