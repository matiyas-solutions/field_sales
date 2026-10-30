import unittest

from field_sales.utils import distance_metres, has_coordinates, stock_status


class TestUtils(unittest.TestCase):
	def test_stock_status(self):
		self.assertEqual(stock_status(0, 10), "Stockout")
		self.assertEqual(stock_status(5, 10), "Low")
		self.assertEqual(stock_status(10, 10), "OK")
		self.assertEqual(stock_status(1, 0), "OK")

	def test_distance(self):
		self.assertAlmostEqual(distance_metres(23.0, 72.0, 23.0, 72.0), 0)
		self.assertAlmostEqual(distance_metres(23.0, 72.0, 23.01, 72.0), 1112, delta=5)

	def test_untagged_outlet_has_no_coordinates(self):
		self.assertFalse(has_coordinates(0, 0))
		self.assertFalse(has_coordinates(None, None))
		self.assertTrue(has_coordinates(23.0, 0))
