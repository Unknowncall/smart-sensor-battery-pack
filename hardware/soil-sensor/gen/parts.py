"""Bill of materials: every part on the soil sensor board.

LCSC codes and JLC tiers were checked against JLC's parts library on
2026-11-16. "preferred" parts carry no Extended-part fee at JLC.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Part:
    ref: str
    value: str
    footprint: str
    lcsc: str
    tier: str  # basic | preferred | extended


R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

# value -> (footprint, lcsc, tier) for the passives
_PASSIVES = {
    "100R": (R0402, "C25076", "basic"),
    "1k": (R0402, "C11702", "basic"),
    "2.4k": (R0402, "C25882", "preferred"),
    "5.1k": (R0402, "C25905", "basic"),
    "10k": (R0402, "C25744", "basic"),
    "100k": (R0402, "C25741", "basic"),
    "1M": (R0402, "C26083", "basic"),
    "100nF": (C0402, "C1525", "basic"),
    "1uF": (C0402, "C52923", "basic"),
    "10uF": (C0805, "C15850", "basic"),
    "22uF": (C0805, "C45783", "basic"),
}


def _p(ref, value):
    fp, lcsc, tier = _PASSIVES[value]
    return Part(ref, value, fp, lcsc, tier)


_PARTS = [
    # Fee-bearing (Extended) parts: exactly the six the design allows.
    Part("U_MCU", "ESP32-C6-WROOM-1-N8", "soil_sensor:ESP32-C6-WROOM-1", "C5366877", "extended"),
    Part("U_LDO", "XC6220B331MR", "soil_sensor:XC6220_SOT-23-5", "C3040644", "extended"),
    Part("J_USB", "TYPE-C-31-M-12", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948", "extended"),
    Part("U_RH", "SHTC3", "soil_sensor:SHTC3_DFN-4", "C194656", "extended"),
    Part("BT1", "BH-18650-B1BA002", "soil_sensor:BH-18650-B1BA002", "C2988620", "extended"),
    Part("U_PROT", "XB5353A", "soil_sensor:XB5353A_SOT-23-5", "C80628", "extended"),
    # No-fee actives
    Part("U_CHG", "TP4056", "soil_sensor:TP4056_ESOP-8", "C16581", "preferred"),
    Part("Q_REV", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", "basic"),
    Part("D_PROBE", "1N4148WS", "Diode_SMD:D_SOD-323", "C2128", "basic"),
    Part("LED_CHG", "Red", "LED_SMD:LED_0603_1608Metric", "C2286", "basic"),
    # USB-C
    _p("R_CC1", "5.1k"), _p("R_CC2", "5.1k"),
    # Charger
    _p("R_PROG", "2.4k"), _p("R_LED", "1k"), _p("C_VBUS", "10uF"), _p("C_VBAT", "10uF"),
    # Protection / reverse cell
    _p("R_PROT", "100R"), _p("C_PROT", "100nF"), _p("R_QG", "100k"),
    # Regulator and 3V3 rail
    _p("C_LDOIN", "1uF"), _p("C_LDOOUT", "1uF"), _p("C_BULK", "22uF"),
    _p("C_MCU1", "10uF"), _p("C_MCU2", "100nF"),
    # ESP32 support
    _p("R_EN", "10k"), _p("C_EN", "1uF"), _p("R_BOOT", "10k"), _p("R_IO8", "10k"),
    # I2C / SHTC3
    _p("R_SDA", "10k"), _p("R_SCL", "10k"), _p("C_RH", "100nF"),
    # Battery sense
    _p("R_BAT1", "1M"), _p("R_BAT2", "1M"), _p("C_BATADC", "100nF"),
    # Soil probe front end
    _p("R_DRV", "1k"), _p("R_SOIL", "1M"), _p("C_SOIL", "100nF"),
]

PARTS = {p.ref: p for p in _PARTS}
assert len(PARTS) == len(_PARTS), "duplicate reference designator"
