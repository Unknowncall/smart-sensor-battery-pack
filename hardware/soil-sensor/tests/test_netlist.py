"""The netlist is complete, fee-minimal, and carries the plan's safety decisions."""
import os

import pcbnew
import pytest

import netlist
import parts

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

EXTENDED_ALLOWED = {"C5366877", "C3040644", "C165948", "C194656", "C2988620", "C80628"}
REQUIRED_NETS = {
    "VBUS", "VBAT", "VCELL_P", "VCELL_N", "3V3", "GND", "SDA", "SCL", "USB_DP",
    "USB_DN", "PROBE_DRV", "PROBE_EL", "SOIL_ADC", "BAT_ADC", "EN", "BOOT",
}


def footprint_pads(fp_id):
    lib, name = fp_id.split(":")
    path = (os.path.join(HERE, "lib", "soil_sensor.pretty") if lib == "soil_sensor"
            else os.path.join(STOCK, lib + ".pretty"))
    fp = pcbnew.FootprintLoad(path, name)
    return {p.GetNumber() for p in fp.Pads() if p.GetNumber()}


def pads_on(net):
    return set(netlist.NETS[net])


def nets_of(ref, pad):
    return [n for n, members in netlist.NETS.items() if (ref, pad) in members]


def test_required_nets_exist():
    assert REQUIRED_NETS <= set(netlist.NETS)


@pytest.mark.parametrize("ref", sorted(parts.PARTS))
def test_every_pad_is_in_exactly_one_net_or_no_connect(ref):
    for pad in footprint_pads(parts.PARTS[ref].footprint):
        hits = len(nets_of(ref, pad)) + ((ref, pad) in netlist.NO_CONNECT)
        assert hits == 1, f"{ref}.{pad} appears {hits} times"


def test_every_net_member_is_a_real_pad():
    for net, members in netlist.NETS.items():
        for ref, pad in members:
            assert pad in footprint_pads(parts.PARTS[ref].footprint), f"{net}: {ref}.{pad}"


def test_no_single_pad_nets():
    for net, members in netlist.NETS.items():
        assert len({r for r, _ in members}) >= 2, f"net {net} touches one part only"


def test_tiers_and_extended_set():
    assert all(p.tier in ("basic", "preferred", "extended") for p in parts.PARTS.values())
    extended = {p.lcsc for p in parts.PARTS.values() if p.tier == "extended"}
    assert extended == EXTENDED_ALLOWED


def test_every_part_has_lcsc_code():
    assert all(p.lcsc.startswith("C") for p in parts.PARTS.values())


# --- Review Focus 1: USB alone powers the board (TP4056 BAT feeds the LDO) ---
def test_charger_output_feeds_regulator_without_cell():
    assert ("U_CHG", "5") in pads_on("VBAT")      # TP4056 BAT
    assert ("U_LDO", "1") in pads_on("VBAT")      # XC6220 VIN
    assert ("U_CHG", "4") in pads_on("VBUS")      # TP4056 VCC


# --- Review Focus 2: reversed cell can't reach the system ---
def test_reverse_cell_pfet_orientation():
    assert ("Q_REV", "3") in pads_on("VCELL_P")   # drain to holder +
    assert ("Q_REV", "2") in pads_on("VBAT")      # source to system
    assert ("BT1", "2") in pads_on("VCELL_P")     # holder pad 2 is + (MYOUNG drawing)
    assert ("BT1", "1") in pads_on("VCELL_N")


def test_protection_ic_sits_in_negative_path():
    assert ("U_PROT", "2") in pads_on("VCELL_N")
    assert {("U_PROT", "4"), ("U_PROT", "5")} <= pads_on("GND")
    assert ("U_PROT", "1") in netlist.NO_CONNECT


# --- Review Focus 3: bulk capacitance on 3V3 for WiFi bursts ---
def test_bulk_capacitance_on_3v3_at_least_22uF():
    def uf(value):
        return float(value.replace("uF", "")) if value.endswith("uF") else 0.0
    caps = {r for r, _ in pads_on("3V3") if r.startswith("C")}
    assert sum(uf(parts.PARTS[c].value) for c in caps) >= 22.0


def test_esp32_pin_assignments():
    assert ("U_MCU", "17") in pads_on("PROBE_DRV")   # IO19
    assert ("U_MCU", "27") in pads_on("SOIL_ADC")    # IO2
    assert ("U_MCU", "26") in pads_on("BAT_ADC")     # IO3
    assert ("U_MCU", "20") in pads_on("SDA")         # IO22
    assert ("U_MCU", "21") in pads_on("SCL")         # IO23
    assert ("U_MCU", "13") in pads_on("USB_DN")      # IO12
    assert ("U_MCU", "14") in pads_on("USB_DP")      # IO13
    assert ("U_MCU", "15") in pads_on("BOOT")        # IO9


def test_report_lists_every_net():
    text = netlist.report()
    for net in netlist.NETS:
        assert f"`{net}`" in text
