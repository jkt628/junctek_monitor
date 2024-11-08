"""poll BLE and decode values"""

import logging
from argparse import Namespace
from typing import Final, NamedTuple

from .device import Device
from .jtdata import JTData


class Operator:
    def __init__(self, operand: float = 1):
        self.operand = operand

    def apply(self, value: int):
        return value  # identity


class Charging(Operator):
    CHARGING: Final[list[str]] = ["Discharging", "Charging"]

    def apply(self, value: int):
        return self.CHARGING[value]


class Divide(Operator):
    def apply(self, value: int):
        return value / self.operand


class Time(Operator):
    def apply(self, value: int):
        value, seconds = divmod(value, 60)
        value, minutes = divmod(value, 60)
        value, hours = divmod(value, 24)
        return f"{value}d {hours:02d}:{minutes:02d}:{seconds:02d}"


class Subtract(Operator):
    def apply(self, value: int):
        return value - self.operand


class Parameter(NamedTuple):
    name: str
    operator: Operator


class BTDevice(Device):
    """
    The format of Bluetooth records:
    * Start of stream (0xBB)
    * One or more values:
      * Value in integer where each nybble (half byte) is a digit (1 or more bytes)
      * Function code (1 byte)
    * CRC (1 byte)
    * End of stream (0xEE)

    Example:
    BB 13 34 C0 20 01 D8 99 EE

    BB = start of stream
    13 34 = value 1334
    C0 = function code (battery voltage)
    20 01 = value 2001
    D8 = function code (watts)
    99 = CRC
    EE = end of stream
    """

    RX_CHARACTERISTIC: Final = "0000fff1-0000-1000-8000-00805f9b34fb"
    START_OF_STREAM: Final = "BB"
    END_OF_STREAM: Final = "EE"
    PARAMETERS: Final[dict[str, Parameter]] = {
        "C0": Parameter("jt_batt_v", Divide(100)),
        "C1": Parameter("jt_current", Divide(100)),
        "D1": Parameter("jt_batt_charging", Charging()),
        "D2": Parameter("jt_ah_remaining", Divide(1000)),
        "D3": Parameter("discharge", Divide(100000)),
        "D4": Parameter("jt_acc_cap", Divide(100000)),
        "D5": Parameter("jt_running", Time()),
        "D6": Parameter("jt_min_remaining", Operator()),
        "D8": Parameter("jt_watts", Divide(100)),
        "D9": Parameter("jt_temp", Subtract(100)),
        "B1": Parameter("battery_capacity", Divide(10)),
    }

    def __init__(self, options: Namespace, jtdata: JTData, logger: logging.Logger) -> None:
        super().__init__(options, jtdata)
        if options.juntek_addr is None:
            raise ValueError("missing juntek_addr")
        self.logger = logger

    def _callback(self, raw: bytes):
        data = str(raw.hex()).upper()
        self.logger.debug("data: %s", data)

        # basic checks
        if not data.startswith(self.START_OF_STREAM):
            self.logger.error("missing Start of Stream")
            return
        if not data.endswith(self.END_OF_STREAM):
            self.logger.error("missing End of Stream")
            return

        self.jtdata.reset()

        # chunk it to two character strings, each represents one byte
        b = [data[i : i + 2] for i in range(0, len(data), 2)]
        # parse it backwards and collect values
        i = len(b) - 1
        while i > 0:
            if b[i] in self.PARAMETERS:
                parameter = self.PARAMETERS[b[i]]
                value = ""
                i -= 1
                while b[i].isdigit():
                    value = b[i] + value
                    i -= 1
                self.jtdata.__dict__[parameter.name] = parameter.operator.apply(int(value))
                self.logger.debug("%s: %s", parameter.name, self.jtdata.__dict__[parameter.name])
            elif b[i] == self.END_OF_STREAM:
                # sometimes multiple reports concatenate
                i -= 2  # skip CRC
            else:
                i -= 1

        if self.jtdata.jt_ah_remaining is not None:
            self.jtdata.jt_soc = int(100 * self.jtdata.jt_ah_remaining / self.options.battery_capacity)
            # in my experience, 'discharging' always appears with 'jt_ah_remaining'
            self.jtdata.jt_batt_charging = Charging().apply(not hasattr(self.jtdata, "discharge"))

        self.publish()

    def poll(self, seconds=60):
        self.values["BTG065"] = self.ble.read(self.RX_CHARACTERISTIC)
