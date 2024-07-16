"""Data collected from Juntek Battery Monitor"""

class JTData:
    """Data collected from Juntek Battery Monitor"""

    def __init__(self) -> None:
        self.jt_ah_remaining = 0.0
        self.jt_batt_v = 0.0
        self.jt_current = 0.0
        self.jt_min_remaining = 0
        self.jt_soc = 0.0
        self.jt_temp = 0
        self.jt_watts = 0.0
