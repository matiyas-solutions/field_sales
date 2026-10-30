import frappe
from frappe import _
from frappe.utils import flt, getdate


def before_validate(doc, method=None):
	"""Field orders are built offline on a phone, so the server has the last word on money.

	Only new orders with a `fs_client_id` are touched: once an order exists, a distributor
	editing the draft in the desk is free to change it.
	"""
	if not doc.get("fs_client_id") or not doc.is_new():
		return

	scheme = _get_valid_scheme(doc)
	for item in doc.items:
		list_rate = _selling_rate(item.item_code, doc.selling_price_list, doc.transaction_date, doc.customer)
		if list_rate is not None:
			item.price_list_rate = list_rate
		item.discount_percentage = min(flt(item.discount_percentage), _allowed_discount(scheme, item))
		# ERPNext keeps a rate it is handed, so set it rather than trust the phone's.
		item.rate = flt(item.price_list_rate) * (1 - flt(item.discount_percentage) / 100)


def _get_valid_scheme(doc):
	"""Judged on the order's own date, so an order booked offline during a scheme stays valid
	even if it syncs after the scheme ended."""
	if not doc.get("fs_scheme"):
		return None

	scheme = frappe.get_cached_doc("FS Scheme", doc.fs_scheme)
	order_date = getdate(doc.transaction_date)
	if not scheme.is_active:
		frappe.throw(_("Scheme {0} has been withdrawn.").format(scheme.title))
	if not getdate(scheme.valid_from) <= order_date <= getdate(scheme.valid_to):
		frappe.throw(_("Scheme {0} was not running on {1}.").format(scheme.title, order_date))
	if scheme.company and scheme.company != doc.company:
		frappe.throw(_("Scheme {0} does not apply to {1}.").format(scheme.title, doc.company))
	return scheme


def _allowed_discount(scheme, item) -> float:
	if not scheme:
		return 0.0
	if scheme.item_group:
		group = frappe.get_cached_value("Item", item.item_code, "item_group")
		if group not in _group_and_descendants(scheme.item_group):
			return 0.0
	return flt(scheme.discount_percent)


def _group_and_descendants(group: str) -> list[str]:
	from frappe.utils.nestedset import get_descendants_of

	return [group, *get_descendants_of("Item Group", group)]


def _selling_rate(item_code: str, price_list: str, on_date, customer: str | None) -> float | None:
	"""The rate in force on the order date, preferring one set for this customer."""
	rows = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "price_list": price_list, "selling": 1},
		fields=["price_list_rate", "customer", "valid_from", "valid_upto"],
	)
	day = getdate(on_date)
	running = [
		r
		for r in rows
		if (not r.valid_from or getdate(r.valid_from) <= day)
		and (not r.valid_upto or getdate(r.valid_upto) >= day)
		and (not r.customer or r.customer == customer)
	]
	if not running:
		return None
	running.sort(key=lambda r: (not r.customer, -(getdate(r.valid_from).toordinal() if r.valid_from else 0)))
	return flt(running[0].price_list_rate)
