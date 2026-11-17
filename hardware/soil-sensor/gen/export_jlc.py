"""Export JLCPCB order files: gerber zip, BOM and CPL.

    tools/kpy gen/export_jlc.py [board.kicad_pcb] [out_dir]
"""
import csv
import glob
import os
import subprocess
import sys
import tempfile
import zipfile

from parts import PARTS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KCLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def _run(*args):
    subprocess.run([KCLI, *args], check=True, capture_output=True)


def _gerbers(board, out_dir):
    with tempfile.TemporaryDirectory() as tmp:
        _run("pcb", "export", "gerbers", "-o", tmp + "/", "--layers", LAYERS,
             "--no-protel-ext", "--subtract-soldermask", board)
        _run("pcb", "export", "drill", "-o", tmp + "/", "--format", "excellon",
             "--excellon-separate-th", board)
        files = sorted(glob.glob(os.path.join(tmp, "*.gbr")) + glob.glob(os.path.join(tmp, "*.drl")))
        with zipfile.ZipFile(os.path.join(out_dir, "soil_sensor-gerbers.zip"), "w",
                             zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, os.path.basename(f))


def _bom(out_dir):
    groups = {}
    for p in PARTS.values():
        groups.setdefault((p.value, p.footprint.split(":")[1], p.lcsc), []).append(p.ref)
    with open(os.path.join(out_dir, "BOM-JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, lcsc), refs in groups.items():
            w.writerow([value, ",".join(refs), fp, lcsc])


def _cpl(board, out_dir):
    with tempfile.TemporaryDirectory() as tmp:
        pos = os.path.join(tmp, "pos.csv")
        _run("pcb", "export", "pos", "-o", pos, "--format", "csv", "--units", "mm",
             "--side", "both", board)
        with open(pos, newline="") as f:
            rows = [r for r in csv.DictReader(f) if r["Ref"] in PARTS]
    with open(os.path.join(out_dir, "CPL-JLCPCB.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm",
                        "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])


def export(board, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    _gerbers(board, out_dir)
    _bom(out_dir)
    _cpl(board, out_dir)


if __name__ == "__main__":
    export(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "soil_sensor.kicad_pcb")),
           os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "jlcpcb")))
