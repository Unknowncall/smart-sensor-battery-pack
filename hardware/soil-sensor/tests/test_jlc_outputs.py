"""JLC order files match the parts list and the board."""
import csv
import os
import zipfile

import pytest

import export_jlc
import parts

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(HERE, "soil_sensor.kicad_pcb")


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = tmp_path_factory.mktemp("jlc")
    export_jlc.export(BOARD, str(d))
    return d


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_bom_groups_identical_parts_and_covers_every_ref(out):
    rows = read_csv(out / "BOM-JLCPCB.csv")
    keys = [(r["Comment"], r["Footprint"], r["LCSC Part #"]) for r in rows]
    assert len(keys) == len(set(keys)), "identical parts not grouped"
    refs = [d for r in rows for d in r["Designator"].split(",")]
    assert sorted(refs) == sorted(parts.PARTS)
    for r in rows:
        for ref in r["Designator"].split(","):
            assert r["LCSC Part #"] == parts.PARTS[ref].lcsc


def test_cpl_has_every_part_on_top_and_nothing_else(out):
    rows = read_csv(out / "CPL-JLCPCB.csv")
    assert sorted(r["Designator"] for r in rows) == sorted(parts.PARTS)
    assert {r["Layer"] for r in rows} == {"Top"}
    for r in rows:
        assert r["Mid X"].endswith("mm") and r["Mid Y"].endswith("mm")
        float(r["Rotation"])


def test_gerber_zip_has_all_layers_and_drills(out):
    names = zipfile.ZipFile(out / "soil_sensor-gerbers.zip").namelist()
    for layer in ("F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Paste", "F_Silkscreen",
                  "B_Silkscreen", "Edge_Cuts"):
        assert any(layer in n for n in names), f"missing {layer}"
    assert any(n.endswith("-PTH.drl") for n in names)
    assert any(n.endswith("-NPTH.drl") for n in names)


def test_extended_fee_count_is_six(out):
    rows = read_csv(out / "BOM-JLCPCB.csv")
    extended = {r["LCSC Part #"] for r in rows
                if parts.PARTS[r["Designator"].split(",")[0]].tier == "extended"}
    assert len(extended) == 6
