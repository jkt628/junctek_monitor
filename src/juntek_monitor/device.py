"""Poll device and publish values to MQTT"""

import json
import logging
from abc import ABC, abstractmethod
from argparse import Namespace

from paho.mqtt import publish

from .jtdata import JTData


class Device(ABC):
    def __init__(self, options: Namespace, jtdata: JTData, logger: logging.Logger, name="BTG065") -> None:
        super().__init__()
        self.options = options
        self.jtdata = jtdata
        self.logger = logger
        self.name = name
        self.auth = {"username": self.options.mqtt_username, "password": self.options.mqtt_password}

    @abstractmethod
    def _callback(self, _, raw: bytes):
        pass

    @abstractmethod
    def poll(self, seconds=60):
        pass

    def announce(self):
        msgs = []
        for key, entry in self.jtdata.entries(self.name):
            msgs.append(
                {
                    "topic": f"homeassistant/sensor/{key}/config",
                    "payload": json.dumps(entry, separators=(",", ":")),
                    "retain": True,
                }
            )
        self.logger.info("Publishing device config=%s", msgs)
        publish.multiple(msgs, hostname=self.options.mqtt_broker, port=self.options.mqtt_port, auth=self.auth)

    def publish(self):
        msgs = []
        for key, value in self.jtdata.values():
            msgs.append({"topic": key, "payload": value})
        if not msgs:
            return
        self.logger.info("Publishing values=%s", msgs)
        publish.multiple(msgs, hostname=self.options.mqtt_broker, port=self.options.mqtt_port, auth=self.auth)
