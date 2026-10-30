import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class FSScheme(Document):
	def validate(self):
		if getdate(self.valid_to) < getdate(self.valid_from):
			frappe.throw(_("Valid To cannot be before Valid From."))
		if not 0 <= flt(self.discount_percent) <= 100:
			frappe.throw(_("Discount must be between 0 and 100."))
