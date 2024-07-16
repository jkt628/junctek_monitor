#!/usr/bin/env python
import argparse
import json
import logging
import math
import time

from paho.mqtt import publish
import serial
import yaml

from . import config, JT_MQTT_YAML
from .jtdata import JTData

logger = logging.getLogger("Juntek KF Coulometer")
logger.setLevel(logging.INFO)
auth = {"username": config.MQTT_USER, "password": config.MQTT_PASS}


class JTInfo:
    def __init__(self, args: argparse.Namespace) -> None:
        self.data = JTData()
        self.name = "Juntek Monitor"
        self.args = args
        # Capture data from RS485
        with serial.Serial(config.RS485, baudrate=115200, timeout=1) as serial_handle:
            get_values_str = b":R50=1,2,1,\n"
            serial_handle.write(get_values_str)
            byte_string = serial_handle.readline()
            print(byte_string)
        # split CSV
        string = byte_string.decode()
        string = string.strip()
        values = string.split(",")
        # Calculations
        calc_watts = int(values[2]) * int(values[3]) / 10000

        # Formatting the data
        self.data.jt_batt_v = int(values[2]) / 100
        self.data.jt_current = int(values[3]) / 100
        self.data.jt_watts = math.ceil(calc_watts * 100) / 100
        # self.data.jt_batt_charging = int(values[11])
        self.data.jt_soc = math.ceil(int(values[4]) / config.BATT_CAP) / 10
        self.data.jt_ah_remaining = int(values[4]) / 1000
        self.data.jt_acc_cap = math.ceil(int(values[6]) / 1000) / 100
        self.data.jt_min_remaining = math.ceil(int(values[7]) / 60)
        self.data.jt_temp = int(values[8]) - 100

        # Negative values if Discharging (0)
        if int(values[11]) == 0:
            self.data.jt_watts_neg = self.data.jt_watts
            self.data.jt_watts = 0
        else:
            self.data.jt_watts = self.data.jt_watts
            self.data.jt_watts_neg = 0

        # Output values on screen
        #       for k, v in self.data.__dict__.items():
        #           print(f"{k} = {v}")

        #    def publish(self):

        # Publish Home Assistant discovery info to MQTT on every run
        logger.info("Publishing Discovery information to Home Assistant")

        with open(JT_MQTT_YAML, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)
            for entry in y:
                if "unique_id" not in entry:
                    # required for mapping to a device
                    entry["unique_id"] = entry["object_id"]
                if "platform" not in entry:
                    entry["platform"] = "mqtt"
                if "expire_after" not in entry:
                    entry["expire_after"] = 90
                if "state_topic" not in entry:
                    entry["state_topic"] = f"Juntek-Monitor/{entry['unique_id']}"
                if "device" not in entry:
                    entry["device"] = {
                        "name": "Juntek Monitor",
                        "identifiers": "BTG065",
                    }

                logger.debug(
                    "DISCOVERY_PUB=homeassistant/sensor/%s/config\nPL=%s\n",
                    entry["object_id"],
                    json.dumps(entry),
                )
                publish.single(
                    topic=f"homeassistant/sensor/{entry['object_id']}/config",
                    payload=json.dumps(entry),
                    retain=True,
                    hostname=config.MQTT_HOST,
                    auth=auth,
                )

        # Combine sensor updates for MQTT
        mqtt_msgs = []
        for k, v in self.data.__dict__.items():
            mqtt_msgs.append({"topic": f"Juntek-Monitor/{k}", "payload": v})
            if not self.args.quiet:
                print(f"{k} = {v}")
        publish.multiple(mqtt_msgs, hostname=config.MQTT_HOST, auth=auth)
        logger.info("Published updated sensor stats to MQTT")


def main():
    if hasattr(config, "JT_LOG_FILE"):
        logging.basicConfig(
            filename=config.JT_LOG_FILE,
            format="%(asctime)s %(levelname)s:%(message)s",
            encoding="utf-8",
            level=logging.WARNING,
        )

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        help="Run nonstop and query the device every <interval> seconds",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet mode. No output except for errors"
    )
    args = parser.parse_args()

    if args.debug:
        logger.warning("Setting logging level to DEBUG")
        logger.setLevel(logging.DEBUG)

    if not args.quiet:
        logger.addHandler(logging.StreamHandler())

    logger.info("Starting up")

    while True:
        try:
            JTInfo(args)
            if not args.interval:
                break
            time.sleep(args.interval)
        except Exception as err:
            logger.warning(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Error : %s, %s",
                err,
                type(err),
            )
            time.sleep(5)


if __name__ == "main":
    main()