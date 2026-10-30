import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime

from field_sales.utils import distance_metres, ensure_client_id, has_coordinates


class FSVisit(Document):
	def before_naming(self):
		ensure_client_id(self)

	def validate(self):
		self._set_location_check()
		self._set_duration()

	def _set_location_check(self):
		"""Recorded rather than rejected: the rep may be offline and already gone, and a manager
		can judge a flagged visit, but cannot recover one the server refused."""
		lat, lng = frappe.db.get_value("Customer", self.outlet, ["fs_latitude", "fs_longitude"]) or (0, 0)
		self.check_in_distance_m = None
		if has_coordinates(flt(lat), flt(lng)) and has_coordinates(flt(self.check_in_lat), flt(self.check_in_lng)):
			self.check_in_distance_m = distance_metres(
				flt(self.check_in_lat), flt(self.check_in_lng), flt(lat), flt(lng)
			)

		radius = flt(frappe.db.get_single_value("FS Settings", "geofence_radius_m"))
		too_far = bool(radius) and flt(self.check_in_distance_m) > radius
		self.location_flagged = 1 if too_far or self.check_in_mocked else 0

	def _set_duration(self):
		if not self.check_out_time:
			return
		if self.status == "Open":
			self.status = "Completed"
		seconds = (get_datetime(self.check_out_time) - get_datetime(self.check_in_time)).total_seconds()
		self.duration_minutes = max(seconds, 0) / 60
