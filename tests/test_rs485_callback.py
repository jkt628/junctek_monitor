import logging
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from juntek_monitor import config
from juntek_monitor.jtdata import JTData
from juntek_monitor.juntek485 import SerialDevice


class TestSerialDeviceCallback(unittest.TestCase):
    device: SerialDevice = None
    jtdata: JTData = None

    @classmethod
    def setUpClass(cls):
        options = config.ArgParser().parse_args()
        options.rs485 = "/dev/ttyUSB0"
        options.battery_capacity = 300
        cls.jtdata = JTData()
        cls.device = SerialDevice(options, cls.jtdata, logging.getLogger())

    def test_r50(self):
        self.device._callback(
            None,
            b":R50=1,\n"
            + b":r50=1,83,1334,120,297385,91985,739573,14353,123,4112,99,1,3426,769,\r\n"
            + b":r51=1,87,0,0,0,0,0,100,0,0,3000,100,100,100,0,0,1,\r\n",
        )
        self.assertEqual(
            list(self.jtdata.values()),
            [
                ("Juntek-Monitor/jt_batt_v", 13.34),
                ("Juntek-Monitor/jt_current", 1.2),
                ("Juntek-Monitor/jt_watts", 41.12),
                ("Juntek-Monitor/jt_batt_charging", "Charging"),
                ("Juntek-Monitor/jt_soc", 99.2),
                ("Juntek-Monitor/jt_ah_remaining", 297.385),
                ("Juntek-Monitor/jt_acc_cap", 7.4),
                ("Juntek-Monitor/jt_sec_remaining", 3426),
                ("Juntek-Monitor/jt_temp", 23),
                ("Juntek-Monitor/jt_sec_running", 14353),
            ],
        )


if __name__ == "__main__":
    unittest.main()
