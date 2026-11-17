"""Every footprint the board uses loads, and has the pads the netlist will rely on."""
import os

import pcbnew
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(HERE, "lib", "soil_sensor.pretty")
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"


def load(lib, name):
    path = LOCAL if lib == "soil_sensor" else os.path.join(STOCK, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    assert fp is not None, f"{lib}:{name} did not load"
    return fp


def pad_names(fp):
    return sorted({p.GetNumber() for p in fp.Pads() if p.GetNumber()})


@pytest.mark.parametrize(
    "lib,name,expected",
    [
        ("soil_sensor", "BH-18650-B1BA002", ["1", "2"]),
        ("soil_sensor", "XB5353A_SOT-23-5", ["1", "2", "3", "4", "5"]),
        ("soil_sensor", "TP4056_ESOP-8", ["1", "2", "3", "4", "5", "6", "7", "8", "9"]),
        ("soil_sensor", "XC6220_SOT-23-5", ["1", "2", "3", "4", "5"]),
        ("soil_sensor", "SHTC3_DFN-4", ["1", "2", "3", "4", "5"]),
    ],
)
def test_local_footprint_pads(lib, name, expected):
    assert pad_names(load(lib, name)) == expected


def test_esp32_c6_mini_module_loads_with_all_pads():
    names = pad_names(load("RF_Module", "ESP32-C6-MINI-1"))
    # Module pins 1..53 plus the exposed ground pads.
    assert {str(n) for n in range(1, 54)} <= set(names)


def test_usb_c_has_cc_and_both_data_pairs():
    names = set(pad_names(load("Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12")))
    assert {"A5", "B5", "A6", "A7", "B6", "B7", "A4", "B4", "A1", "B1"} <= names


@pytest.mark.parametrize(
    "lib,name",
    [
        ("Package_TO_SOT_SMD", "SOT-23"),
        ("Resistor_SMD", "R_0402_1005Metric"),
        ("Capacitor_SMD", "C_0402_1005Metric"),
        ("Capacitor_SMD", "C_0805_2012Metric"),
        ("LED_SMD", "LED_0603_1608Metric"),
        ("Diode_SMD", "D_SOD-323"),
    ],
)
def test_stock_passives_load(lib, name):
    assert len(pad_names(load(lib, name))) >= 2
