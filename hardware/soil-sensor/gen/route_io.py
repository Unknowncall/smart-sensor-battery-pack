"""Specctra round-trip for Freerouting: `export BOARD DSN` / `import BOARD SES`."""
import sys

import pcbnew


def export(board_path, dsn_path):
    board = pcbnew.LoadBoard(board_path)
    if not pcbnew.ExportSpecctraDSN(board, dsn_path):
        raise SystemExit("DSN export failed")


def import_ses(board_path, ses_path):
    board = pcbnew.LoadBoard(board_path)
    if not pcbnew.ImportSpecctraSES(board, ses_path):
        raise SystemExit("SES import failed")
    pcbnew.SaveBoard(board_path, board)


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def stitch(board_path, max_y_mm, keepout_y_mm, pitch_mm="4.0"):
    """Drop GND vias on a grid wherever they fit inside the front GND pour.

    Freerouting treats GND as a plane, so front-side pour islands would
    otherwise never reach the back-side GND plane.
    """
    board = pcbnew.LoadBoard(board_path)
    mm = pcbnew.FromMM
    gnd = board.FindNet("GND")
    edge = board.GetBoardEdgesBoundingBox()
    via_r, clear = mm(0.3), mm(0.25)
    front = [z for z in board.Zones() if not z.GetIsRuleArea()
             and z.GetNetname() == "GND" and z.IsOnLayer(pcbnew.F_Cu)]
    polys = [z.GetFilledPolysList(pcbnew.F_Cu) for z in front]
    obstacles = []  # (kind, data)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            obstacles.append(("box", pad.GetBoundingBox()))
    all_zones = list(board.Zones()) + [z for fp in board.GetFootprints() for z in fp.Zones()]
    rule_areas = [z for z in all_zones if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    edge_segs = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    tracks = list(board.GetTracks())
    step = mm(float(pitch_mm))
    x0, x1 = edge.GetLeft() + mm(1.0), edge.GetRight() - mm(1.0)
    y0 = edge.GetTop() + mm(float(keepout_y_mm)) + mm(1.0)
    y1 = edge.GetTop() + mm(float(max_y_mm)) - mm(1.0)
    def fits(p, inside):
        if not inside.Contains(p, -1, via_r + clear):
            return False
        if any(z.Outline().Contains(p, -1, via_r + clear) for z in rule_areas):
            return False
        for d in edge_segs:
            a, e = d.GetStart(), d.GetEnd()
            if _seg_dist(p.x, p.y, a.x, a.y, e.x, e.y) < via_r + mm(0.5):
                return False
        for _, box in obstacles:
            b = pcbnew.BOX2I(box.GetOrigin(), box.GetSize())
            b.Inflate(via_r + clear)
            if b.Contains(p):
                return False
        for t in tracks:
            w = t.GetWidth() / 2 if t.GetClass() != "PCB_VIA" else mm(0.3)
            a, e = t.GetStart(), t.GetEnd()
            if _seg_dist(p.x, p.y, a.x, a.y, e.x, e.y) < w + via_r + clear:
                return False
        return True

    def add_via(p):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        board.Add(v)
        tracks.append(v)

    added = 0
    # 1) at least one via inside every front-side pour island
    for poly in polys:
        for i in range(poly.OutlineCount()):
            island = pcbnew.SHAPE_POLY_SET()
            island.AddOutline(poly.Outline(i))
            bb = island.BBox()
            fine = mm(0.25)
            placed = False
            yy = bb.GetTop()
            while yy < bb.GetBottom() and not placed:
                xx = bb.GetLeft()
                while xx < bb.GetRight():
                    p = pcbnew.VECTOR2I(int(xx), int(yy))
                    if y0 <= yy <= y1 and fits(p, island):
                        add_via(p)
                        added += 1
                        placed = True
                        break
                    xx += fine
                yy += fine
            if not placed:
                c = bb.Centre()
                print("no via fits island near %.1f,%.1f mm (%.1f x %.1f)" % (
                    pcbnew.ToMM(c.x - edge.GetLeft()), pcbnew.ToMM(c.y - edge.GetTop()),
                    pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
    # 2) a sparse grid to tie the planes together everywhere else
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            p = pcbnew.VECTOR2I(int(x), int(y))
            if any(fits(p, poly) for poly in polys):
                add_via(p)
                added += 1
            x += step
        y += step
    pcbnew.SaveBoard(board_path, board)
    print(f"stitching vias added: {added}")


if __name__ == "__main__":
    cmd, board_path, *rest = sys.argv[1:]
    {"export": export, "import": import_ses, "stitch": stitch}[cmd](board_path, *rest)
