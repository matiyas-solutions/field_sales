import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.nestedset import get_ancestors_of

from field_sales.setup import ASM, SO
from field_sales.utils import ensure_client_id, stock_status, STOCK_OK


class FSStockAudit(Document):
	def before_naming(self):
		ensure_client_id(self)

	def validate(self):
		for row in self.items:
			if flt(row.qty) < 0:
				frappe.throw(_("Row {0}: quantity cannot be negative.").format(row.idx))
			# The minimum comes from the Item, so it cannot be set on the way in.
			row.min_qty = flt(frappe.db.get_value("Item", row.item_code, "fs_min_outlet_stock"))
			row.stock_status = stock_status(flt(row.qty), row.min_qty)
		self.has_alert = 1 if any(r.stock_status != STOCK_OK for r in self.items) else 0

	def after_insert(self):
		if self.has_alert and frappe.db.get_single_value("FS Settings", "notify_low_stock"):
			self._notify_managers()

	def _notify_managers(self):
		count = sum(1 for r in self.items if r.stock_status != STOCK_OK)
		subject = _("{0} product(s) low or out of stock at {1}").format(count, self.outlet_name or self.outlet)
		for user in _managers_covering(self.territory):
			if user == self.owner:
				continue
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"for_user": user,
					"from_user": self.owner,
					"type": "Alert",
					"document_type": self.doctype,
					"document_name": self.name,
					"subject": subject,
				}
			).insert(ignore_permissions=True)


def _managers_covering(territory: str | None) -> list[str]:
	"""Front-line managers only. Everyone above them can see the same data in reports,
	and alerting the whole chain for each shelf would train them to ignore it."""
	if not territory:
		return []
	covering = [territory, *get_ancestors_of("Territory", territory)]
	users = frappe.get_all(
		"User Permission",
		filters={"allow": "Territory", "for_value": ("in", covering)},
		pluck="user",
		distinct=True,
	)
	if not users:
		return []
	holders = frappe.get_all(
		"Has Role",
		filters={"parenttype": "User", "parent": ("in", users), "role": ("in", (ASM, SO))},
		pluck="parent",
		distinct=True,
	)
	return frappe.get_all("User", filters={"name": ("in", holders), "enabled": 1}, pluck="name") if holders else []
