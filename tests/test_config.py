import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from juntek_monitor import config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = config.ArgParser().parse_args()

    def test_config(self):
        self.assertEqual(self.config.debug, False)
        self.assertEqual(self.config.mqtt_broker, "localhost")
        self.assertEqual(self.config.mqtt_port, 1883)
        self.assertEqual(self.config.mqtt_username, "user")
        self.assertEqual(self.config.mqtt_password, "pass")
        self.assertEqual(self.config.battery_capacity, 200)
        self.assertEqual(self.config.juntec_addr, None)
        self.assertEqual(self.config.rs485, "/dev/ttyUSB0")

    def test_env(self):
        os.environ["BATTERY_CAPACITY"] = "300"
        os.environ["JUNTEC_ADDR"] = "aa:bb:cc:dd:ee:ff"
        self.config = config.ArgParser().parse_args()
        self.assertEqual(self.config.battery_capacity, int(os.getenv("BATTERY_CAPACITY")))
        self.assertEqual(self.config.juntec_addr, os.getenv("JUNTEC_ADDR"))


if __name__ == "__main__":
    unittest.main()
