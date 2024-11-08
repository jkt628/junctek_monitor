import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from juntek_monitor import config
from juntek_monitor.btdevice import BTDevice
from juntek_monitor.device import Device
from juntek_monitor.jtdata import JTData


def main():
    options = config.ArgParser().parse_args()
    logging.basicConfig(
        format="%(asctime)s %(name)s[%(process)d]: %(levelname)s: %(message)s",
        level=logging.DEBUG if options.debug else logging.INFO,
    )
    logger = logging.getLogger(os.path.basename(os.path.dirname(__file__)))
    logger.debug("options: %s", options)

    device: Device = None
    if options.juntek_addr is not None:
        device = BTDevice(options, JTData(), logger)
    elif options.rs485 is not None:
        # device = SerialDevice(options, JTData())
        pass
    else:
        raise ValueError("must specify juntek_addr or rs485")
    device.announce()
    device.poll(options.poll)


if __name__ == "__main__":
    main()
