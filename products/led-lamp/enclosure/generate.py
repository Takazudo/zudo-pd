#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "trimesh==4.8.3"]
# ///
"""Generate the smoke-reversing enclosure, print meshes and preview from one CAD source.

Run from any directory: uv run enclosure/generate.py
All lengths are mm. KiCad front-view (x,y) maps to CAD (x-30,30-y).
The PCB mating gap is a prototype parameter, not an as-built measurement.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/schgen"))
from sexp import atom, find_all, load

OUT = ROOT / "doc/public/assets/enclosure"
CFG = {
    "outer_tip_radius": 58.0, "outer_valley_radius": 54.0,
    "inner_tip_radius": 48.0, "inner_valley_radius": 44.0,
    "teeth": 16, "panel_thickness": 13.0, "panel_count": 6,
    "floor_thickness": 2.4, "feet_height": 6.0,
    "board_p_support": 5.0, "board_gap": 11.0, "pcb_thickness": 1.6,
    "pin_diameter": 2.4, "socket_diameter": 2.8,
    "pin_height": 1.0, "socket_depth": 1.35,
    "post_width": 4.0, "post_clearance": 0.0, "post_bottom_recess": 1.0, "joint_radius": 51.0,
    "usb_opening_width": 18.0, "usb_opening_height": 13.0,
    "wheel_access_width": 30.0, "wheel_access_depth": 38.0,
}
COLORS = {"clear": "#ead9b5", "amber": "#df880c", "teal": "#337e7d", "smoke": "#58545b"}


def field(node, name):
    return atom(find_all(node, name)[0][1])


def xyz(x, y):
    return (x - 30, 30 - y)


def read_board(name):
    path = ROOT / f"boards/{name}/{name}.kicad_pcb"
    tree = load(str(path))
    holes, fps = [], {}
    for fp in find_all(tree, "footprint"):
        ref = next(atom(p[2]) for p in find_all(fp, "property") if atom(p[1]) == "Reference")
        at = [float(atom(v)) for v in find_all(fp, "at")[0][1:]]
        fps[ref] = {"at": at, "side": field(fp, "layer")}
        if "MountingHole" in atom(fp[1]):
            drill = float(field(find_all(fp, "pad")[0], "drill"))
            assert drill == 3.2, "PCB mounting drill changed; review fasteners"
            holes.append(at[:2])
    rect = find_all(tree, "gr_rect")
    edge = [r for r in rect if field(r, "layer") == "Edge.Cuts"]
    assert len(edge) == 1, "Review changed PCB outline"
    bounds = [float(atom(v)) for key in ["start", "end"] for v in find_all(edge[0], key)[0][1:]]
    assert bounds == ([0, 0, 60, 60] if name == "board-l" else [0, 0, 27, 40])
    assert float(field(find_all(tree, "general")[0], "thickness")) == CFG["pcb_thickness"]
    stack = find_all(find_all(tree, "setup")[0], "stackup")[0]
    layers = {atom(n[1]): float(field(n, "thickness")) for n in find_all(stack, "layer") if find_all(n, "thickness")}
    assert abs(sum(layers.values()) - 1.6) < .001, "Review PCB stackup thickness"
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "holes": sorted(holes), "footprints": fps, "stackup_mm": layers}


def circle(x, y, diameter, height, z=0):
    return cq.Workplane("XY").workplane(offset=z).center(x, y).circle(diameter / 2).extrude(height)


def box(x, y, w, d, height, z=0):
    return cq.Workplane("XY").box(w, d, height, centered=(True, True, False)).translate((x, y, z))


def polar(radius, angle):
    a = math.radians(angle)
    return radius * math.cos(a), radius * math.sin(a)


def star(tip, valley, angle):
    # Trim each sharp vertex by 0.35 mm along both edges: printable, less sharp tips.
    raw = [polar(tip if i % 2 == 0 else valley, angle + i * 180 / CFG["teeth"])
           for i in range(CFG["teeth"] * 2)]
    result = []
    for i, p in enumerate(raw):
        for q in (raw[i - 1], raw[(i + 1) % len(raw)]):
            distance = math.dist(p, q)
            result.append(tuple(p[j] + (q[j] - p[j]) * .35 / distance for j in (0, 1)))
    return result


RODS = [polar(CFG["joint_radius"], a) for a in (0, 120, 240)]
PINS = [polar(CFG["joint_radius"], a) for a in (60, 180, 290)]


def joints(part, height, bottom=True, top=True):
    for x, y in RODS:
        opening = CFG["post_width"] + CFG["post_clearance"]
        part = part.cut(box(x, y, opening, opening, height + 2, -1))
    for x, y in PINS:
        if bottom:
            part = part.cut(circle(x, y, CFG["socket_diameter"], CFG["socket_depth"] + .1, -.1))
        if top:
            # A tapered tip starts without forcing the socket; 0.4 mm diametral clearance.
            pin = circle(x, y, CFG["pin_diameter"], CFG["pin_height"], height)
            pin = pin.edges(">Z").chamfer(.25)
            part = part.union(pin)
    return part


def ring(angle, height):
    outer = cq.Workplane("XY").polyline(star(CFG["outer_tip_radius"], CFG["outer_valley_radius"], angle)).close().extrude(height)
    inner = cq.Workplane("XY").polyline(star(CFG["inner_tip_radius"], CFG["inner_valley_radius"], angle)).close().extrude(height + 2).translate((0, 0, -1))
    return outer.cut(inner)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board-gap", type=float, default=CFG["board_gap"], help="Measured facing-PCB surface gap in mm")
    parser.add_argument("--post-clearance", type=float, default=0.0, help="Added square-hole width in mm; zero gives exact nominal 4 x 4 mm holes")
    parser.add_argument("--skip-pcb-models", action="store_true", help="Debug only: omit KiCad STEP clearance checks")
    args = parser.parse_args()
    assert 9 <= args.board_gap <= 13, "Review enclosure height outside the supported prototype gap range"
    CFG["board_gap"] = args.board_gap
    assert 0 <= args.post_clearance <= .4, "Use a tested clearance from 0 to 0.4 mm"
    CFG["post_clearance"] = args.post_clearance
    OUT.mkdir(parents=True, exist_ok=True)
    previous = json.loads((OUT / "manifest.json").read_text()) if (OUT / "manifest.json").exists() else None
    for folder in ("stl", "preview"):
        (OUT / folder).mkdir(exist_ok=True)
    boards = {name: read_board(name) for name in ("board-l", "board-p")}
    lamp, power = boards["board-l"], boards["board-p"]
    assert lamp["footprints"]["SW2"] == {"at": [9.1, 27.75, 90.0], "side": "B.Cu"}
    assert lamp["footprints"]["RV1"] == {"at": [51.9, 9.5], "side": "B.Cu"}
    assert power["footprints"]["J1"] == {"at": [13.506, 5.0, 180.0], "side": "F.Cu"}
    shared = [(20.5, 4), (39.5, 4)]
    assert all(list(p) in lamp["holes"] and [p[0] - 16.5, p[1]] in power["holes"] for p in shared)
    # Use the existing six-pin placement checker without touching PCB layout.
    import importlib.util
    spec = importlib.util.spec_from_file_location("controls", ROOT / "scripts/pcb/verify-controls.py")
    controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controls)
    controls.check_stack(ROOT / "boards/board-l/board-l.kicad_pcb", ROOT / "boards/board-p/board-p.kicad_pcb")

    floor_z = CFG["feet_height"]
    floor_top = floor_z + CFG["floor_thickness"]
    p_bottom = floor_top + CFG["board_p_support"]
    p_top = p_bottom + CFG["pcb_thickness"]
    l_bottom = p_top + CFG["board_gap"]
    l_top = l_bottom + CFG["pcb_thickness"]
    usb_x, _ = xyz(power["footprints"]["J1"]["at"][0] + 16.5, 0)
    usb_z = floor_top  # full-height notch in the first band; the next band closes its roof
    usb_cut = box(usb_x, 49, CFG["usb_opening_width"], 42, CFG["usb_opening_height"], usb_z)
    entries, shapes, checks = [], {}, []
    source_hashes = {"enclosure/generate.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

    def emit(name, shape, color, position=(0, 0, 0), group="print", level=0, quantity=1, note="", rotation_y=0):
        solid = shape.val() if isinstance(shape, cq.Workplane) else shape
        assert solid.isValid(), f"Invalid CAD shape: {name}"
        if group == "print":
            assert len(solid.Solids()) == 1, f"Disconnected printable body: {name}"
        folder = "stl" if group == "print" or group == "coupon" else "preview"
        path = OUT / folder / f"{name}.stl"
        cq.exporters.export(solid, str(path), tolerance=.035, angularTolerance=.12)
        mesh = trimesh.load_mesh(path, process=True)
        if group != "electronics":
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, f"Invalid mesh: {name}"
        if group in ("print", "coupon"):
            assert abs(mesh.bounds[0, 2]) < .001, f"Print part not on Z=0: {name}"
        entry = {"name": name, "file": f"{folder}/{name}.stl", "color": color,
                 "position": list(position), "group": group, "level": level,
                 "rotation_y_degrees": rotation_y,
                 "quantity": quantity, "note": note,
                 "bounds_mm": mesh.bounds.tolist(), "volume_mm3": round(mesh.volume, 3),
                 "triangles": len(mesh.faces), "watertight": bool(mesh.is_watertight),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        entries.append(entry)
        if group != "coupon":
            shapes[name] = solid.rotate((0, 0, 0), (0, 1, 0), rotation_y).translate(position)
        print(f"Exported {name}", flush=True)
        return entry

    # Base plate: mounting holes come from the actual PCBs, never the concept image.
    base = cq.Workplane("XY").polyline(star(58, 54, 0)).close().extrude(CFG["floor_thickness"])
    p_holes = [tuple((x + 16.5, y)) for x, y in power["holes"]]
    l_only = [tuple(p) for p in lamp["holes"] if tuple(p) not in shared]
    mounting = sorted(set(p_holes + l_only))
    for x, y in mounting:
        base = base.cut(circle(*xyz(x, y), 3.4, 5, -1))
    # Offset the finger window toward the free right side of the wheel, keeping
    # the shared PCB pillar at CAD (9.5,26) and its supporting web intact.
    wheel_window = box(29, 13, CFG["wheel_access_width"], CFG["wheel_access_depth"], 5, -1).edges("|Z").fillet(6)
    base = base.cut(wheel_window)
    base = base.cut(box(*xyz(9.1, 27.75), 20, 24, 5, -1))
    for x in (-16, -8, 0, 8, 16):
        base = base.cut(box(x, -39, 3, 12, 5, -1))
    base = joints(base, CFG["floor_thickness"], bottom=False)
    emit("00-base", base, COLORS["clear"], (0, 0, floor_z), level=0)

    # Six single-piece, equal-height color bands. Middle bands are interchangeable.
    for index, color in enumerate(("clear", "clear", "amber", "teal", "clear", "smoke")):
        height = CFG["panel_thickness"]
        z = floor_top + index * height
        panel = joints(ring(0, height), height, top=index < CFG["panel_count"] - 1)
        if index == 0:
            panel = panel.cut(usb_cut.translate((0, 0, -z)))
        suffix = "-usb" if index == 0 else "-top" if index == CFG["panel_count"] - 1 else ""
        label = f"{index + 1:02d}-band{suffix}"
        entry = emit(label, panel, COLORS[color], (0, 0, z), level=index + 1,
                     note=f"Band {index + 1}; 13 mm; suggested {color} filament; print in any color")
        entry["profile_angle_degrees"] = 0
        entry["body_height_mm"] = height
    assert all(e["profile_angle_degrees"] == 0 for e in entries if "profile_angle_degrees" in e)

    # Separate solid spacers print upright with holes vertical; board clamping is independent of shell rods.
    for i, (x, y) in enumerate(mounting):
        height = CFG["board_p_support"] if (x, y) in p_holes else l_bottom - floor_top
        spacer = circle(0, 0, 6, height).cut(circle(0, 0, 3.4, height + 2, -1))
        emit(f"mount-{i + 1:02d}-{height:.1f}mm", spacer, "#999999", (*xyz(x, y), floor_top), level=1,
             note=f"PCB mounting spacer at KiCad Board L ({x:g}, {y:g}); M3 nylon hardware recommended")
    for i, (x, y) in enumerate(shared):
        spacer = circle(0, 0, 6, CFG["board_gap"]).cut(circle(0, 0, 3.4, CFG["board_gap"] + 2, -1))
        emit(f"interboard-{i + 1:02d}-{CFG['board_gap']:.1f}mm", spacer, "#aaaaaa", (*xyz(x, y), p_top), level=3)
    # Round printed feet with centered square through-holes, suitable for TPU trials.
    opening = CFG["post_width"] + CFG["post_clearance"]
    foot = circle(0, 0, 12, CFG["feet_height"]).cut(box(0, 0, opening, opening, 8, -1))
    post_length = floor_top + CFG["panel_count"] * CFG["panel_thickness"] - CFG["post_bottom_recess"]
    width = CFG["post_width"]
    for i, (x, y) in enumerate(RODS):
        emit(f"foot-{i + 1:02d}", foot, COLORS["smoke"], (x, y, 0), level=-1,
             note=f"Printed round foot, diameter 12 x 6 mm; centered {opening:g} mm square hole; TPU trial")
        # Long axis lies on the bed; only the assembly uses a standing orientation.
        post = box(post_length / 2, 0, post_length, width, width)
        emit(f"post-{i + 1:02d}-flat", post, "#77747b", (x + width / 2, y, CFG["post_bottom_recess"]), level=-1,
             note=f"Printed {width:g} x {width:g} x {post_length:g} mm cuboid; keep long side flat on bed; friction fit only",
             rotation_y=-90)

    emit("test-square-post-flat", box(10, 0, 20, width, width), "#999999", group="coupon")
    for allowance in (0.0, .2, .4):
        size = width + allowance
        socket = box(0, 0, 12, 12, 13).cut(box(0, 0, size, size, 15, -1))
        emit(f"test-square-hole-{size:.1f}", socket, "#999999", group="coupon")

    # Small fitting coupons: one male, three sockets with known diametral clearances.
    male = box(0, 0, 16, 16, 3).union(circle(0, 0, 2.4, 1, 3).edges(">Z").chamfer(.25))
    emit("test-pin-2.4", male, "#aaaaaa", group="coupon")
    for clearance in (.2, .4, .6):
        socket = box(0, 0, 16, 16, 3).cut(circle(0, 0, 2.4 + clearance, 1.45, -.1))
        emit(f"test-socket-clearance-{clearance:.1f}", socket, "#aaaaaa", group="coupon")

    # True KiCad STEP transforms preserve rear mounting and model offsets.
    if not args.skip_pcb_models:
        cli = shutil.which("kicad-cli")
        if cli is None:
            raise RuntimeError("Install KiCad or put kicad-cli on PATH to generate and check PCB previews")
        with tempfile.TemporaryDirectory(prefix="zld-enclosure-pcb-") as temp:
            for board, bottom, xoffset in [("board-l", l_bottom, -30), ("board-p", p_bottom, -13.5)]:
                original = ROOT / f"boards/{board}/{board}.kicad_pcb"
                # Resolve the exact sibling STEP paths in an export-only copy.
                # This avoids dependence on GUI model-resolver settings and does
                # not change any footprint placement, model transform or source PCB.
                def step_path(match):
                    path = Path(match[1].replace("${KIPRJMOD}", str(original.parent))).resolve()
                    if path.suffix.lower() == ".wrl":
                        path = path.with_suffix(".step")
                    assert path.exists(), f"Missing STEP sibling: {path}"
                    source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
                    return '(model "' + str(path) + '"'
                export_board = Path(temp) / f"{board}.kicad_pcb"
                export_board.write_text(re.sub(r'\(model "([^"]+)"', step_path, original.read_text()))
                for kind, flag, color in [("substrate", "--board-only", "#326949"), ("components", "--component-filter", "#b4b4b6")]:
                    target = Path(temp) / f"{board}-{kind}.step"
                    flags = [flag] if kind == "substrate" else [flag, "*"]
                    cmd = [cli, "pcb", "export", "step", "--subst-models", "--no-dnp", *flags,
                           "--user-origin", "0x0mm", "-o", str(target), str(export_board)]
                    result = subprocess.run(cmd, text=True, capture_output=True)
                    assert result.returncode == 0, result.stdout + result.stderr
                    assert target.exists(), result.stdout + result.stderr
                    shape = cq.importers.importStep(str(target)).val()
                    # Derive the exporter Z datum from the substrate; apply exactly
                    # the same translation to its components (KiCad versions differ).
                    if kind == "substrate":
                        b = shape.BoundingBox()
                        stack = boards[board]["stackup_mm"]
                        finish_bottom = stack["B.Cu"] + stack["B.Mask"]
                        finish_top = stack["F.Cu"] + stack["F.Mask"]
                        core = CFG["pcb_thickness"] - finish_bottom - finish_top
                        assert abs(b.zlen - core) < .002, f"KiCad STEP core thickness: {b.zlen}"
                        assert abs(b.xmin) < .02 and abs(b.ymax) < .02, "KiCad STEP XY origin changed"
                        zshift = bottom + finish_bottom - b.zmin
                        substrate_bounds = b
                    else:
                        # KiCad 10.0.0's no-board-body path can return an empty
                        # assembly. Export the full assembly, then remove exactly
                        # the one core solid whose bounds match the board-only export.
                        solids = shape.Solids()
                        def is_substrate(solid):
                            bb = solid.BoundingBox()
                            return all(abs(getattr(bb, key) - getattr(substrate_bounds, key)) < .002
                                       for key in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"))
                        assert sum(is_substrate(s) for s in solids) == 1, "PCB core not uniquely identified"
                        components = [s for s in solids if not is_substrate(s)]
                        assert len(components) > 10, "Component export unexpectedly incomplete"
                        shape = cq.Compound.makeCompound(components)
                    emit(f"{board}-{kind}-reference", shape, color, (xoffset, 30, zshift), "electronics", level=2 if board == "board-p" else 4)

    # Validate contacts/clearances in solid CAD, including every populated STEP body.
    print("Checking assembled contacts and interference…", flush=True)
    printed = {n: s for n, s in shapes.items() if next(e for e in entries if e["name"] == n)["group"] == "print"}
    bounds_cache = {}
    def bounds(shape):
        key = id(shape)
        if key not in bounds_cache:
            bounds_cache[key] = shape.BoundingBox()
        return bounds_cache[key]
    def overlaps(a, b):
        aa, bb = bounds(a), bounds(b)
        return all(getattr(aa, f"{axis}min") < getattr(bb, f"{axis}max") - .001 and
                   getattr(bb, f"{axis}min") < getattr(aa, f"{axis}max") - .001 for axis in "xyz")
    pairs = []
    reference_solids = {name: shape.Solids() for name, shape in shapes.items() if "-reference" in name}
    for i, (name, shape) in enumerate(printed.items()):
        print(f"Checking {name}", flush=True)
        for other, second in list(printed.items())[i + 1:]:
            if overlaps(shape, second):
                volume = shape.intersect(second).Volume()
                assert volume < .01, f"Printed parts collide: {name} / {other}: {volume} mm3"
                pairs.append([name, other, round(volume, 6)])
        for other, second in shapes.items():
            if "-reference" in other and overlaps(shape, second):
                # All panel material is outside radius 43.5 mm (inner valley
                # radius 44, including the trimmed vertices). A contained AABB
                # proves an electronics group cannot meet that annulus.
                bb = bounds(second)
                radial_bound = max(math.hypot(x, y) for x in (bb.xmin, bb.xmax) for y in (bb.ymin, bb.ymax))
                if name[:2].isdigit() and name != "00-base" and radial_bound < 43.5:
                    volume = 0.0
                else:
                    # Do not boolean a small spacer against every solid on the PCB.
                    volume = sum(shape.intersect(s).Volume() for s in reference_solids[other] if overlaps(shape, s))
                assert volume < .02, f"Enclosure hits {other}: {name}: {volume} mm3"
                pairs.append([name, other, round(volume, 6)])
    # Wide plastic overmold stops at the PCB edge (Y=30), while the narrower
    # metal nose enters the receptacle. Sweeping the full overmold through the
    # PCB would incorrectly reject the two existing front mounting pillars.
    cable_body = box(usb_x, 46, 16, 32, 8, p_top - 2.4).val()
    cable_nose = box(usb_x, 26, 8.4, 8, 2.6, p_top + .3).val()
    for plug in (cable_body, cable_nose):
        for name, shape in printed.items():
            if overlaps(shape, plug):
                volume = shape.intersect(plug).Volume()
                assert volume < .01, f"USB cable corridor blocked by {name}"
    checks.extend(["Every printable STL is watertight, consistently wound, and positive-volume",
                   "Every print mesh starts on Z=0", "Each assembly print file contains one connected solid",
                   "All printed-part pairs and modeled PCB/hardware intersections checked",
                   "16 x 8 mm overmold corridor to PCB edge and 8.4 x 2.6 mm metal-nose corridor are open; actual seating unverified", "Existing PCB mounting and six-pin alignment checked"])

    manifest = {"revision": "prototype-03-square-posts", "units": "mm", "config": CFG, "source_hashes": source_hashes,
                "retention": "Unthreaded printed posts: fit-based retention only; no positive axial lock. Support the base when lifting.",
                "status": "FIT PROTOTYPE — physical fit and powered thermal testing pending",
                "pcb_models_checked": not args.skip_pcb_models,
                "board_sources": boards,
                "datums": {"floor_top": floor_top, "board_p_bottom": p_bottom, "board_p_top": p_top,
                           "board_l_bottom": l_bottom, "board_l_top": l_top,
                           "top": floor_top + CFG["panel_count"] * CFG["panel_thickness"], "usb_opening_bottom": usb_z},
                "checks": checks, "intersection_checks": pairs, "parts": entries}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assembly = cq.Assembly(name="square_posts_prototype_03")
    for entry in entries:
        if entry["group"] == "coupon":
            continue
        color = entry["color"].lstrip("#")
        rgb = tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
        assembly.add(shapes[entry["name"]], name=entry["name"], color=cq.Color(*rgb))
    with tempfile.TemporaryDirectory(prefix="zld-enclosure-step-") as temp:
        step_file = Path(temp) / "assembly.step"
        assembly.export(str(step_file))
        with zipfile.ZipFile(OUT / "assembly-step.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.write(step_file, "assembly.step")
    # An STL assembly is deliberately omitted: it would invite printing an unserviceable fused stack.
    with zipfile.ZipFile(OUT / "smoke-reversing-stls.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for entry in entries:
            if entry["group"] in ("print", "coupon"):
                archive.write(OUT / entry["file"], entry["file"])
        archive.write(OUT / "manifest.json", "manifest.json")
        archive.write(ROOT / "enclosure/README.md", "README.md")
    # Retire only previously generated files recorded in the old manifest.
    if previous:
        current_files = {e["file"] for e in entries}
        for old in previous["parts"]:
            path = OUT / old["file"]
            if old["file"] not in current_files and path.parent in (OUT / "stl", OUT / "preview") and path.exists():
                path.unlink()
    print(json.dumps({"output": str(OUT), "print_files": sum(e["group"] == "print" for e in entries),
                      "checks": checks, "height_mm": manifest["datums"]["top"]}, indent=2))


if __name__ == "__main__":
    main()
