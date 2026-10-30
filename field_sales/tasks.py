import frappe
from frappe.utils import add_to_date, cint, now_datetime


def auto_close_open_visits():
	"""Closes visits a rep forgot to check out of, so they stop distorting time-in-outlet."""
	hours = cint(frappe.db.get_single_value("FS Settings", "auto_close_after_hours"))
	if hours <= 0:
		return

	cutoff = add_to_date(now_datetime(), hours=-hours)
	for name in frappe.get_all(
		"FS Visit", filters={"status": "Open", "check_in_time": ["<", cutoff]}, pluck="name"
	):
		visit = frappe.get_doc("FS Visit", name)
		visit.status = "Auto Closed"
		visit.flags.ignore_permissions = True
		visit.save()
		frappe.db.commit()  # One bad visit must not undo the rest of the run.
