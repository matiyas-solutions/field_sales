from math import atan2, cos, radians, sin, sqrt

import frappe

STOCK_OK, STOCK_LOW, STOCK_OUT = "OK", "Low", "Stockout"


def distance_metres(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
	"""Great-circle distance in metres."""
	d_lat = radians(lat2 - lat1)
	d_lng = radians(lng2 - lng1)
	a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
	return 2 * 6371000.0 * atan2(sqrt(a), sqrt(1 - a))


def stock_status(qty: float, min_qty: float) -> str:
	if qty <= 0:
		return STOCK_OUT
	return STOCK_LOW if qty < min_qty else STOCK_OK


def has_coordinates(lat: float | None, lng: float | None) -> bool:
	"""Zero means the outlet was never tagged, not that it sits off West Africa."""
	return bool(lat or lng)


def ensure_client_id(doc):
	"""Field documents are named by an id from the phone. Desk-created ones get one here."""
	if not doc.client_id:
		doc.client_id = f"{doc.doctype.replace(' ', '-')}-{frappe.generate_hash(length=10)}"
