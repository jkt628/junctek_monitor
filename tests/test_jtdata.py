import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from juntek_monitor.jtdata import JTData

jtdata = JTData()


class TestJTData(unittest.TestCase):
    def test_00_entries(self):
        """ensure a few known entries are present"""
        known = {
            "jt_batt_v": False,
            "jt_current": False,
            "jt_sec_running": False,
        }
        for key, _ in jtdata.entries():
            known[key] = True
        for key, value in known.items():
            self.assertTrue(value, msg=f"Missing {key}")

    def test_00_values(self):
        self.assertEqual(list(jtdata.values()), [])

    def test_10_setup(self):
        jtdata.jt_batt_v = 12.5

    def test_11_values(self):
        self.assertEqual(list(jtdata.values()), [("Juntek-Monitor/jt_batt_v", 12.5)])

    def test_19_reset(self):
        jtdata.reset()
        self.test_00_values()

    def test_20_setup(self):
        jtdata.jt_current = 30.2

    def test_21_values(self):
        self.assertEqual(list(jtdata.values()), [("Juntek-Monitor/jt_current", 30.2)])

    def test_29_reset(self):
        jtdata.reset()
        self.test_00_values()

    def test_30_setup(self):
        jtdata.jt_batt_v = 12.5
        jtdata.jt_current = 30.2

    def test_31_values(self):
        self.assertEqual(
            list(jtdata.values()), [("Juntek-Monitor/jt_batt_v", 12.5), ("Juntek-Monitor/jt_current", 30.2)]
        )

    def test_39_reset(self):
        jtdata.reset()
        self.test_00_values()


if __name__ == "__main__":
    unittest.main()
