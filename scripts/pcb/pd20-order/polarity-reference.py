"""List pad 1 of every polarized fitted part from a package's locked source PCB. Read-only desk evidence.

usage: python3 scripts/pcb/pd20-order/polarity-reference.py [--release DIR] [--board NAME ...] [--json]

`cpl.csv` holds only designator, centre, side and rotation. Pad numbers and nets live in the exported
`<board>/source/<board>.kicad_pcb`, which SHA256SUMS locks. This prints, per polarized part (D*, DZ*, Q*, U*, J*
and electrolytic C* on a `CAP-SMD_BD` footprint, in the CPL), the CPL row, the footprint, the pad-1 net and the pad-1 centre in CPL coordinates (X right, Y up from the
manifest origin). What pad 1 *means* (cathode, pin 1, source) comes from the part's owner pin map under
`.claude/skills/component-*/`, not from this listing. JLC places with its own library footprints, so agreement here
does not prove the placed orientation; the supplier preview is the check that counts.
"""
import argparse, csv, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load  # noqa: E402

DEFAULT_RELEASE = ROOT / 'manufacturing/releases/pd20-sourcing-review-20261122'
POLARIZED_PREFIXES = ('DZ', 'D', 'Q', 'U', 'J')
POLARIZED_CAP_FOOTPRINT = 'CAP-SMD_BD'  # electrolytic can footprints; ceramics are non-polar


def children(node, tag):
    return [x for x in node if isinstance(x, list) and x and atom(x[0]) == tag]


def pad_one(fp):
    pads = [p for p in children(fp, 'pad') if atom(p[1]) == '1']
    if not pads:
        return None, None
    pad = pads[0]
    net = children(pad, 'net')
    at = children(pad, 'at')[0]
    return (atom(net[0][-1]) if net else None), (float(atom(at[1])), float(atom(at[2])))


def absolute(fp_at, local):
    x, y = float(atom(fp_at[1])), float(atom(fp_at[2]))
    angle = math.radians(float(atom(fp_at[3])) if len(fp_at) > 3 else 0.0)
    px, py = local
    # KiCad rotates footprint-local pad coordinates counter-clockwise on screen with Y pointing down.
    return x + px * math.cos(angle) + py * math.sin(angle), y - px * math.sin(angle) + py * math.cos(angle)


def board_rows(pcb_path, cpl_path, origin):
    cpl = {r['Designator']: r for r in csv.DictReader(open(cpl_path))}
    ox, oy = origin
    rows = []
    for fp in find_all(load(pcb_path), 'footprint'):
        props = {atom(n[1]): atom(n[2]) for n in find_all(fp, 'property')}
        ref = props['Reference']
        footprint = atom(fp[1]).split(':')[-1]
        polarized = ref.startswith(POLARIZED_PREFIXES) or (ref.startswith('C') and footprint.startswith(POLARIZED_CAP_FOOTPRINT))
        if ref not in cpl or not polarized or not ref[len(ref.rstrip('0123456789')):]:
            continue
        net, local = pad_one(fp)
        if local is None:
            continue
        x, y = absolute(children(fp, 'at')[0], local)
        row = cpl[ref]
        rows.append({'ref': ref, 'value': props.get('Value'), 'lcsc': props.get('LCSC'),
                     'footprint': footprint, 'side': row['Layer'], 'rotation': row['Rotation'],
                     'cpl_mid_mm': [row['Mid X'], row['Mid Y']], 'pad1_net': net,
                     'pad1_cpl_mm': [round(x - ox, 3), round(oy - y, 3)]})
    order = lambda r: (r['side'] != 'Top', r['ref'].rstrip('0123456789'), int(r['ref'][len(r['ref'].rstrip('0123456789')):]))
    return sorted(rows, key=order)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--release', type=Path, default=DEFAULT_RELEASE)
    parser.add_argument('--board', action='append')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    manifest = json.loads((args.release / 'manifest.json').read_text())
    out = {}
    for record in manifest['boards']:
        name = record['board']
        if args.board and name not in args.board:
            continue
        out[name] = board_rows(args.release / name / 'source' / f'{name}.kicad_pcb', args.release / name / 'cpl.csv',
                               record['origin_mm'])
    if args.json:
        print(json.dumps(out, indent=1))
        return 0
    for name, rows in out.items():
        print(f'\n### {name}\n')
        print('| Ref | Part | LCSC | Footprint | Side | Rot | Pad-1 net | Pad-1 centre X, Y (mm, CPL frame) |')
        print('| --- | --- | --- | --- | --- | ---: | --- | --- |')
        for r in rows:
            x, y = r['pad1_cpl_mm']
            print(f"| {r['ref']} | {r['value']} | {r['lcsc']} | {r['footprint']} | {r['side']} | {r['rotation']} | "
                  f"`{r['pad1_net']}` | {x:.3f}, {y:.3f} |")
    return 0


if __name__ == '__main__':
    sys.exit(main())
