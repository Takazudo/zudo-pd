#!/usr/bin/env python3
"""Placement feasibility study for the r-next candidate on the 27 x 40 mm Board P outline.

No routing. Courtyard rectangles (axis-aligned bounding boxes of each footprint's F.CrtYd
graphics, as resolved through ../fp-lib-table) are packed into the outline around fixed
items taken from the ordered boards/board-p/board-p.kicad_pcb:
  - Edge.Cuts 27 x 40 mm rectangle,
  - three M3 mounting holes (courtyard from the board file, blocks both sides),
  - JOUT1 at (12.9, 37.7) (R3.1 mating stack; through-hole, blocks both sides),
  - J1 USB-C at (13.506, 5.0) rot 180 (enclosure opening; assumption, blocks both sides).
RESET keep-out (requirement R1.1): U1's courtyard is widened by RESET_STRAP_MM on one side
to reserve a pin-6-to-GND strap zone that no other courtyard may cover (proposed size).
Margins below have no manufacturer or measured source; they are *proposed* study inputs.

Usage: python3 tools/placement_study.py [--height H] > checks/placement-study.json
--height grows the outline in +Y only (away from the USB edge); fixed items keep their
coordinates. It is a what-if for a mechanical delta, not an adopted outline.
"""
import argparse
import json
import math
import re
import runpy
import sys
from pathlib import Path

CAND = Path(__file__).resolve().parents[1]
ROOT = CAND.parents[1]
BOARD = ROOT / "boards/board-p/board-p.kicad_pcb"
W, H = 27.0, 40.0
GRID = 0.1
EDGE_KEEPIN_MM = 0.3          # proposed
RESET_STRAP_MM = 1.0          # proposed
FIXED = {"J1": ((13.506, 5.0), 180), "JOUT1": ((12.9, 37.7), 0)}


def sexp(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok.strip('"'))
    return stack[0][0]


def child(node, key):
    return next((c for c in node[1:] if isinstance(c, list) and c and c[0] == key), None)


def courtyard_bbox(fp, layer="F.CrtYd"):
    xs, ys = [], []
    for item in fp[1:]:
        if not (isinstance(item, list) and item and item[0].startswith("fp_")):
            continue
        lay = child(item, "layer")
        if not lay or lay[1] != layer:
            continue
        if item[0] == "fp_circle":
            cx, cy = map(float, child(item, "center")[1:3])
            ex, ey = map(float, child(item, "end")[1:3])
            r = math.hypot(ex - cx, ey - cy)
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
            continue
        for key in ("start", "mid", "end"):
            c = child(item, key)
            if c:
                xs.append(float(c[1]))
                ys.append(float(c[2]))
        pts = child(item, "pts")
        for p in (pts[1:] if pts else []):
            xs.append(float(p[1]))
            ys.append(float(p[2]))
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def pad_bbox(fp):
    xs, ys = [], []
    for item in fp[1:]:
        if isinstance(item, list) and item and item[0] == "pad":
            at, size = child(item, "at"), child(item, "size")
            x, y = float(at[1]), float(at[2])
            rot = float(at[3]) if len(at) > 3 else 0
            w, h = float(size[1]), float(size[2])
            if round(rot) % 180 == 90:
                w, h = h, w
            xs += [x - w / 2, x + w / 2]
            ys += [y - h / 2, y + h / 2]
    return min(xs) - 0.25, min(ys) - 0.25, max(xs) + 0.25, max(ys) + 0.25


def lib_table():
    table = {}
    for name, uri in re.findall(r'\(lib \(name "?([^")\s]+)"?\).*?\(uri "([^"]+)"\)', (CAND / "fp-lib-table").read_text()):
        table[name] = Path(uri.replace("${KIPRJMOD}", str(CAND))).resolve()
    return table


def rotate_box(box, rot):
    x0, y0, x1, y1 = box
    r = round(rot) % 360
    if r == 0:
        return box
    if r == 180:
        return -x1, -y1, -x0, -y0
    if r == 90:   # KiCad: x' = x cos + y sin, y' = -x sin + y cos
        return y0, -x1, y1, -x0
    return -y1, x0, -y0, x1


class Grid:
    def __init__(self):
        self.nx, self.ny = round(W / GRID), round(H / GRID)
        self.occ = {"F": bytearray(self.nx * self.ny), "B": bytearray(self.nx * self.ny)}
        e = round(EDGE_KEEPIN_MM / GRID)
        for side in self.occ:
            for j in range(self.ny):
                for i in range(self.nx):
                    if i < e or j < e or i >= self.nx - e or j >= self.ny - e:
                        self.occ[side][j * self.nx + i] = 1

    def cells(self, x0, y0, x1, y1):
        return (max(0, math.floor(x0 / GRID + 1e-9)), max(0, math.floor(y0 / GRID + 1e-9)),
                min(self.nx, math.ceil(x1 / GRID - 1e-9)), min(self.ny, math.ceil(y1 / GRID - 1e-9)))

    def mark(self, box, sides):
        i0, j0, i1, j1 = self.cells(*box)
        for side in sides:
            for j in range(j0, j1):
                self.occ[side][j * self.nx + i0:j * self.nx + i1] = b"\x01" * (i1 - i0)

    def free(self, side, i0, j0, wi, hj):
        if i0 + wi > self.nx or j0 + hj > self.ny:
            return False
        o, nx = self.occ[side], self.nx
        return all(not any(o[j * nx + i0:j * nx + i0 + wi]) for j in range(j0, j0 + hj))

    def used(self, side):
        return sum(self.occ[side]) * GRID * GRID


def pack(parts, sides_allowed, margin):
    g = Grid()
    fixed_area = {}
    for name, box, sides in FIXED_BOXES:
        g.mark(box, sides)
        fixed_area[name] = round((box[2] - box[0]) * (box[3] - box[1]), 2)
    blocked = {s: round(g.used(s), 1) for s in g.occ}
    placed, failed = [], []
    for ref, w, h, side_pref in sorted(parts, key=lambda p: -(p[1] * p[2])):
        sides = [s for s in sides_allowed if s in side_pref]
        spot = None
        for side in sides:
            for ww, hh in ((w, h), (h, w)):
                wi, hj = math.ceil((ww + margin) / GRID - 1e-9), math.ceil((hh + margin) / GRID - 1e-9)
                for j in range(g.ny - hj + 1):
                    for i in range(g.nx - wi + 1):
                        if g.free(side, i, j, wi, hj):
                            spot = (side, i, j, wi, hj, ww, hh)
                            break
                    if spot:
                        break
                if spot:
                    break
            if spot:
                break
        if not spot:
            failed.append(ref)
            continue
        side, i, j, wi, hj, ww, hh = spot
        g.mark((i * GRID, j * GRID, (i + wi) * GRID, (j + hj) * GRID), [side])
        placed.append({"ref": ref, "side": side, "x_mm": round(i * GRID + margin / 2, 2), "y_mm": round(j * GRID + margin / 2, 2),
                       "w_mm": round(ww, 2), "h_mm": round(hh, 2)})
    return {"placed": len(placed), "failed": failed, "blocked_before_packing_mm2": blocked,
            "occupied_after_mm2": {s: round(g.used(s), 1) for s in g.occ}, "positions": placed}


def ordered_reference(board):
    """Same metric on the ordered, routed Board P (pad bbox + 0.25 mm where it has no courtyard)."""
    total, fallback, count = 0.0, [], 0
    for fp in (c for c in board[1:] if isinstance(c, list) and c and c[0] == "footprint"):
        ref = next(p[2] for p in fp[1:] if isinstance(p, list) and p[:2] == ["property", "Reference"])
        if ref in FIXED or fp[1].startswith("MountingHole:"):
            continue
        box = courtyard_bbox(fp)
        if box is None:
            box = pad_bbox(fp)
            fallback.append(ref)
        total += (box[2] - box[0]) * (box[3] - box[1])
        count += 1
    return {"movable_parts": count, "movable_parts_courtyard_sum_mm2": round(total, 1),
            "courtyard_fallback_pad_bbox_plus_0p25": fallback,
            "note": "ordered board is routed on 2 layers; its single-side utilisation is the only in-repo calibration point"}


def main():
    global H
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=float, default=40.0)
    H = parser.parse_args().height
    spec = runpy.run_path(str(CAND / "board_p_rnext_spec.py"))
    table = lib_table()
    board = sexp(BOARD.read_text())
    global FIXED_BOXES
    FIXED_BOXES = []
    for fp in (c for c in board[1:] if isinstance(c, list) and c and c[0] == "footprint"):
        if fp[1].startswith("MountingHole:"):
            at = child(fp, "at")
            x, y = float(at[1]), float(at[2])
            b = courtyard_bbox(fp)
            FIXED_BOXES.append((f"hole@{x},{y}", (x + b[0], y + b[1], x + b[2], y + b[3]), ["F", "B"]))
    parts, rows, missing_crtyd = [], [], []
    for ref, comp in sorted(spec["COMPONENTS"].items()):
        if ref.startswith("#"):
            continue
        nick, name = comp[3].split(":", 1)
        fp = sexp((table[nick] / f"{name}.kicad_mod").read_text())
        box = courtyard_bbox(fp)
        if box is None:
            box = pad_bbox(fp)
            missing_crtyd.append(ref)
        if ref in FIXED:
            (x, y), rot = FIXED[ref]
            rb = rotate_box(box, rot)
            FIXED_BOXES.append((ref, (x + rb[0], y + rb[1], x + rb[2], y + rb[3]), ["F", "B"]))
        w, h = box[2] - box[0], box[3] - box[1]
        if ref == "U1":
            w += RESET_STRAP_MM
        th = any(isinstance(i, list) and i and i[0] == "pad" and i[2] == "thru_hole" for i in fp[1:])
        rows.append({"ref": ref, "footprint": comp[3], "dnp": comp[4], "courtyard_w_mm": round(w, 2), "courtyard_h_mm": round(h, 2),
                     "area_mm2": round(w * h, 2), "through_hole": th, "fixed": ref in FIXED})
        if ref not in FIXED:
            parts.append((ref, w, h, "F" if th or ref in ("C3",) else "FB"))
    board_area = W * H
    hole_area = sum((b[2] - b[0]) * (b[3] - b[1]) for n, b, s in FIXED_BOXES if n.startswith("hole"))
    fixed_area = sum(r["area_mm2"] for r in rows if r["fixed"])
    free_area = sum(r["area_mm2"] for r in rows if not r["fixed"])
    edge_area = board_area - (W - 2 * EDGE_KEEPIN_MM) * (H - 2 * EDGE_KEEPIN_MM)
    usable_one_side = board_area - edge_area - hole_area - fixed_area
    window = [r for r in rows if r["ref"] in {"U4", "U5", "C40", "C41", "C42"} | {f"R{n}" for n in range(30, 40)}]
    out = {
        "status": "UNADOPTED desk study; not a layout, no routing, no DRC",
        "inputs": {"outline_mm": [W, H], "grid_mm": GRID, "edge_keepin_mm_proposed": EDGE_KEEPIN_MM,
                   "reset_strap_keepout_mm_proposed": RESET_STRAP_MM,
                   "fixed": {n: [round(v, 2) for v in b] for n, b, s in FIXED_BOXES},
                   "fixed_assumption": "J1 kept at the ordered position for the enclosure opening (assumption, not stated by the coordinator)",
                   "courtyard_fallback_pad_bbox_plus_0p25": missing_crtyd},
        "areas_mm2": {
            "board": board_area, "edge_keepin": round(edge_area, 1), "holes_courtyard_bbox": round(hole_area, 1),
            "fixed_parts_courtyard": round(fixed_area, 1),
            "usable_per_side_after_fixed": round(usable_one_side, 1),
            "movable_parts_courtyard_sum": round(free_area, 1),
            "of_which_window_subcircuit": round(sum(r["area_mm2"] for r in window), 1),
            "of_which_C3_bulk_cap": next(r["area_mm2"] for r in rows if r["ref"] == "C3"),
            "single_side_courtyard_utilisation": round(free_area / usable_one_side, 3),
            "double_side_courtyard_utilisation": round(free_area / (2 * usable_one_side), 3),
        },
        "parts": rows,
        "packing": {
            "F_only_margin_0": pack(parts, ["F"], 0.0),
            "F_only_margin_0p5_proposed": pack(parts, ["F"], 0.5),
            "F_then_B_margin_0p5_proposed": pack(parts, ["F", "B"], 0.5),
            "F_only_margin_1p0_proposed": pack(parts, ["F"], 1.0),
            "F_then_B_margin_1p0_proposed": pack(parts, ["F", "B"], 1.0),
        },
    }
    for p in out["packing"].values():
        p["back_side_refs"] = [x["ref"] for x in p["positions"] if x["side"] == "B"]
    out["calibration_ordered_board_p"] = ordered_reference(board)
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
