"""Poll device and publish values to MQTT"""

import json
import logging
from abc import ABC, abstractmethod
from argparse import Namespace

import paho.mqtt.client as mqtt

from .jtdata import JTData


class Device(ABC):
    def __init__(self, options: Namespace, jtdata: JTData, logger: logging.Logger, name="BTG065") -> None:
        super().__init__()
        self.options = options
        self.jtdata = jtdata
        self.logger = logger
        self.name = name
        self.mqtt = mqtt.Client()
        self.mqtt.username_pw_set(username=self.options.mqtt_username, password=self.options.mqtt_password)

    def initialize(self):
        self.mqtt.connect(self.options.mqtt_broker, self.options.mqtt_port, keepalive=90)

    @abstractmethod
    def _callback(self, _, raw: bytes):
        pass

    @abstractmethod
    def poll(self, seconds=60):
        pass

    def announce(self):
        for key, entry in self.jtdata.entries(self.name):
            topic = f"homeassistant/sensor/{key}/config"
            self.mqtt.publish(topic, json.dumps(entry, separators=(",", ":")), retain=True)
            self.logger.info("Announcing %s", topic)

    def publish(self):
        for key, value in self.jtdata.values():
            self.mqtt.publish(key, value, retain=True)
            self.logger.info("Publishing key=%s value=%s", key, value)
