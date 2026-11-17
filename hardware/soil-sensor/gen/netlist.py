"""Connections on the soil sensor board: net name -> [(ref, pad), ...].

Pin maps come from each part's datasheet / KiCad footprint:
- ESP32-C6-MINI-1: KiCad RF_Module symbol (pin 5 IO2, 6 IO3, 8 EN, 17 IO12/D-,
  18 IO13/D+, 22 IO8, 23 IO9, 25 IO19, 28 IO22, 29 IO23; GND 1,2,11,14,36-53).
- TYPE-C-31-M-12: USB-C standard pinout (A5/B5 CC, A6/B6 D+, A7/B7 D-).
- TP4056 ESOP-8: 1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT, 6 STDBY, 7 CHRG, 8 CE, 9 EP.
- XB5353A (XySemi REV0.4 p.2): 1 VT (vendor test, unused), 2 GND, 3 VDD, 4/5 VM.
  Application circuit p.1: VDD via 100R to BAT+, 100nF VDD-GND.
- XC6220 SOT-23-5 (LCSC C3040644): 1 VIN, 2 GND, 3 CE, 4 NC, 5 VOUT.
- SHTC3 (Sensirion): 1 VDD, 2 SCL, 3 SDA, 4 VSS, 5 exposed pad (to VSS).
- BH-18650-B1BA002 (MYOUNG WD-CP-0088): pad 2 is +, beside the locating peg.
- AO3401A SOT-23: 1 G, 2 S, 3 D. Diodes/LEDs: pad 1 cathode, pad 2 anode.
"""
from parts import PARTS


def _two(ref, a, b):
    """A two-pad part between nets a (pad 1) and b (pad 2)."""
    return [(a, (ref, "1")), (b, (ref, "2"))]


_GND_MCU = ["1", "2", "11", "14"] + [str(n) for n in range(36, 54)]

_CONNECTIONS = [
    # --- USB-C ---
    *[("GND", ("J_USB", p)) for p in ("A1", "A12", "B1", "B12", "SH")],
    *[("VBUS", ("J_USB", p)) for p in ("A4", "A9", "B4", "B9")],
    ("CC1", ("J_USB", "A5")), ("CC2", ("J_USB", "B5")),
    ("USB_DP", ("J_USB", "A6")), ("USB_DP", ("J_USB", "B6")),
    ("USB_DN", ("J_USB", "A7")), ("USB_DN", ("J_USB", "B7")),
    *_two("R_CC1", "CC1", "GND"), *_two("R_CC2", "CC2", "GND"),
    # --- Charger (TP4056) ---
    ("GND", ("U_CHG", "1")), ("PROG", ("U_CHG", "2")), ("GND", ("U_CHG", "3")),
    ("VBUS", ("U_CHG", "4")), ("VBAT", ("U_CHG", "5")), ("CHRG_N", ("U_CHG", "7")),
    ("VBUS", ("U_CHG", "8")), ("GND", ("U_CHG", "9")),
    *_two("R_PROG", "PROG", "GND"),
    ("CHRG_N", ("LED_CHG", "1")), ("LED_A", ("LED_CHG", "2")),
    *_two("R_LED", "LED_A", "VBUS"),
    *_two("C_VBUS", "VBUS", "GND"), *_two("C_VBAT", "VBAT", "GND"),
    # --- Cell, protection, reverse-cell FET ---
    ("VCELL_N", ("BT1", "1")), ("VCELL_P", ("BT1", "2")),
    ("VCELL_N", ("U_PROT", "2")), ("PROT_VDD", ("U_PROT", "3")),
    ("GND", ("U_PROT", "4")), ("GND", ("U_PROT", "5")),
    *_two("R_PROT", "VCELL_P", "PROT_VDD"), *_two("C_PROT", "PROT_VDD", "VCELL_N"),
    ("QG", ("Q_REV", "1")), ("VBAT", ("Q_REV", "2")), ("VCELL_P", ("Q_REV", "3")),
    *_two("R_QG", "QG", "GND"),
    # --- Regulator ---
    ("VBAT", ("U_LDO", "1")), ("GND", ("U_LDO", "2")), ("VBAT", ("U_LDO", "3")),
    ("3V3", ("U_LDO", "5")),
    *_two("C_LDOIN", "VBAT", "GND"), *_two("C_LDOOUT", "3V3", "GND"),
    *_two("C_BULK", "3V3", "GND"), *_two("C_MCU1", "3V3", "GND"), *_two("C_MCU2", "3V3", "GND"),
    # --- ESP32-C6 ---
    *[("GND", ("U_MCU", p)) for p in _GND_MCU],
    ("3V3", ("U_MCU", "3")), ("EN", ("U_MCU", "8")),
    ("SOIL_ADC", ("U_MCU", "5")), ("BAT_ADC", ("U_MCU", "6")),
    ("USB_DN", ("U_MCU", "17")), ("USB_DP", ("U_MCU", "18")),
    ("IO8", ("U_MCU", "22")), ("BOOT", ("U_MCU", "23")),
    ("PROBE_DRV", ("U_MCU", "25")), ("SDA", ("U_MCU", "28")), ("SCL", ("U_MCU", "29")),
    *_two("R_EN", "EN", "3V3"), *_two("C_EN", "EN", "GND"),
    *_two("R_BOOT", "BOOT", "3V3"), *_two("R_IO8", "IO8", "3V3"),
    # --- SHTC3 + I2C ---
    ("3V3", ("U_RH", "1")), ("SCL", ("U_RH", "2")), ("SDA", ("U_RH", "3")),
    ("GND", ("U_RH", "4")), ("GND", ("U_RH", "5")),
    *_two("R_SDA", "SDA", "3V3"), *_two("R_SCL", "SCL", "3V3"), *_two("C_RH", "3V3", "GND"),
    # --- Battery sense ---
    *_two("R_BAT1", "VBAT", "BAT_ADC"), *_two("R_BAT2", "BAT_ADC", "GND"),
    *_two("C_BATADC", "BAT_ADC", "GND"),
    # --- Soil probe: PWM -> 1k -> electrode -> diode -> hold cap/bleed -> ADC ---
    *_two("R_DRV", "PROBE_DRV", "PROBE_EL"),
    ("SOIL_ADC", ("D_PROBE", "1")), ("PROBE_EL", ("D_PROBE", "2")),
    *_two("C_SOIL", "SOIL_ADC", "GND"), *_two("R_SOIL", "SOIL_ADC", "GND"),
]

NO_CONNECT = {
    ("J_USB", "A8"), ("J_USB", "B8"),          # SBU
    ("U_CHG", "6"),                            # STDBY
    ("U_PROT", "1"),                           # VT, vendor test pin
    ("U_LDO", "4"),                            # NC
    # ESP32 module: NC pins and unused GPIOs (IO4, IO5, IO0, IO1, IO6, IO7,
    # IO14, IO15, IO18, IO20, IO21, RXD0, TXD0)
    *[("U_MCU", p) for p in ("4", "7", "21", "32", "33", "34", "35",
                             "9", "10", "12", "13", "15", "16", "19", "20",
                             "24", "26", "27", "30", "31")],
}

NETS = {}
for _net, _member in _CONNECTIONS:
    NETS.setdefault(_net, []).append(_member)

_unknown = {ref for members in NETS.values() for ref, _ in members} - set(PARTS)
assert not _unknown, f"netlist references unknown parts: {_unknown}"


def report() -> str:
    """Markdown netlist for human review."""
    lines = ["# Soil sensor netlist", "", "Generated from `gen/netlist.py`. Do not edit by hand.", ""]
    for net in sorted(NETS):
        members = ", ".join(f"{r}.{p}" for r, p in NETS[net])
        lines.append(f"- `{net}`: {members}")
    lines += ["", "## Not connected", ""]
    lines += [f"- {r}.{p}" for r, p in sorted(NO_CONNECT)]
    lines += ["", "## Parts", "", "| Ref | Value | LCSC | JLC tier |", "|---|---|---|---|"]
    lines += [f"| {p.ref} | {p.value} | {p.lcsc} | {p.tier} |" for p in PARTS.values()]
    return "\n".join(lines) + "\n"
