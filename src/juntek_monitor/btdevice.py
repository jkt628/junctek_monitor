"""poll BLE and decode values"""

import asyncio
import datetime
import logging
import signal
import traceback
from argparse import Namespace
from typing import Final, NamedTuple

from bleak import BleakClient, BleakError, BleakScanner, BLEDevice

from .device import Device
from .jtdata import JTData


class DeviceNotFoundException(Exception):
    pass


def _add_signal_handlers():
    loop = asyncio.get_event_loop()

    async def shutdown():
        """
        Cancel all running async tasks (other than this one) when called.
        By catching asyncio.CancelledError, any running task can perform
        any necessary cleanup when it's cancelled.
        """
        tasks = []
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task(loop):
                task.cancel()
                tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))


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
        "D5": Parameter("jt_sec_running", Operator()),
        "D6": Parameter("jt_sec_remaining", Operator()),
        "D8": Parameter("jt_watts", Divide(100)),
        "D9": Parameter("jt_temp", Subtract(100)),
        "B1": Parameter("battery_capacity", Divide(10)),
    }

    def __init__(self, options: Namespace, jtdata: JTData, logger: logging.Logger) -> None:
        super().__init__(options, jtdata, logger)
        if options.juntek_addr is None:
            raise ValueError("missing juntek_addr")
        self.bleDevice: BLEDevice = None

    def initialize(self):
        self.bleDevice = asyncio.run(self._locate_device(self.options.poll))
        self.name = self.bleDevice.name
        self.logger.info("Located JUNTEK device - name=%s address=%s", self.name, self.bleDevice.address)

    def _callback(self, _, raw: bytes):
        data = str(raw.hex()).upper()
        self.logger.debug("data=%s", data)

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
                self.logger.debug("%s=%s", parameter.name, self.jtdata.__dict__[parameter.name])
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

    async def _locate_device(self, seconds):
        expire = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        self.logger.debug("Scanning for JUNTEK device address=%s until %s", self.options.juntek_addr, expire)
        while True:
            device = await BleakScanner.find_device_by_address(self.options.juntek_addr)
            if device is not None:
                return device
            if datetime.datetime.now() > expire:
                raise DeviceNotFoundException(
                    "Couldn't find BLE device - is it in range? is another client connected? "
                    + "Check 'hcitool con' and force disconnect if necessary"
                )
            await asyncio.sleep(5)

    async def _poll(self, seconds=60):
        _add_signal_handlers()

        async with BleakClient(self.bleDevice, timeout=20) as client:
            await client.start_notify(self.RX_CHARACTERISTIC, self._callback)
            while True:
                try:
                    if not client.is_connected:
                        self.logger.warning("No connection... Attempting to reconnect")
                        await client.connect()
                        await client.start_notify(self.RX_CHARACTERISTIC, self._callback)
                except EOFError:
                    self.logger.warning("DBus EOFError")
                except asyncio.exceptions.TimeoutError:
                    self.logger.warning("asyncio TimeOutError communicating with device")
                except BleakError as _err:
                    self.logger.warning("BleakError - %s", _err)
                except Exception as _err:
                    self.logger.warning(
                        "Error querying Juntek: %s, %s %s",
                        _err,
                        type(_err),
                        traceback.format_exc(),
                    )

                if not seconds:  # one-shot run, don't loop
                    break

                await asyncio.sleep(seconds)

    def poll(self, seconds=60):
        asyncio.run(self._poll(seconds))
