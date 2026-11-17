"""Build soil_sensor.kicad_pcb from parts.PARTS and netlist.NETS.

Board coordinates in this file are millimetres from the board's top-left
corner, x to the right, y down (towards the soil). Run:

    tools/kpy gen/build_board.py soil_sensor.kicad_pcb
"""
import os
import subprocess
import sys

import pcbnew

from netlist import NETS
from parts import PARTS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
LOCAL_LIB = os.path.join(HERE, "lib", "soil_sensor.pretty")
KCLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

ORIGIN = (50.0, 50.0)          # where the board sits on the KiCad page
WIDTH, LENGTH = 25.0, 210.0
TIP_START = 198.0              # outline narrows to a point from here
FILL_LINE_Y_MM = 140.0         # max insertion depth; nothing but the electrode below
MCU_Y = 11.15                  # module origin; antenna top lands on the board edge
KEEPOUT_RECT_MM = (0.0, 0.0, WIDTH, MCU_Y - 5.6)   # module's antenna keep-out on the board
ELECTRODE = (7.5, 142.0, 17.5, 195.0)               # x0, y0, x1, y1 on F.Cu, under mask

# ref: (x, y, rotation_degrees)
PLACEMENT = {
    "U_MCU": (12.5, MCU_Y, 0),
    # left of the module
    "R_EN": (2.6, 7.2, 0), "C_EN": (2.6, 8.6, 0), "R_BOOT": (2.6, 10.0, 0),
    "R_IO8": (2.6, 11.4, 0), "R_SDA": (2.6, 12.8, 0), "R_SCL": (2.6, 14.2, 0),
    # right of the module
    "C_MCU2": (22.4, 7.2, 0), "C_MCU1": (22.4, 9.4, 0), "C_BULK": (22.4, 12.0, 0),
    "C_LDOOUT": (22.4, 14.4, 0),
    # USB-C, mating face on the left edge
    "J_USB": (3.7, 23.0, -90),
    # charger / regulator block
    "U_CHG": (13.2, 23.4, 0), "C_VBUS": (18.6, 19.6, 0), "C_VBAT": (18.6, 22.0, 0),
    "R_PROG": (18.3, 24.2, 0), "R_LED": (18.3, 25.6, 0), "LED_CHG": (18.6, 27.2, 0),
    "U_LDO": (22.7, 19.9, 90), "C_LDOIN": (22.7, 23.0, 0),
    "R_CC1": (10.6, 18.6, 0), "R_CC2": (10.6, 28.2, 0),
    # row between the charger and the holder
    "R_BAT1": (12.6, 30.6, 0), "R_BAT2": (14.6, 30.6, 0), "C_BATADC": (16.6, 30.6, 0),
    "Q_REV": (20.6, 30.9, 0), "R_QG": (23.9, 30.9, 90),
    # the cell
    "BT1": (12.5, 77.0, 0),
    # protection, probe front end and SHTC3 below the holder
    "U_PROT": (5.0, 124.0, 0), "C_PROT": (5.0, 127.2, 0), "R_PROT": (8.6, 124.0, 90),
    "R_DRV": (11.5, 127.0, 0), "D_PROBE": (12.5, 130.0, 0),
    "C_SOIL": (10.5, 133.0, 0), "R_SOIL": (13.5, 133.0, 0),
    "U_RH": (21.8, 131.0, 0), "C_RH": (21.8, 134.8, 0),
}

# L-shaped slot that puts the SHTC3 on a peninsula (thermal isolation).
SHTC3_SLOT = [(17.6, 124.5), (23.9, 124.5), (23.9, 125.5), (18.6, 125.5),
              (18.6, 137.5), (17.6, 137.5)]

TEST_PADS = {"TP_BOOT": ("BOOT", 1.6, 16.0), "TP_GND": ("GND", 3.8, 16.0)}


def _mm(v):
    return pcbnew.FromMM(v)


def _pt(x, y):
    return pcbnew.VECTOR2I(_mm(ORIGIN[0] + x), _mm(ORIGIN[1] + y))


def _load_footprint(fp_id):
    lib, name = fp_id.split(":")
    path = LOCAL_LIB if lib == "soil_sensor" else os.path.join(STOCK, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"cannot load footprint {fp_id}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def _polyline(board, layer, points, closed=True, width=0.1):
    pts = list(points) + ([points[0]] if closed else [])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(layer)
        seg.SetStart(_pt(x0, y0))
        seg.SetEnd(_pt(x1, y1))
        seg.SetWidth(_mm(width))
        board.Add(seg)


def _outline_points():
    return [(0, 0), (WIDTH, 0), (WIDTH, TIP_START), (WIDTH / 2, LENGTH), (0, TIP_START)]


def _zone(board, net, layer, points, priority=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(_mm(0.3))
    z.SetMinThickness(_mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = z.Outline()
    outline.NewOutline()
    for x, y in points:
        outline.Append(_pt(x, y))
    board.Add(z)
    return z


def _text(board, text, x, y, size=1.0, layer=pcbnew.F_SilkS, angle=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(_pt(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(_mm(size), _mm(size)))
    t.SetTextThickness(_mm(size * 0.15))
    t.SetTextAngleDegrees(angle)
    board.Add(t)


def _board_only(fp):
    fp.SetAttributes(pcbnew.FP_SMD | pcbnew.FP_EXCLUDE_FROM_BOM
                     | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
    return fp


def _electrode(board, net):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("soil_sensor", "PROBE_ELECTRODE"))
    fp.SetReference("E_PROBE")
    fp.SetValue("electrode")
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    x0, y0, x1, y1 = ELECTRODE
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetSize(pcbnew.VECTOR2I(_mm(x1 - x0), _mm(y1 - y0)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)                    # copper only: solder mask covers it
    pad.SetLayerSet(ls)
    fp.Add(pad)
    fp.SetPosition(_pt((x0 + x1) / 2, (y0 + y1) / 2))
    pad.SetPosition(fp.GetPosition())
    pad.SetNet(net)
    board.Add(_board_only(fp))


def _test_pad(board, ref, net, x, y):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("soil_sensor", "TESTPAD_1.2"))
    fp.SetReference(ref)
    fp.SetValue(ref)
    fp.Reference().SetVisible(False)
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(pcbnew.VECTOR2I(_mm(1.2), _mm(1.2)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.F_Mask)
    pad.SetLayerSet(ls)
    fp.Add(pad)
    fp.SetPosition(_pt(x, y))
    pad.SetPosition(fp.GetPosition())
    pad.SetNet(net)
    board.Add(_board_only(fp))


def _design_rules(board):
    bds = board.GetDesignSettings()
    bds.m_TrackMinWidth = _mm(0.15)
    bds.m_ViasMinSize = _mm(0.6)
    bds.m_MinThroughDrill = _mm(0.3)
    bds.m_CopperEdgeClearance = _mm(0.3)
    bds.m_MinClearance = _mm(0.15)
    nc = bds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(_mm(0.2))
    nc.SetTrackWidth(_mm(0.3))
    nc.SetViaDiameter(_mm(0.6))
    nc.SetViaDrill(_mm(0.3))


def build(path):
    board = pcbnew.NewBoard(path)
    _design_rules(board)

    nets = {}
    for name in sorted(NETS):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
    pad_net = {member: name for name, members in NETS.items() for member in members}

    for ref, part in PARTS.items():
        fp = _load_footprint(part.footprint)
        fp.SetReference(ref)
        fp.SetValue(part.value)
        x, y, rot = PLACEMENT[ref]
        fp.SetPosition(_pt(x, y))
        fp.SetOrientationDegrees(rot)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            name = pad_net.get((ref, pad.GetNumber()))
            if name:
                pad.SetNet(nets[name])

    _electrode(board, nets["PROBE_EL"])
    for ref, (net, x, y) in TEST_PADS.items():
        _test_pad(board, ref, nets[net], x, y)

    _polyline(board, pcbnew.Edge_Cuts, _outline_points(), width=0.1)
    _polyline(board, pcbnew.Edge_Cuts, SHTC3_SLOT, width=0.1)

    head = [(0, 0), (WIDTH, 0), (WIDTH, FILL_LINE_Y_MM), (0, FILL_LINE_Y_MM)]
    _zone(board, nets["GND"], pcbnew.F_Cu, head)
    _zone(board, nets["GND"], pcbnew.B_Cu, _outline_points())

    _polyline(board, pcbnew.F_SilkS, [(0.8, FILL_LINE_Y_MM), (WIDTH - 0.8, FILL_LINE_Y_MM)],
              closed=False, width=0.3)
    _text(board, "SOIL LINE", WIDTH / 2, FILL_LINE_Y_MM - 1.4, 1.0)
    _text(board, "+", 19.5, 35.7, 2.0)
    _text(board, "-", 19.5, 118.3, 2.0)
    _text(board, "18650", 12.5, 60.0, 2.5, angle=90)
    _text(board, "SOIL SENSOR v1", 12.5, 100.0, 1.5, angle=90)
    _text(board, "JLCJLCJLCJLC", 5.5, 137.0, 0.8)
    _text(board, "BOOT", 1.6, 17.2, 0.6)

    pcbnew.SaveBoard(path, board)
    fill_zones(path)


def fill_zones(path):
    """Fill zones with kicad-cli: the Python filler ignores edge and hole clearances."""
    subprocess.run([KCLI, "pcb", "drc", "--refill-zones", "--save-board",
                    "-o", os.devnull, path], check=True, capture_output=True)


if __name__ == "__main__":
    build(os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                          else os.path.join(HERE, "soil_sensor.kicad_pcb")))
