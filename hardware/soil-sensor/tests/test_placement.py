"""The generated board has the right shape, parts, nets, keep-outs and probe."""
import json
import os
import subprocess

import pcbnew
import pytest

import build_board
import netlist
import parts

KCLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_W, BOARD_L = 25.0, 222.0
MM = 1e6


def _routed_board_path():
    return os.environ.get("SOIL_BOARD")


@pytest.fixture(scope="module")
def board_path(tmp_path_factory):
    routed = _routed_board_path()
    if routed:
        return routed
    path = str(tmp_path_factory.mktemp("board") / "soil_sensor.kicad_pcb")
    build_board.build(path)
    return path


@pytest.fixture(scope="module")
def board(board_path):
    return pcbnew.LoadBoard(board_path)


def mm(v):
    return v / MM


def origin(board):
    bb = board.GetBoardEdgesBoundingBox()
    return bb.GetLeft(), bb.GetTop()


def rel(board, pos):
    ox, oy = origin(board)
    return mm(pos.x - ox), mm(pos.y - oy)


def test_outline_size(board):
    bb = board.GetBoardEdgesBoundingBox()
    assert abs(mm(bb.GetWidth()) - BOARD_W) < 0.5
    assert abs(mm(bb.GetHeight()) - BOARD_L) < 0.5


def test_every_bom_part_is_placed_on_top(board):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for ref, part in parts.PARTS.items():
        assert ref in fps, f"{ref} missing"
        assert fps[ref].GetLayer() == pcbnew.F_Cu, f"{ref} not on top"
        assert fps[ref].GetFPID().GetUniStringLibItemName() == part.footprint.split(":")[1]


def test_pads_carry_the_netlist_nets(board):
    pads = {(f.GetReference(), p.GetNumber()): p.GetNetname()
            for f in board.GetFootprints() for p in f.Pads()}
    for net, members in netlist.NETS.items():
        for member in members:
            assert pads[member] == net, f"{member} on {pads[member]!r}, want {net}"


def test_usb_faces_left_edge_and_antenna_at_top(board):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    usb_left = rel(board, fps["J_USB"].GetBoundingBox(False).GetOrigin())[0]
    assert usb_left <= 0.6
    mcu_top = rel(board, fps["U_MCU"].GetBoundingBox(False).GetOrigin())[1]
    assert mcu_top <= 0.6


def _filled_layer_polys(board, layer):
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(layer):
            continue
        out.append((z.GetNetname(), z.GetFilledPolysList(layer)))
    return out


def _keepout_box(board):
    ox, oy = origin(board)
    x0, y0, x1, y1 = build_board.KEEPOUT_RECT_MM
    return pcbnew.BOX2I(pcbnew.VECTOR2I(int(ox + x0 * MM), int(oy + y0 * MM)),
                        pcbnew.VECTOR2I(int((x1 - x0) * MM), int((y1 - y0) * MM)))


def test_no_copper_in_antenna_keepout(board):
    box = _keepout_box(board)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        for net, polys in _filled_layer_polys(board, layer):
            assert not polys.BBox().Intersects(box) or not _poly_hits_box(polys, box), \
                f"{net} pour enters the antenna keep-out on {pcbnew.LayerName(layer)}"
    for t in board.GetTracks():
        assert not t.GetBoundingBox().Intersects(box), "track/via in antenna keep-out"


def _poly_hits_box(polys, box):
    probe = pcbnew.SHAPE_POLY_SET()
    probe.NewOutline()
    for x, y in ((box.GetLeft(), box.GetTop()), (box.GetRight(), box.GetTop()),
                 (box.GetRight(), box.GetBottom()), (box.GetLeft(), box.GetBottom())):
        probe.Append(x, y)
    inter = pcbnew.SHAPE_POLY_SET(polys)
    inter.BooleanIntersection(probe)
    return inter.OutlineCount() > 0 and inter.Area() > 0.01 * MM * MM


def test_nothing_but_the_electrode_below_fill_line(board):
    ox, oy = origin(board)
    fill_y = oy + build_board.FILL_LINE_Y_MM * MM
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            assert t.GetPosition().y < fill_y, "via below the fill line"
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetPosition().y > fill_y:
                assert f.GetReference() == "E_PROBE", f"{f.GetReference()} pad below fill line"


def test_electrode_and_back_ground_plane(board):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    el = fps["E_PROBE"]
    assert all(p.GetNetname() == "PROBE_EL" for p in el.Pads())
    assert all(not p.IsOnLayer(pcbnew.F_Mask) for p in el.Pads()), "electrode must stay under solder mask"
    ox, oy = origin(board)
    fill_y = oy + build_board.FILL_LINE_Y_MM * MM
    back_gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"
                and z.IsOnLayer(pcbnew.B_Cu) and z.GetBoundingBox().GetBottom() > fill_y + 40 * MM]
    assert back_gnd, "no back-side GND under the probe"
    front_below = [z for z in board.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)
                   and z.GetBoundingBox().GetBottom() > fill_y + 1 * MM]
    assert not front_below, "front copper pour below the fill line"


def test_shtc3_sits_beside_a_slot(board):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    rh = fps["U_RH"].GetPosition()
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    outline_bb = board.GetBoardEdgesBoundingBox()
    slots = [d for d in edges if d.GetBoundingBox().GetWidth() < outline_bb.GetWidth() * 0.9
             and d.GetBoundingBox().GetHeight() < outline_bb.GetHeight() * 0.5]
    near = [d for d in slots if d.GetBoundingBox().Distance(rh) < 3 * MM]
    assert near, "no slot next to the SHTC3"


def test_board_only_footprints_stay_out_of_bom(board):
    for f in board.GetFootprints():
        if f.GetReference() not in parts.PARTS:
            assert f.IsExcludedFromBOM() and f.IsExcludedFromPosFiles(), f.GetReference()


def test_drc_has_no_errors_besides_unrouted(board_path, tmp_path):
    report = tmp_path / "drc.json"
    subprocess.run([KCLI, "pcb", "drc", "--format", "json", "--severity-error",
                    "-o", str(report), board_path], check=False, capture_output=True)
    data = json.loads(report.read_text())
    allowed = {"unconnected_items"} if not _routed_board_path() else set()
    errors = [v for v in data.get("violations", []) if v["type"] not in allowed]
    assert not errors, json.dumps([(v["type"], v["description"]) for v in errors][:10], indent=1)
    if _routed_board_path():
        assert not data.get("unconnected_items"), "routed board still has unconnected items"
