"""V196 -> V198 field-only sync. Touches only footprint/symbol property text.

1. Schematic: add MPN/Manufacturer/LCSC to J1 (exact orderable bound from the GCT
   B4 ordering grid and the JLC C3020560 listing; see ../PROVENANCE.md).
2. PCB: for every footprint, set each schematic field (LCSC, MPN, Manufacturer,
   LCSC Part) as a hidden F.Fab property; overwrite the stale "LCSC Part" value
   with the schematic LCSC code. No other byte of the PCB is changed.
Usage: python3 -I sync_fields.py <project_dir>
"""
import re
import sys
import uuid
from pathlib import Path

NS = uuid.UUID("6b9d6c0e-1f70-4d0b-9b8e-198000000000")
J1_FIELDS = [("MPN", "USB4105-GF-A"), ("Manufacturer", "Global Connector Technology"), ("LCSC", "C3020560")]
SYNC = ("LCSC", "MPN", "Manufacturer", "LCSC Part")


def sch_add_j1(text):
    anchor = re.search(r'\(property "Reference" "J1".*?\(property "Datasheet" "[^"]*" \(at ([\d.]+) ([\d.]+) 0\) \(effects \(font \(size 1\.27 1\.27\)\) \(hide yes\)\)\)', text, re.S)
    if not anchor:
        raise SystemExit("J1 anchor not found")
    x, y = anchor.group(1), anchor.group(2)
    add = "".join(f' (property "{k}" "{v}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))' for k, v in J1_FIELDS)
    return text[:anchor.end()] + add + text[anchor.end():]


def sch_fields(text):
    out = {}
    for part in re.split(r"\(symbol \(lib_id ", text)[1:]:
        props = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', part[:8000]))
        ref = props.get("Reference", "")
        if ref and not ref.startswith("#"):
            out[ref] = {k: props[k] for k in SYNC if k in props}
    return out


def pcb_sync(text, fields):
    starts = [m.start() for m in re.finditer(r'\(footprint "', text)]
    pieces, last, log = [], 0, []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        blk = text[s:e]
        ref = re.search(r'fp_text reference "([^"]+)"', blk).group(1)
        want = dict(fields.get(ref, {}))
        if "LCSC" in want:
            want["LCSC Part"] = want["LCSC"]
        changes = []
        for key, val in want.items():
            pat = re.compile(r'\(property "%s" "([^"]*)"' % re.escape(key))
            m = pat.search(blk)
            if m:
                if m.group(1) != val:
                    changes.append((key, m.group(1), val))
                    blk = blk[:m.start(1)] + val + blk[m.end(1):]
            else:
                u = uuid.uuid5(NS, f"{ref}/{key}")
                prop = f'(property "{key}" "{val}" (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))) (uuid "{u}")) '
                k = blk.index("(fp_text reference")
                blk = blk[:k] + prop + blk[k:]
                changes.append((key, None, val))
        log.append((ref, changes))
        pieces.append(text[last:s] + blk)
        last = e
    pieces.append(text[last:])
    return "".join(pieces), log


def main():
    d = Path(sys.argv[1])
    sch = d / "board-p-COUT1206-TRIAL.kicad_sch"
    pcb = d / "board-p-COUT1206-TRIAL.kicad_pcb"
    s = sch_add_j1(sch.read_text())
    sch.write_text(s)
    p, log = pcb_sync(pcb.read_text(), sch_fields(s))
    pcb.write_text(p)
    for ref, ch in log:
        for key, old, new in ch:
            print(f"{ref}\t{key}\t{old}\t->\t{new}")


if __name__ == "__main__":
    main()
