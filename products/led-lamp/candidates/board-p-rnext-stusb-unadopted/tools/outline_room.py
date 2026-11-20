#!/usr/bin/env python3
"""Room around the 27 x 40 mm Board P outline at Board P level in the current enclosure stack.

Reads boards/board-l/board-l.kicad_pcb (Board L sits 11 mm above Board P, offset +16.5 mm in X,
per enclosure/generate.py) and the enclosure config. Obstacles in Board P coordinates:
Board L bottom-side through-hole bodies (courtyards), Board L-only mounting spacers (radius 6 mm),
the floor access windows for SW2 and the RV1 wheel, and the inner shell radius 43.5 mm.
Usage: python3 tools/outline_room.py > checks/outline-room.json
"""
import json
import math
import runpy
import sys
from pathlib import Path

CAND = Path(__file__).resolve().parents[1]
ROOT = CAND.parents[1]
ps = runpy.run_path(str(CAND / "tools/placement_study.py"))
DX = 16.5            # enclosure/generate.py: Board P x + 16.5 = Board L x
CENTER_L = (30.0, 30.0)  # enclosure/generate.py xyz(): CAD = (x - 30, 30 - y)
SHELL_R = 43.5       # enclosure/generate.py: panel material outside radius 43.5 mm
SPACER_R = 6.0       # enclosure/generate.py: circle(0, 0, 6, ...) spacers


def main():
    board = ps["sexp"]((ROOT / "boards/board-l/board-l.kicad_pcb").read_text())
    obstacles = []
    for fp in (c for c in board[1:] if isinstance(c, list) and c and c[0] == "footprint"):
        ref = next(p[2] for p in fp[1:] if isinstance(p, list) and p[:2] == ["property", "Reference"])
        layer = ps["child"](fp, "layer")[1]
        at = ps["child"](fp, "at")
        x, y, rot = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        if fp[1].startswith("MountingHole:"):
            if (x - DX, y) not in [(4.0, 4.0), (23.0, 4.0)]:
                obstacles.append({"what": f"Board L-only spacer at L({x},{y})", "box": [x - DX - SPACER_R, y - SPACER_R, x - DX + SPACER_R, y + SPACER_R]})
            continue
        if layer == "B.Cu" and ref != "J2":
            bb = ps["courtyard_bbox"](fp, "B.CrtYd") or ps["pad_bbox"](fp)
            bb = ps["rotate_box"]((-bb[2], bb[1], -bb[0], bb[3]), -rot)
            obstacles.append({"what": f"Board L {ref} bottom body", "box": [x + bb[0] - DX, y + bb[1], x + bb[2] - DX, y + bb[3]]})
    # enclosure/generate.py base cuts: SW2 box(xyz(9.1, 27.75), 20, 24); wheel window box(29, 13, 30, 38) in CAD
    obstacles.append({"what": "floor window under SW2 (access from below)", "box": [9.1 - 10 - DX, 27.75 - 12, 9.1 + 10 - DX, 27.75 + 12]})
    obstacles.append({"what": "floor finger window for the RV1 wheel", "box": [29 - 15 + 30 - DX, 30 - (13 + 19), 29 + 15 + 30 - DX, 30 - (13 - 19)]})
    out = {"obstacles_board_p_coords": [{**o, "box": [round(v, 2) for v in o["box"]]} for o in obstacles]}

    def clear(x0, y0, x1, y1):
        return [o["what"] for o in obstacles if o["box"][0] < x1 and x0 < o["box"][2] and o["box"][1] < y1 and y0 < o["box"][3]]
    grow = {}
    for name, step in (("+y", (0, 0, 0, 1)), ("+x", (0, 0, 1, 0)), ("-x", (-1, 0, 0, 0))):
        extra = 0.0
        while extra < 30:
            nxt = extra + 0.5
            box = [0 + step[0] * nxt, 0, 27 + step[2] * nxt, 40 + step[3] * nxt]
            corners = [(bx + DX - CENTER_L[0], CENTER_L[1] - by) for bx in (box[0], box[2]) for by in (box[1], box[3])]
            hits = [h for h in clear(*box) if h not in clear(0, 0, 27, 40)]
            if hits or max(math.hypot(*c) for c in corners) > SHELL_R - 1.0:
                grow[name] = {"max_extra_mm": extra, "limited_by": hits or ["shell radius - 1 mm"]}
                break
            extra = nxt
        else:
            grow[name] = {"max_extra_mm": extra, "limited_by": ["search limit 30 mm"]}
    out["existing_outline_already_overlaps"] = clear(0, 0, 27, 40)
    out["growth"] = grow
    out["note"] = "Geometry screen only. enclosure/generate.py asserts the 27 x 40 outline; any growth is a mechanical delta needing regeneration and a new fit print"
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
