#!/usr/bin/env python3
"""Independently validate release identity, coordinates, hashes and Gerber/drill data."""
import argparse
import csv
import hashlib
import importlib
import json
import math
import re
from pathlib import Path
import sys
import warnings
import zipfile

ROOT=Path(__file__).resolve().parents[2]
from board_b_layout import WIDTH as BOARD_B_WIDTH, HEIGHT as BOARD_B_HEIGHT
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load


# Per-variant contract. Each board names its schematic spec, its copper layer stack and its nominal outline; the
# 2-layer variants keep exactly the earlier checks, and board-b20-draft (phase 33 binding) is the 4-layer B20 draft.
VARIANTS={
    'board-p':{'spec':'board_p_spec','copper':('F.Cu','B.Cu'),'size':(27,40)},
    'board-p15':{'spec':'board_p15_spec','copper':('F.Cu','B.Cu'),'size':(27,40)},
    'board-b':{'spec':'board_b_spec','copper':('F.Cu','B.Cu'),'size':(BOARD_B_WIDTH,BOARD_B_HEIGHT)},
    'board-b20-draft':{'spec':'board_b20_spec','copper':('F.Cu','In1.Cu','In2.Cu','B.Cu'),'size':(BOARD_B_WIDTH,BOARD_B_HEIGHT)},
}
P_VARIANTS,B_VARIANTS={'board-p','board-p15'},{'board-b','board-b20-draft'}


def require(ok,message):
    if not ok: raise ValueError(message)


def props(node):
    return {atom(n[1]):atom(n[2]) for n in find_all(node,'property')}


def rows(path):
    with path.open() as f: return list(csv.DictReader(f))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release',type=Path)
    parser.add_argument('--write',action='store_true',help='store renders and independent-validation.json in the release and refresh SHA256SUMS (only right after a fresh export)')
    parser.add_argument('--out',type=Path,help='directory for renders and the report when --write is not given (default: a new temporary directory)')
    args=parser.parse_args()
    from gerbonara import LayerStack
    import resvg_py
    release=args.release.resolve()
    if args.write:
        out=release
    else:
        import tempfile
        out=(args.out or Path(tempfile.mkdtemp(prefix='verify-jlcpcb-'))).resolve()
        require(not out.is_relative_to(release),'--out must lie outside the release; use --write to store results in it')
    sums=release/'SHA256SUMS'
    require(sums.is_file(), 'Missing original export checksums')
    checksum_paths=set()
    for line in sums.read_text().splitlines():
        sha,relative=line.split('  ',1)
        require(relative not in checksum_paths, 'Duplicate checksum path')
        checksum_paths.add(relative)
        path=(release/relative).resolve()
        require(path.is_relative_to(release), 'Invalid checksum path')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==sha, f'Release file changed: {relative}')
    require('manifest.json' in checksum_paths, 'Manifest is not checksum locked')
    manifest=json.loads((release/'manifest.json').read_text())
    records=manifest.get('boards', [])
    names=[r['board'] for r in records]
    require(bool(names) and len(names)==len(set(names)) and set(names)<=set(VARIANTS)
            and len(set(names)&P_VARIANTS)<=1 and len(set(names)&B_VARIANTS)<=1, 'Invalid or empty board selection')
    require(bool(manifest.get('artifact_hashes')), 'Missing exported artifact locks')
    for relative,sha in manifest['artifact_hashes'].items():
        path=(release/relative).resolve()
        require(path.is_relative_to(release), 'Invalid artifact path')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==sha, f'Exported artifact changed: {relative}')
    results=[]
    require(set(manifest['artifact_hashes'])<=checksum_paths, 'Export artifacts missing from checksums')
    for record in records:
        name=record['board']; dest=release/name
        variant=VARIANTS[name]
        spec=importlib.import_module(variant['spec'])
        require(tuple(record.get('copper_layers',()))==variant['copper'],f'{name}: exported copper layers differ from the variant stack')
        expected={ref:comp[2] for ref,comp in spec.COMPONENTS.items() if comp[2] and not comp[4]}
        bom={}
        for row in rows(dest/'bom.csv'):
            for ref in row['Designator'].split(','):
                require(ref not in bom,f'Duplicate BOM ref {ref}')
                bom[ref]=row['JLCPCB Part #']
        require(bom==expected,f'{name}: BOM/spec mismatch')
        cpl=rows(dest/'cpl.csv')
        require(len(cpl)==len(expected) and {r['Designator'] for r in cpl}==set(expected),f'{name}: CPL/BOM mismatch')
        board=load(dest/'source'/(name+'.kicad_pcb'))
        fps={props(fp)['Reference']:fp for fp in find_all(board,'footprint')}
        raw={r['Ref']:r for r in rows(dest/'raw/positions.csv')}
        ox,oy=record['origin_mm']
        for row in cpl:
            ref=row['Designator'];fp=fps[ref]
            at=find_all(fp,'at')[0]
            x,y=float(row['Mid X'].removesuffix('mm')),float(row['Mid Y'].removesuffix('mm'))
            require(math.isfinite(x) and math.isfinite(y),f'{ref}: nonfinite position')
            require(abs(x-(float(atom(at[1]))-ox))<.0001 and abs(y-(oy-float(atom(at[2]))))<.0001,f'{ref}: coordinate mismatch')
            layer=atom(find_all(fp,'layer')[0][1])
            require(row['Layer']==('Top' if layer=='F.Cu' else 'Bottom'),f'{ref}: wrong side')
            rotation=float(row['Rotation'])
            require(math.isfinite(rotation) and 0<=rotation<360 and math.isclose(rotation,float(raw[ref]['Rot'])%360,abs_tol=.0001),f'{ref}: incorrect rotation')
            require(props(fp)['LCSC']==expected[ref],f'{ref}: footprint identity mismatch')
        require(bool(record.get('source_hashes')), f'{name}: missing source locks')
        for path,sha in record['source_hashes'].items():
            source_path=(ROOT/path).resolve()
            require(source_path.is_relative_to(ROOT), 'Invalid source path')
            require(hashlib.sha256(source_path.read_bytes()).hexdigest()==sha,f'Source changed: {path}')
        drc=json.loads((dest/'checks/drc.json').read_text())
        erc=json.loads((dest/'checks/erc.json').read_text())
        require(not drc['unconnected_items'],f'{name}: unrouted connections')
        require(not any(v['severity']=='error' for key in ('violations','schematic_parity') for v in drc[key]),f'{name}: DRC errors')
        require(all(v['type']=='extra_footprint' for v in drc['schematic_parity']),f'{name}: schematic parity mismatch')
        require(not any(v['severity']=='error' for sheet in erc['sheets'] for v in sheet['violations']),f'{name}: ERC errors')
        archive=dest/(name+'-gerbers.zip')
        with zipfile.ZipFile(archive) as z:
            require(z.testzip() is None,'Corrupt Gerber ZIP')
            require(set(z.namelist())=={p.name for p in (dest/'gerbers').iterdir()},'Gerber ZIP contents mismatch')
            for path in (dest/'gerbers').iterdir():require(z.read(path.name)==path.read_bytes(),'Stale zipped Gerber')
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');stack=LayerStack.open(archive)
        # gerbonara names its temporary extraction directory in each note; keep only the file name so reports are deterministic
        notes=[re.sub(r'\S*/input/','',str(w.message)) for w in caught if not issubclass(w.category,ResourceWarning)]
        require(all('G90 header statement found after end of header' in n for n in notes),f'Unexpected Gerber parser warnings: {notes}')
        copper=variant['copper']
        require(len(stack.copper_layers)==len(copper) and stack.drill_pth is not None and stack.drill_npth is not None,
                f'Expected {len(copper)} copper layers and PTH/NPTH drill data')
        inner=[layer for layer in copper if layer.startswith('In')]
        gerber_names=[p.name for p in (dest/'gerbers').iterdir()]
        for layer in copper:
            tag=layer.replace('.','_')
            require(sum(n.startswith(f'{name}-{tag}.') for n in gerber_names)==1,f'{name}: expected one {layer} Gerber')
        stray=[n for n in gerber_names if re.search(r'In\d+_Cu',n) and not any(l.replace('.','_') in n for l in inner)]
        require(not stray,f'{name}: inner-layer Gerbers outside the variant stack: {stray}')
        expected_size=variant['size']
        width,height=stack.outline.size('mm')
        require(abs(width-expected_size[0])<.06 and abs(height-expected_size[1])<.06,'Wrong board outline')
        for side in ('top','bottom'):
            render=out/name if out!=release else dest
            render.mkdir(parents=True,exist_ok=True)
            svg=str(stack.to_pretty_svg(side=side));(render/f'gerber-{side}.svg').write_text(svg)
            (render/f'gerber-{side}.png').write_bytes(resvg_py.svg_to_bytes(svg_string=svg,width=1500,dpi=96))
        results.append({'board':name,'identity_coordinates_hashes':'PASS','gerber_drill_parse':'PASS','size_mm':[width,height],
                        'fitted_components':len(expected),'parser_notes':notes})
    (out/'independent-validation.json').write_text(json.dumps(results,indent=2)+'\n')
    if args.write:
        paths=[p for p in sorted(release.rglob('*')) if p.is_file() and p.name!='SHA256SUMS' and p.suffix not in ('.lck','.kicad_prl')]
        (release/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(release))+'\n' for p in paths))
    else:
        print(f'release left unchanged; report and renders in {out}',file=sys.stderr)
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
