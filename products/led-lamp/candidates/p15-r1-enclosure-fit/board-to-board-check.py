# Scratch check (P15P): P15 component bodies vs Board L in the LED enclosure stack, nominal datums from
# enclosure/generate.py (floor_top 8.4, Board P bottom 13.4, Board L bottom 26.0). Board L substrate is a plate:
# compare body zmax with its bottom. Board L bodies: AABB screen, exact boolean only for AABB-overlapping pairs.
import json, re, subprocess, sys, tempfile, time
from pathlib import Path
import cadquery as cq
led = Path(sys.argv[1]); out = Path(sys.argv[2]); t0 = time.time()
p_bottom, l_bottom = 13.4, 26.0
def export(board, kind):
    original = led / f'boards/{board}/{board}.kicad_pcb'
    def sp(m):
        p = Path(m[1].replace('${KIPRJMOD}', str(original.parent))).resolve()
        return '(model "' + str(p.with_suffix('.step') if p.suffix.lower() == '.wrl' else p) + '"'
    t = Path(tempfile.mkdtemp(dir='/tmp')); b = t / f'{board}.kicad_pcb'
    b.write_text(re.sub(r'\(model "([^"]+)"', sp, original.read_text()))
    tgt = t / f'{board}-{kind}.step'
    flags = ['--board-only'] if kind == 'substrate' else ['--component-filter', '*']
    subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--subst-models', '--no-dnp', *flags, '--user-origin', '0x0mm', '-o', str(tgt), str(b)], check=True, capture_output=True)
    return cq.importers.importStep(str(tgt)).val()
boards = {}
for board, bottom, xoff in [('board-l', l_bottom, -30), ('board-p', p_bottom, -13.5)]:
    sub = export(board, 'substrate'); bb = sub.BoundingBox()
    comp = export(board, 'components')
    v = cq.Vector(xoff, 30, bottom - bb.zmin)
    sols = []
    for s in comp.Solids():
        sb = s.BoundingBox()
        if all(abs(getattr(sb, k) - getattr(bb, k)) < .002 for k in ('xmin','xmax','ymin','ymax','zmin','zmax')):
            continue
        s = s.translate(v); sols.append((s, s.BoundingBox()))
    boards[board] = sols
    print(board, len(sols), 'solids', round(time.time() - t0), 's', flush=True)
def kxy(b, xoff): return [round(b.center.x - xoff, 2), round(30 - b.center.y, 2)]
gaps, hits = [], []
for s, b in boards['board-p']:
    gaps.append({'p15_body_kicad_xy': kxy(b, -13.5), 'zmax': round(b.zmax, 3), 'gap_to_board_l_bottom_mm': round(l_bottom - b.zmax, 3)})
    for o, ob in boards['board-l']:
        if all(getattr(b, f'{x}min') < getattr(ob, f'{x}max') - 1e-3 and getattr(ob, f'{x}min') < getattr(b, f'{x}max') - 1e-3 for x in 'xyz'):
            vol = s.intersect(o).Volume()
            hits.append({'p15_body_kicad_xy': kxy(b, -13.5), 'board_l_body_kicad_xy': kxy(ob, -30), 'p15_z': [round(b.zmin, 2), round(b.zmax, 2)],
                         'board_l_z': [round(ob.zmin, 2), round(ob.zmax, 2)], 'volume_mm3': round(vol, 4)})
gaps.sort(key=lambda g: g['gap_to_board_l_bottom_mm'])
res = {'datums_mm': {'board_p_bottom': p_bottom, 'board_l_bottom': l_bottom}, 'p15_bodies': len(boards['board-p']), 'board_l_bodies': len(boards['board-l']),
       'aabb_overlapping_pairs': hits, 'tightest_p15_bodies': gaps[:6], 'seconds': round(time.time() - t0)}
out.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
