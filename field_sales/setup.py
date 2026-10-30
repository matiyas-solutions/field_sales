import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, setup_custom_perms, update_permission_property

NSM = "National Sales Manager"
ZSM = "Zonal Sales Manager"
RSM = "Regional Sales Manager"
ASM = "Area Sales Manager"
SO = "Sales Officer"
SR = "Sales Representative"

MANAGER_ROLES = (NSM, ZSM, RSM, ASM, SO)
FIELD_ROLES = (*MANAGER_ROLES, SR)

# What the mobile app reads from stock ERPNext doctypes.
READ_ONLY_DOCTYPES = (
	"Customer",
	"Item",
	"Item Group",
	"Item Price",
	"Price List",
	"Territory",
	"Company",
	"Warehouse",
	"Bin",
	"Payment Terms Template",
)


def _custom_fields() -> dict:
	# SQLite cannot add a UNIQUE column to an existing table. Bench's SQLite support is for
	# development, and the sync engine looks up this id before posting in any case.
	unique = 0 if frappe.db.db_type == "sqlite" else 1
	return {
		"Customer": [
			{"fieldname": "fs_distributor", "fieldtype": "Link", "label": "Distributor", "options": "Company", "insert_after": "territory"},
			{"fieldname": "fs_latitude", "fieldtype": "Float", "label": "Outlet Latitude", "precision": "7", "insert_after": "fs_distributor"},
			{"fieldname": "fs_longitude", "fieldtype": "Float", "label": "Outlet Longitude", "precision": "7", "insert_after": "fs_latitude"},
		],
		"Item": [
			{"fieldname": "fs_min_outlet_stock", "fieldtype": "Float", "label": "Minimum Outlet Stock", "insert_after": "stock_uom"},
		],
		"Sales Order": [
			{"fieldname": "fs_client_id", "fieldtype": "Data", "label": "Client ID", "read_only": 1, "no_copy": 1, "unique": unique, "insert_after": "order_type"},
			{"fieldname": "fs_visit", "fieldtype": "Link", "label": "Field Visit", "options": "FS Visit", "no_copy": 1, "insert_after": "fs_client_id"},
			{"fieldname": "fs_scheme", "fieldtype": "Link", "label": "Scheme", "options": "FS Scheme", "insert_after": "fs_visit"},
		],
	}


def after_install():
	after_migrate()
	_grant_permissions()


def after_migrate():
	_ensure_roles()
	create_custom_fields(_custom_fields(), update=True)


def _ensure_roles():
	for role in FIELD_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _grant_permissions():
	"""Runs once, on install. Re-running on migrate would undo an admin's later changes."""
	for doctype in READ_ONLY_DOCTYPES:
		for role in FIELD_ROLES:
			add_permission(doctype, role)

	# ERPNext checks the customer's receivable account when an order is saved. `select`
	# satisfies that without opening the ledger to field staff.
	for role in FIELD_ROLES:
		add_permission("Account", role)
		update_permission_property("Account", role, 0, "select", 1)
		update_permission_property("Account", role, 0, "read", 0)

	for role in MANAGER_ROLES:
		add_permission("Sales Order", role)
		for ptype in ("write", "create", "report", "export"):
			update_permission_property("Sales Order", role, 0, ptype, 1)

	add_permission("Sales Order", SR)
	update_permission_property("Sales Order", SR, 0, "if_owner", 1)
	for ptype in ("write", "create"):
		update_permission_property("Sales Order", SR, 0, ptype, 1, if_owner=1)


def before_uninstall():
	"""Removes what was added to ERPNext's own doctypes. Roles are left, since users hold them."""
	for dt, fields in _custom_fields().items():
		for field in fields:
			name = f"{dt}-{field['fieldname']}"
			if frappe.db.exists("Custom Field", name):
				frappe.delete_doc("Custom Field", name, ignore_permissions=True)

	for doctype in (*READ_ONLY_DOCTYPES, "Account", "Sales Order"):
		setup_custom_perms(doctype)
		frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": ("in", FIELD_ROLES)})
		frappe.clear_cache(doctype=doctype)
