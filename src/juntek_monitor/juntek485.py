import logging
import math
import os
import time
from argparse import Namespace

import serial

from .btdevice import Charging
from .device import Device
from .jtdata import JTData


class SerialDevice(Device):
    def __init__(self, options: Namespace, jtdata: JTData, logger: logging.Logger):
        super().__init__(options, jtdata, logger)
        if options.rs485 is None:
            raise ValueError("missing rs485")

    def initialize(self):
        if os.stat(self.options.rs485).st_mode & 0o170060 != 0o20060:
            raise ValueError(f"rs485 device={self.options.rs485} must be a group R/W char device")
        super().initialize()

    def _callback(self, _, raw: bytes):
        self.logger.debug("raw=%s", raw)
        values = raw.decode().split(":r50=")
        if len(values) < 2:
            self.logger.error("missing Start of Stream")
            return
        values = values[-1].split(",")
        # checksum=values[1] is not used
        self.jtdata.jt_batt_v = int(values[2]) / 100
        self.jtdata.jt_current = int(values[3]) / 100
        self.jtdata.jt_soc = math.ceil(int(values[4]) / self.options.battery_capacity) / 10
        self.jtdata.jt_ah_remaining = int(values[4]) / 1000
        # remaining capacity=values[5] is not used
        self.jtdata.jt_acc_cap = math.ceil(int(values[6]) / 1000) / 100
        self.jtdata.jt_sec_running = int(values[7])
        self.jtdata.jt_temp = int(values[8]) - 100
        self.jtdata.jt_watts = int(values[9]) / 100
        # output status=values[10] is not used
        self.jtdata.jt_batt_charging = Charging().apply(int(values[11]))
        self.jtdata.jt_sec_remaining = int(values[12])
        self.publish()

    def poll(self, seconds=60):
        with serial.Serial(self.options.rs485, baudrate=115200, timeout=1) as ser:
            ser.write(b":R50=1,2,1,\n")
            self._callback(None, ser.read_all())
