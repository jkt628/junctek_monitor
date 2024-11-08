"""Data collected from Juntek Battery Monitor for MQTT"""

import os

import yaml


class JTData:
    def __init__(self) -> None:
        with open(os.path.join(os.path.dirname(__file__), "jt_mqtt.yaml"), "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
            for entry in self.data:
                if "unique_id" not in entry:
                    # required for mapping to a device
                    entry["unique_id"] = entry["object_id"]
                if "platform" not in entry:
                    entry["platform"] = "mqtt"
                if "expire_after" not in entry:
                    entry["expire_after"] = 180
                if "state_topic" not in entry:
                    entry["state_topic"] = f"Juntek-Monitor/{entry['unique_id']}"
                if "device" not in entry:
                    entry["device"] = {
                        "name": "Juntek Monitor",
                    }
                setattr(self, entry["unique_id"], None)

    def reset(self) -> None:
        """Reset values"""
        for entry in self.data:
            setattr(self, entry["unique_id"], None)

    def entries(self, identifier="BTG065"):
        """Yield entries for MQTT"""
        for entry in self.data:
            entry["device"]["identifiers"] = identifier
            yield entry["unique_id"], entry

    def values(self):
        """Yield interesting values for MQTT"""
        for entry in self.data:
            key = entry["unique_id"]
            if not key.startswith("jt_"):
                continue
            value = getattr(self, key)
            if value is not None:
                yield entry["state_topic"], value
