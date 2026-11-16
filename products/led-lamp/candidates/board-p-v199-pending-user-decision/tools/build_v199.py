"""Rebuild the V199 scratch candidate from the committed V198 files.

Each recommended option is one named change. Any of them can be dropped with
--skip NAME, and the rest still apply, because no change depends on another.
The PCB keeps every footprint on one long line, so `git revert` of a single
commit would conflict. Rebuilding with --skip is how you drop one change.

Usage (from the repository root):
  python3 -I candidates/board-p-v199-pending-user-decision/tools/build_v199.py \
      [--skip NAME ...] [--out DIR]
"""
import argparse
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
V199 = HERE.parent
V198 = V199.parent / "board-p-v198-unadopted"
BASE = "board-p-COUT1206-TRIAL"
NS = uuid.UUID("6b9d6c0e-1f70-4d0b-9b8e-199000000000")
ROOT_SHEET = "504a03fe-2ef9-52ee-8b8d-97d09bd9c311"


def uid(tag):
    return str(uuid.uuid5(NS, tag))


def sub1(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{what}: expected 1 match, found {n}: {old[:80]!r}")
    return text.replace(old, new)


# --- change 1: RMH2 180k -> 187k (FAILOFF-WINDOW.md option O3) -------------
# Value-only change on the same land. The RT0603BRD07187KL LCSC code is not
# verified, so the LCSC fields are left empty rather than guessed.
RMH2_OLD_VAL = "180k 0.1% / RT0603BRD07180KL"
RMH2_NEW_VAL = "187k 0.1% / RT0603BRD07187KL"
RMH2_MPN = "RT0603BRD07187KL"


def rmh2_187k(f):
    sch = f["sch"]
    sch = sub1(sch, f'(property "Value" "{RMH2_OLD_VAL}" (at 279.4 353.06 0)',
               f'(property "Value" "{RMH2_NEW_VAL}" (at 279.4 353.06 0)', "RMH2 sch value")
    sch = sub1(sch, '(property "LCSC" "C326731" (at 279.4 363.22 0) (effects (font (size 1.27 1.27)) (hide yes)))',
               '(property "LCSC" "" (at 279.4 363.22 0) (effects (font (size 1.27 1.27)) (hide yes)))'
               f' (property "MPN" "{RMH2_MPN}" (at 279.4 363.22 0) (effects (font (size 1.27 1.27)) (hide yes)))',
               "RMH2 sch LCSC")
    f["sch"] = sch

    pcb = f["pcb"]
    start = pcb.index('(footprint "rmh2-candidate:')
    end = pcb.index('(footprint "', start + 10)
    blk = pcb[start:end]
    blk = sub1(blk, '(property "LCSC" "C326731"', '(property "LCSC" ""', "RMH2 pcb LCSC")
    blk = sub1(blk, '(property "LCSC Part" "C326731"', '(property "LCSC Part" ""', "RMH2 pcb LCSC Part")
    blk = sub1(blk, f'(fp_text value "{RMH2_OLD_VAL}"', f'(fp_text value "{RMH2_NEW_VAL}"', "RMH2 pcb value")
    blk = sub1(blk, '(fp_text reference "RMH2"',
               f'(property "MPN" "{RMH2_MPN}" (at 0 0) (layer "F.Fab") (hide yes) '
               f'(effects (font (size 1 1) (thickness 0.15))) (uuid "{uid("RMH2/MPN")}")) '
               '(fp_text reference "RMH2"', "RMH2 pcb MPN")
    f["pcb"] = pcb[:start] + blk + pcb[end:]

    f["bom"] = sub1(f["bom"],
                    "RMH2,180k 0.1% / RT0603BRD07180KL,,C326731,",
                    f"RMH2,{RMH2_NEW_VAL},{RMH2_MPN},,", "RMH2 bom")
    f["bom"] = f["bom"].replace(
        "rmh2-candidate:RMH2_RT0603BRD07180KL_YAGEO_REFLOW_CANDIDATE,UNADOPTED engineering source",
        "rmh2-candidate:RMH2_RT0603BRD07180KL_YAGEO_REFLOW_CANDIDATE,PENDING USER DECISION (O3); LCSC UNBOUND")


# --- change 2: COUT Datasheet field sync (the one V198 parity notice) ------
COUT_DS = "https://product.samsungsem.com/mlcc/CL31B475KBHNNN.do"


def cout_datasheet(f):
    pcb = f["pcb"]
    start = pcb.index('(footprint "cout-candidate:')
    end = pcb.index('(footprint "', start + 10)
    blk = pcb[start:end]
    if '(property "Datasheet"' in blk:
        raise SystemExit("COUT already has a Datasheet property")
    blk = sub1(blk, '(fp_text reference "COUT"',
               f'(property "Datasheet" "{COUT_DS}" (at 0 0 -90) (layer "F.Fab") (hide yes) '
               f'(effects (font (size 1 1) (thickness .15))) (uuid "{uid("COUT/Datasheet")}")) '
               '(fp_text reference "COUT"', "COUT datasheet")
    f["pcb"] = pcb[:start] + blk + pcb[end:]


# --- change 3: J1 GND hole-side land trim, 0.025 mm ------------------------
# Shorten A1/B12 and B1/A12 only at the end facing the 0.65 mm NPTH locating
# holes: length 1.15 -> 1.125, centre moved 0.0125 mm away from the hole. The
# outer end, the width and the rest of J1 stay as printed. Nominal hole-to-land
# distance goes from 0.1751 to 0.2001 mm.
J1_MOD = "libraries/trial.pretty/USB4105_V106_TRIAL_UNASSIGNED.kicad_mod"


def j1_gnd_trim(f):
    pcb = f["pcb"]
    for pad, x in (("A1/B12", "-3.2"), ("B1/A12", "3.2")):
        pcb = sub1(pcb, f'(pad "{pad}" smd rect (at {x} -7.355 180) (size 0.6 1.15)',
                   f'(pad "{pad}" smd rect (at {x} -7.3675 180) (size 0.6 1.125)', f"J1 {pad} pcb")
    f["pcb"] = pcb
    mod = f["libs"].get(J1_MOD) or (V198 / J1_MOD).read_bytes().decode("utf-8")
    for pad, x in (("A1/B12", "-3.2"), ("B1/A12", "3.2")):
        mod = sub1(mod, f'(pad "{pad}" smd rect (at {x} -7.355) (size 0.6 1.15)',
                   f'(pad "{pad}" smd rect (at {x} -7.3675) (size 0.6 1.125)', f"J1 {pad} lib")
    f["libs"][J1_MOD] = mod


# --- change 4: input TVS DTVS = SMAJ20A / C571370 at J1 VBUS ----------------
# Exact owner record: .claude/skills/component-high-diode-smaj20a-c571370/.
# Pad 1 = cathode on RAW_USB_VBUS and pad 2 = anode on GND, per that record's
# pin map. Placed left of J1, below MH1. VBUS is taken from the J1 VBUS via
# square at (11.2, 4.7) with a 0.6 mm F.Cu track. GND is a 0.6 mm F.Cu stub to
# the x=8 GND track.
TVS_REF = "DTVS"
TVS_AT = (5.6, 10.87, -90)
TVS_FP = "zudo-led-lamp:SMA_L4.2-W2.6-LS5.3-RD"
TVS_DS = "https://lcsc.com/product-detail/TVS_High-Diode-SMAJ20A_C571370.html"
TVS_MFR = "High Diode(海德)"
TVS_SYM_AT = (279.4, 431.8)
NET_VBUS, NET_GND = (12, "RAW_USB_VBUS"), (5, "GND")
TVS_ROUTE = [
    (NET_VBUS, 0.6, (5.6, 8.3), (5.6, 5.9)),
    (NET_VBUS, 0.6, (5.6, 5.9), (6.3, 4.7)),
    (NET_VBUS, 0.6, (6.3, 4.7), (11.2, 4.7)),
    (NET_GND, 0.6, (5.6, 13.44), (8, 13.44)),
]
TVS_MOD = "libraries/zudo-led-lamp.pretty/SMA_L4.2-W2.6-LS5.3-RD.kicad_mod"
REPO = V199.parents[1]


def _balanced(text, i):
    depth = 0
    for k in range(i, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return k + 1
    raise SystemExit("unbalanced")


def tvs_footprint():
    sym_uuid = uid("DTVS/symbol")
    fab = '(layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15)))'
    props = [("LCSC", "C571370"), ("LCSC Part", "C571370"), ("MPN", "SMAJ20A"),
             ("Manufacturer", TVS_MFR), ("Datasheet", TVS_DS)]
    p = " ".join(f'(property "{k}" "{v}" (at 0 0 -90) {fab} (uuid "{uid("DTVS/" + k)}"))' for k, v in props)
    silk = [((-2.70, -1.36), (2.70, -1.36)), ((-2.70, 1.36), (2.70, 1.36)), ((-1.34, -1.36), (-1.34, 1.36)),
            ((2.70, -1.36), (2.70, -1.01)), ((2.70, 1.36), (2.70, 1.01))]
    crt = [((-2.10, 1.30), (-2.10, -1.30)), ((-2.10, -1.30), (2.10, -1.30)),
           ((2.10, -1.30), (2.10, 1.30)), ((2.10, 1.30), (-2.10, 1.30))]
    g = []
    for i, (a, b) in enumerate(silk):
        g.append(f'(fp_line (start {a[0]:.2f} {a[1]:.2f}) (end {b[0]:.2f} {b[1]:.2f}) (layer "F.SilkS") '
                 f'(stroke (width 0.15) (type solid)) (uuid "{uid(f"DTVS/silk{i}")}"))')
    g.append(f'(fp_circle (center -2.63 1.30) (end -2.60 1.30) (layer "F.SilkS") (stroke (width 0.06) (type solid)) '
             f'(fill none) (uuid "{uid("DTVS/dot")}"))')
    for i, (a, b) in enumerate(crt):
        g.append(f'(fp_line (start {a[0]:.2f} {a[1]:.2f}) (end {b[0]:.2f} {b[1]:.2f}) (layer "F.CrtYd") '
                 f'(stroke (width 0.05) (type solid)) (uuid "{uid(f"DTVS/crt{i}")}"))')
    for i, ys in enumerate(((1.439901, 0.962406), (-1.439901, -0.962406))):
        y0, y1 = ys
        g.append(f'(fp_poly (pts (xy -2.624988 {y0}) (xy -2.624988 {y1}) (xy -3.082188 {y1}) (xy -3.082188 {y0}) '
                 f'(xy -2.624988 {y0})) (stroke (width 0) (type solid)) (fill solid) (layer "F.SilkS") '
                 f'(uuid "{uid(f"DTVS/poly{i}")}"))')
    x, y, r = TVS_AT
    pads = (f'(pad "1" smd rect (at -2.57 0 {r}) (size 2.2 1.7) (layers "F.Cu" "F.Paste" "F.Mask") '
            f'(net {NET_VBUS[0]} "{NET_VBUS[1]}") (uuid "{uid("DTVS/pad1")}")) '
            f'(pad "2" smd rect (at 2.57 0 {r}) (size 2.2 1.7) (layers "F.Cu" "F.Paste" "F.Mask") '
            f'(net {NET_GND[0]} "{NET_GND[1]}") (uuid "{uid("DTVS/pad2")}"))')
    model = ('(model "${KIPRJMOD}/../../footprints/kicad/zudo-led-lamp.3dshapes/SMA_L4.2-W2.6-LS5.3-RD.wrl" '
             '(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    return (f'(footprint "{TVS_FP}" (at {x} {y} {r}) (layer "F.Cu") (attr smd) {p} '
            f'(fp_text reference "{TVS_REF}" (at 0 2.3 {r}) (layer "F.SilkS") '
            f'(effects (font (size 0.8 0.8) (thickness 0.12))) (uuid "{uid("DTVS/ref")}")) '
            f'(fp_text value "SMAJ20A" (at 0 4 {r}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) '
            f'(uuid "{uid("DTVS/value")}")) '
            + " ".join(g) + " " + pads + " " + model +
            f' (uuid "{uid("DTVS/footprint")}") (path "/{ROOT_SHEET}/{sym_uuid}")) ')


def tvs(f):
    pcb = f["pcb"]
    if f'"{TVS_REF}"' in pcb:
        raise SystemExit("DTVS already present")
    anchor = '(footprint "V112-mechanical:NPTH_3.2_SOURCE_TRIAL"'
    i = pcb.index(anchor)
    pcb = pcb[:i] + tvs_footprint() + pcb[i:]
    segs = []
    for n, ((net, _), w, a, b) in enumerate(TVS_ROUTE):
        segs.append(f'(segment (start {a[0]:g} {a[1]:g}) (end {b[0]:g} {b[1]:g}) (width {w:g}) (layer "F.Cu") '
                    f'(net {net}) (uuid "{uid(f"DTVS/seg{n}")}"))')
    end = pcb.rstrip().rindex(")")
    f["pcb"] = pcb[:end].rstrip("\n") + "\n" + "\n".join(segs) + "\n" + pcb[end:]

    sch = f["sch"]
    lib = (REPO / "symbols/zudo-led-lamp.kicad_sym").read_bytes().decode("utf-8")
    li = lib.index('(symbol "SMAJ20A_C571370"')
    cached = " ".join(lib[li:_balanced(lib, li)].split()).replace("( ", "(")
    cached = cached.replace('(symbol "SMAJ20A_C571370"', '(symbol "zudo-led-lamp:SMAJ20A_C571370"', 1)
    lsi = sch.index("(lib_symbols")
    lse = _balanced(sch, lsi)
    sch = sch[:lse - 1] + " " + cached + sch[lse - 1:]
    sx, sy = TVS_SYM_AT
    eff = "(effects (font (size 1.27 1.27)) (hide yes))"
    fields = [("Footprint", TVS_FP), ("Datasheet", TVS_DS), ("LCSC", "C571370"), ("MPN", "SMAJ20A"),
              ("Manufacturer", TVS_MFR), ("LCSC Part", "C571370")]
    inst = (f'(symbol (lib_id "zudo-led-lamp:SMAJ20A_C571370") (at {sx:g} {sy:g} 0) (unit 1) (exclude_from_sim no) '
            f'(in_bom yes) (on_board yes) (dnp no) (uuid "{uid("DTVS/symbol")}") '
            f'(property "Reference" "{TVS_REF}" (at {sx:g} {sy - 5.08:g} 0) (effects (font (size 1.27 1.27)))) '
            f'(property "Value" "SMAJ20A" (at {sx:g} {sy + 5.08:g} 0) (effects (font (size 1.27 1.27)))) '
            + " ".join(f'(property "{k}" "{v}" (at {sx:g} {sy:g} 0) {eff})' for k, v in fields) +
            f' (pin "1" (uuid "{uid("DTVS/pin1")}")) (pin "2" (uuid "{uid("DTVS/pin2")}")) '
            f'(instances (project "husb006-m12-erc-boundary-UNADOPTED" (path "/{ROOT_SHEET}" '
            f'(reference "{TVS_REF}") (unit 1)))))')
    labels = (f' (global_label "RAW_USB_VBUS" (shape passive) (at {sx - 5.08:g} {sy:g} 180) '
              f'(effects (font (size 1.27 1.27)) (justify right)) (uuid "{uid("DTVS/label-vbus")}"))'
              f' (global_label "GND" (shape passive) (at {sx + 5.08:g} {sy:g} 0) '
              f'(effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid("DTVS/label-gnd")}"))')
    k = sch.index("(sheet_instances")
    f["sch"] = sch[:k] + inst + labels + " " + sch[k:]

    f["bom"] = f["bom"].rstrip("\n") + "\n" + (
        f"{TVS_REF},SMAJ20A 20V TVS,SMAJ20A,C571370,{TVS_FP},PENDING USER DECISION (input TVS)\n")
    f["libs"][TVS_MOD] = (REPO / "footprints/kicad/zudo-led-lamp.pretty/SMA_L4.2-W2.6-LS5.3-RD.kicad_mod"
                          ).read_bytes().decode("utf-8")


CHANGES = [
    ("rmh2-187k", rmh2_187k),
    ("cout-datasheet", cout_datasheet),
    ("j1-gnd-trim", j1_gnd_trim),
    ("tvs", tvs),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", action="append", default=[], choices=[n for n, _ in CHANGES])
    ap.add_argument("--out", default=str(V199))
    a = ap.parse_args()
    out = Path(a.out)
    if out.resolve() != V199.resolve():
        out.mkdir(parents=True, exist_ok=True)
        for name in (f"{BASE}.kicad_pro", "fp-lib-table", "sym-lib-table"):
            shutil.copyfile(V198 / name, out / name)
        shutil.copytree(V198 / "libraries", out / "libraries", dirs_exist_ok=True)
    f = {
        "pcb": (V198 / f"{BASE}.kicad_pcb").read_bytes().decode("utf-8"),
        "sch": (V198 / f"{BASE}.kicad_sch").read_bytes().decode("utf-8"),
        "bom": (V198 / "BOM-TRIAL.csv").read_bytes().decode("utf-8"),
        "libs": {},
    }
    for name, fn in CHANGES:
        if name in a.skip:
            print(f"skip  {name}")
            continue
        fn(f)
        print(f"apply {name}")
    (out / f"{BASE}.kicad_pcb").write_bytes(f["pcb"].encode("utf-8"))
    (out / f"{BASE}.kicad_sch").write_bytes(f["sch"].encode("utf-8"))
    (out / "BOM-TRIAL.csv").write_bytes(f["bom"].encode("utf-8"))
    for rel, text in f["libs"].items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))


if __name__ == "__main__":
    main()
