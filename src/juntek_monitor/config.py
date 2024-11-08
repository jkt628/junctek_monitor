import argparse
import os

import configargparse


def ArgParser() -> argparse.ArgumentParser:
    parser = configargparse.ArgParser(
        default_config_files=[
            os.path.join(os.path.dirname(__file__), "config.ini"),
            os.path.join("~", ".config", os.path.split(os.path.split(__file__)[0])[1], "config.ini"),
        ]
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--mqtt_broker", type=str, env_var="MQTT_BROKER", default="localhost")
    parser.add_argument("--mqtt_port", type=int, env_var="MQTT_PORT", default=1883)
    parser.add_argument("--mqtt_username", type=str, env_var="MQTT_USERNAME")
    parser.add_argument("--mqtt_password", type=str, env_var="MQTT_PASSWORD")
    parser.add_argument("--battery_capacity", type=int, env_var="BATTERY_CAPACITY", required=True)
    parser.add_argument("--poll", "-i", type=int, env_var="POLL_INTERVAL", default=60)
    parser.add_argument("--juntek_addr", type=str, env_var="JUNTEK_ADDR")
    parser.add_argument("--rs485", type=str, env_var="RS485")

    return parser
