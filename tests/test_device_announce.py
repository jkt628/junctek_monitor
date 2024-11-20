import logging
import os
import sys
import unittest
from argparse import Namespace
from unittest.mock import Mock, call

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from juntek_monitor import config
from juntek_monitor.device import Device
from juntek_monitor.jtdata import JTData


class Concrete(Device):
    def _callback(self, _, raw: bytes):
        return super()._callback(_, raw)

    def poll(self, seconds=60):
        return super().poll(seconds)


class TestDeviceAnnounce(unittest.TestCase):
    options: Namespace = None
    jtdata: JTData = None

    @classmethod
    def setUpClass(cls):
        cls.options = config.ArgParser().parse_args()
        cls.options.juntek_addr = "aa:bb:cc:dd:ee:ff"
        cls.options.battery_capacity = 300
        cls.jtdata = JTData()

    def test_announce(self):
        device = Concrete(self.options, self.jtdata, logging.getLogger())
        device.mqtt.publish = Mock()
        device.announce()
        device.mqtt.publish.assert_has_calls(
            [
                call(
                    "homeassistant/sensor/jt_batt_v/config",
                    '{"name":"Battery Voltage","object_id":"jt_batt_v","device_class":"voltage","unit_of_measurement":"V","unique_id":"jt_batt_v","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_batt_v","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_current/config",
                    '{"name":"Battery Current","object_id":"jt_current","device_class":"current","unit_of_measurement":"A","unique_id":"jt_current","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_current","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_watts/config",
                    '{"name":"Battery Charging Power","object_id":"jt_watts","device_class":"power","unit_of_measurement":"W","unique_id":"jt_watts","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_watts","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_batt_charging/config",
                    '{"name":"Battery Charging","object_id":"jt_batt_charging","device_class":"enum","options":["Charging","Discharging"],"unique_id":"jt_batt_charging","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_batt_charging","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_soc/config",
                    '{"name":"State of Charge","object_id":"jt_soc","device_class":"battery","unit_of_measurement":"%","unique_id":"jt_soc","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_soc","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_ah_remaining/config",
                    '{"name":"Ah Remaining","object_id":"jt_ah_remaining","device_class":"energy","unit_of_measurement":"Ah","unique_id":"jt_ah_remaining","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_ah_remaining","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_acc_cap/config",
                    '{"name":"Accumulated Capacity","object_id":"jt_acc_cap","device_class":"energy_storage","unit_of_measurement":"kWh","unique_id":"jt_acc_cap","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_acc_cap","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_sec_remaining/config",
                    '{"name":"Estimated Remaining Time","object_id":"jt_sec_remaining","device_class":"duration","unit_of_measurement":"s","unique_id":"jt_sec_remaining","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_sec_remaining","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_temp/config",
                    '{"name":"Temperature","object_id":"jt_temp","device_class":"temperature","unit_of_measurement":"C","unique_id":"jt_temp","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_temp","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
                call(
                    "homeassistant/sensor/jt_sec_running/config",
                    '{"name":"Running Time","object_id":"jt_sec_running","device_class":"duration","unit_of_measurement":"s","unique_id":"jt_sec_running","platform":"mqtt","expire_after":180,"state_topic":"Juntek-Monitor/jt_sec_running","device":{"name":"Juntek Monitor","identifiers":"BTG065"}}',
                    retain=True,
                ),
            ]
        )


if __name__ == "__main__":
    unittest.main()
