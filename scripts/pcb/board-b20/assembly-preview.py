#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1"]
# ///
"""Review-only Board P + board-b20-draft stack preview.

usage: uv run scripts/pcb/board-b20/assembly-preview.py --kicad-cli CLI --kicad-python PY [--output DIR]

Drives the unchanged helpers of scripts/pcb/export-assembly-preview.py (native STEP datums, the face-to-face P(x,y) ->
B(y-0.5,x+12) transform, the cross-board collision screen and the corner-support collar screen) for B20. That
generator and the Board B mechanical verifiers stay unchanged because their hashes bind the 15 V package's stack proof.
B20 differences:
- the mechanical check is scripts/pcb/board-b20/verify-mechanics.py (B20 net names and rail labels; pogo row OPEN);
- the B20 stackup (JLC7628 layer values from the draft page) sums to 1.59 mm against the declared 1.6 mm board, so the
  B20 core uses a local copy of native_parts that takes the thickness from the PCB instead of the fixed 1.6 mm;
- B20 has no bulk C5. The reviewed C5 envelope (11.2 x 11.2 x 11.0 mm at the contract center) is still screened as a
  reserved column against Board P, and every fitted B20 part is screened in the populated collision check.
Nominal CAD screening only: no physical fit, seating, flex or electrical qualification.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location('assembly_preview', ROOT / 'scripts/pcb/export-assembly-preview.py')
ap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ap)
cq = ap.cq
require, sha, command, bounds, overlaps = ap.require, ap.sha, ap.command, ap.bounds, ap.overlaps
find_all, properties, load, parse, tokenize = ap.find_all, ap.properties, ap.load, ap.parse, ap.tokenize
atom, math, NativeAssembly, serialize, resolve_model = ap.atom, ap.math, ap.NativeAssembly, ap.serialize, ap.resolve_model

B_NAME = 'board-b20-draft'
B_PCB = ROOT / 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
HELPERS = ROOT / 'scripts/pcb/export-assembly-preview.py'
VERIFIER = ROOT / 'scripts/pcb/board-b20/verify-mechanics.py'


def native_parts(tree,project,scratch,cli):
    """Copy of the shared helper with the board thickness taken from the PCB's own stackup (B20: 1.59 mm, see module doc).

    PD20: Board P r3 is two-sided, so B.Cu component models are accepted too. KiCad flips a B.Cu footprint's model, so a
    B.Cu model is attributed to the footprint within the length of its XY offset (plus 0.001 mm) instead of exactly.
    """
    work=copy.deepcopy(tree);sources={};expected={}
    for footprint in find_all(work,'footprint'):
        ref=properties(footprint)['Reference']
        attrs=[atom(v) for node in find_all(footprint,'attr') for v in node[1:]]
        fitted='dnp' not in attrs
        for model in find_all(footprint,'model'):
            path=resolve_model(model,project)
            step=path.with_suffix('.step') if path.suffix.lower()=='.wrl' else path
            require(step.is_file(),'Missing STEP companion: '+str(step))
            for source in (path,step):sources[str(source.relative_to(ROOT))]=sha(source)
            model[1]=('str',str(step))
            if fitted:
                require(ref not in expected,'Multiple models per fitted component need explicit grouping')
                side=atom(find_all(footprint,'layer')[0][1])
                require(side in ('F.Cu','B.Cu'),'Component models must sit on F.Cu or B.Cu')
                at=[float(atom(v)) for v in find_all(footprint,'at')[0][1:]]
                theta=math.radians(at[2] if len(at)>2 else 0)
                offset=[float(atom(v)) for v in find_all(find_all(model,'offset')[0],'xyz')[0][1:]]
                if side=='F.Cu':
                    expected[ref]=(at[0]+offset[0]*math.cos(theta)-offset[1]*math.sin(theta),
                                   -at[1]+offset[0]*math.sin(theta)+offset[1]*math.cos(theta),.001)
                else:
                    expected[ref]=(at[0],-at[1],math.hypot(offset[0],offset[1])+.001)
    temporary=scratch/'native-export.kicad_pcb';temporary.write_text(serialize(work)+'\n')
    exported=[]
    for tag,flags in [('core',['--board-only']),('populated',[])]:
        output=scratch/(tag+'.step')
        command([cli,'pcb','export','step','--force','--no-dnp','--output',output,*flags,temporary])
        exported.append(cq.importers.importStep(str(output)).val())
    core,whole=exported;bb=bounds(core)
    stackup=find_all(find_all(tree,'setup')[0],'stackup')
    require(len(stackup)==1,'Explicit PCB stackup required')
    thickness={atom(layer[1]):float(atom(find_all(layer,'thickness')[0][1])) for layer in find_all(stackup[0],'layer') if find_all(layer,'thickness')}
    total=sum(thickness.values())
    declared=float(atom(find_all(find_all(tree,'general')[0],'thickness')[0][1]))
    require(abs(total-declared)<=.0105,f'Stackup {total} mm differs from the declared {declared} mm board by more than 0.01 mm')
    lower=thickness['B.Cu']+thickness['B.Mask'];upper=thickness['F.Cu']+thickness['F.Mask']
    core_t=bb[5]-bb[2]
    require(min(abs(core_t-(t-lower-upper)) for t in (total,declared))<.003,'Native STEP core disagrees with stackup')
    board_t=total if abs(core_t-(total-lower-upper))<.003 else declared
    shift=-board_t+lower-bb[2]
    # Preserve native assembly hierarchy: imported STEP models may contain many
    # solids and lose their reference name, but each top-level component keeps
    # its native placement. Match that origin to the exact footprint/model node.
    imported=NativeAssembly.load(str(scratch/'populated.step'));parts={};cores=[];native_solids=[]
    for child in imported.children:
        shape=child.toCompound()
        native_solids.extend(shape.Solids())
        if all(abs(a-b)<.003 for a,b in zip(bounds(shape),bb)):
            cores.append(shape);continue
        origin=child.loc.toTuple()[0]
        matches=[ref for ref,point in expected.items() if math.dist(origin[:2],point[:2])<point[2]]
        require(len(matches)==1,'Native component cannot be uniquely attributed: '+child.name+' '+str(origin))
        ref=matches[0];require(ref not in parts,'Duplicate native component '+ref)
        parts[ref]=shape.translate((0,0,shift))
    require(len(cores)==1,'Native substrate is not uniquely identifiable')
    require(set(parts)==set(expected),'Native export omitted/added fitted model references')
    # Integrate each solid separately. OpenCascade's compound-level integration
    # gives different numeric results for equivalent nested/flat compounds.
    # The same 270 B solids agree exactly when integrated individually.
    flat_solids=whole.Solids();attributed_volume=sum(part.Volume() for part in native_solids)
    flat_volume=sum(part.Volume() for part in flat_solids)
    require(len(native_solids)==len(flat_solids) and abs(attributed_volume-flat_volume)<.01,
            f'Native hierarchy count/volume differs from flat native solids: {len(native_solids)}/{len(flat_solids)}, {attributed_volume}/{flat_volume}')
    native_boxes=sorted(tuple(round(v,5) for v in bounds(part)) for part in native_solids)
    flat_boxes=sorted(tuple(round(v,5) for v in bounds(part)) for part in flat_solids)
    require(all(max(abs(x-y) for x,y in zip(a,b))<.003 for a,b in zip(native_boxes,flat_boxes)),
            'Native hierarchy solid bounds differ from flat native geometry')
    return core.translate((0,0,shift)),parts,sources,{'native_core_bounds_mm':bb,'stackup_total_mm':total,'declared_thickness_mm':declared,'modelled_thickness_mm':board_t,'world_z_translation_mm':shift,
            'fitted_components':len(parts),'component_solids':sum(len(part.Solids()) for part in parts.values()),
            'hierarchy_geometry_check':{'status':'PASS','solid_count_including_core':len(native_solids),
                                        'sum_individual_volume_mm3':attributed_volume,'flat_sum_individual_volume_mm3':flat_volume,
                                        'every_solid_bounds_match':True},
            'component_bounds_mm':{ref:bounds(shape) for ref,shape in parts.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board-p', choices=sorted(ap.P_BOARDS), default='board-p')
    parser.add_argument('--output', type=Path, default=ROOT / 'boards/board-b20-draft/assembly-preview')
    parser.add_argument('--kicad-cli', required=True)
    parser.add_argument('--kicad-python', required=True)
    args = parser.parse_args()
    p_name = args.board_p
    b_pcb, p_pcb, project = B_PCB, ROOT / ap.P_BOARDS[p_name], B_PCB.parent
    output = args.output.resolve()
    require(not output.exists(), 'Choose a new preview output directory; never overwrite an existing review')
    b_tree, p_tree = load(b_pcb), load(p_pcb)
    source_hashes = {B_NAME: sha(b_pcb), p_name: sha(p_pcb)}
    contract_path = ROOT / 'boards/board-b/mechanical.json'
    contract = json.loads(contract_path.read_text())
    contract_hash, helpers_hash = sha(contract_path), sha(HELPERS)
    verification_sources = {str(path.relative_to(ROOT)): sha(path) for path in
                            [Path(__file__).resolve(), VERIFIER, ROOT / 'scripts/pcb/verify-compact-mechanics.py',
                             ROOT / 'scripts/pcb/board_b_layout.py', ROOT / 'scripts/pcb/check-model-bodies.py',
                             ROOT / 'scripts/schgen/board_b20_spec.py', ROOT / 'boards/board-p/mechanical.json',
                             ROOT / 'boards/board-b/supports/hc11-evidence.json',
                             ROOT / '.claude/skills/component-kangnex-wj500v-5-08-2p-c8465/facts.json']}
    require(contract['terminal_blocks']['maximum_tail_projection_mm'] == 4.7, 'Unreviewed terminal tail envelope')
    output.mkdir(parents=True)
    command([args.kicad_python, VERIFIER, b_pcb, '--output', output / 'mechanical-check.json'])
    for name, pcb, directory in [(B_NAME, b_pcb, project), ('board-p', p_pcb, p_pcb.parent)]:
        command([sys.executable, ROOT / 'scripts/pcb/check-model-bodies.py', pcb, '--project-dir', directory,
                 '--output', output / (name + '-model-bodies.json')])
    with tempfile.TemporaryDirectory(prefix='zudo-pd-b20-assembly-') as temporary:
        scratch = Path(temporary)
        (scratch / 'b').mkdir()
        (scratch / 'p').mkdir()
        b_core, b_parts, b_sources, b_datum = native_parts(b_tree, project, scratch / 'b', args.kicad_cli)
        p_core, p_parts, p_sources, p_datum = native_parts(p_tree, p_pcb.parent, scratch / 'p', args.kicad_cli)
        p_core = ap.place_board_p(p_core, contract)
        p_parts = {ref: ap.place_board_p(part, contract) for ref, part in p_parts.items()}
        collision = ap.cross_board_screen(b_core, b_parts, p_core, p_parts, contract)
        (output / 'populated-collision-check.json').write_text(json.dumps(collision, indent=2) + '\n')
        require(collision['status'] == 'PASS', 'Populated cross-board collision: ' + str(collision['failures']))
        header_spacing = []
        for spacing in (11.0, 11.08, 11.1):
            check = ap.cross_board_screen(b_core, {'J5': b_parts['J5']}, p_core,
                                          {'JOUT1': p_parts['JOUT1'].translate((0, 0, spacing - 11.1))}, contract)
            header_spacing.append({'nominal_plane_spacing_mm': spacing, 'status': check['status'],
                                   'unintended_intersection_mm3': check['maximum_unintended_intersection_mm3']})
        terminal_screens = []
        for item in contract['terminal_blocks']['placements']:
            ref = item['reference']
            fx, fy = item['center_mm']
            # Same maximum housing and 1 x 1 x 4.7 mm tail envelopes as the Board B generator.
            housing = cq.Workplane('XY').box(11.56, 10.4, 14.2).translate((0, .5, 7.1)).val()
            housing = housing.rotate((0, 0, 0), (0, 0, 1), 90).translate((fx, -fy, 0))
            tails = [cq.Workplane('XY').box(1, 1, 4.7).translate((fx + ly, -(fy - lx), -2.35)).val()
                     for lx, ly in contract['terminal_blocks']['pad_centers_local_mm'].values()]
            worst = 0
            for candidate in [b_parts[ref], housing, *tails]:
                for part in [p_core, *p_parts.values()]:
                    if overlaps(candidate, part):
                        volume = candidate.intersect(part).Volume()
                        worst = max(worst, volume)
                        require(volume <= .005, ref + ': terminal or tail envelope intersects Board P')
            terminal_screens.append({'reference': ref, 'status': 'PASS', 'maximum_intersection_mm3': worst})
        c5 = contract['pd_stack']['c5_envelope']
        require(c5['size_mm'] == [11.2, 11.2, 11.0] and c5['origin_z_mm'] == 0, 'Unreviewed C5 envelope')
        cx, cy = c5['center_mm']
        envelope = cq.Workplane('XY').box(*c5['size_mm']).translate((cx, -cy, 5.5)).val()
        pairs = []
        for ref, part in {'substrate': p_core, **p_parts}.items():
            if overlaps(envelope, part):
                volume = envelope.intersect(part).Volume()
                pairs.append({'board_p': ref, 'intersection_mm3': volume})
                require(volume <= .005, 'Reserved C5 envelope column intersects Board P ' + ref)
        c5_screen = {'status': 'PASS', 'basis': 'reserved Board B C5 envelope column at the contract center; '
                     'board-b20-draft fits no bulk C5 there (its C5 is a 0603 part screened in the populated check)',
                     'envelope_world_bounds_mm': bounds(envelope), 'overlapping_bbox_pairs_checked': pairs}
        support_screen = ap.support_collar_screen(b_parts, p_core, p_parts, contract)
        stacked = cq.Assembly(name='zudo_pd_board_p_stacked')
        stacked.add(p_core, name='substrate', color=cq.Color(.15, .47, .25))
        for ref, part in p_parts.items():
            stacked.add(part, name=ref, color=cq.Color(.63, .65, .67))
        stacked.export(str(output / 'board-p-stacked.step'))
        ap.clean_step(output / 'board-p-stacked.step')
        assembly = cq.Assembly(name='zudo_pd_b20_stack_review')
        assembly.add(b_core, name='board_b_substrate', color=cq.Color(.10, .38, .20))
        assembly.add(p_core, name='board_p_substrate', color=cq.Color(.15, .47, .25))
        for tag, parts in [('b', b_parts), ('p', p_parts)]:
            for ref, part in parts.items():
                assembly.add(part, name=f'board_{tag}_{ref}', color=cq.Color(.63, .65, .67))
        assembly.export(str(output / 'populated-stack.step'))
        ap.clean_step(output / 'populated-stack.step')
    preview = copy.deepcopy(b_tree)
    models = output / 'models'
    models.mkdir()
    for fp in find_all(preview, 'footprint'):
        for model in find_all(fp, 'model'):
            path = ap.resolve_model(model, project)
            for asset in (path, path.with_suffix('.step')):
                require(asset.is_file(), 'Missing preview companion: ' + str(asset))
                target = models / asset.name
                if target.exists():
                    require(sha(target) == sha(asset), 'Conflicting preview model basename')
                else:
                    shutil.copyfile(asset, target)
            model[1] = ('str', '${KIPRJMOD}/models/' + path.name)
    mechanical = ('(footprint "zudo-pd:Mechanical_Preview" (layer "F.Cu") (at 0 0) (uuid "'
                  + str(uuid.uuid5(uuid.NAMESPACE_URL, 'zudo-pd/b20-assembly-preview'))
                  + '") (property "Reference" "PD_PREVIEW" (at 0 0) (layer "F.Fab") (effects (font (size 1 1)) hide))'
                  ' (property "Value" "PD_STACK_REVIEW_ONLY" (at 0 0) (layer "F.Fab") (effects (font (size 1 1)) hide))'
                  ' (attr board_only exclude_from_pos_files exclude_from_bom) (model "${KIPRJMOD}/board-p-stacked.step"'
                  ' (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))')
    preview.append(parse(tokenize(mechanical)))
    restored = copy.deepcopy(preview)
    restored.pop()
    require(ap.without_models(restored) == ap.without_models(b_tree), 'Preview changed original B20 non-model geometry')
    preview_path = output / 'preview.kicad_pcb'
    preview_path.write_text(ap.serialize(preview) + '\n')
    shutil.copyfile(project / (B_NAME + '.kicad_pro'), output / 'preview.kicad_pro')
    command([sys.executable, ROOT / 'scripts/pcb/check-model-paths.py', preview_path, '--output', output / 'model-paths.json'])
    for side in ('top', 'bottom'):
        command([args.kicad_cli, 'pcb', 'render', '--side', side, '--rotate', '20,0,-15', '--width', '1800', '--height',
                 '1400', '--quality', 'high', '--zoom', '.8', '--output', output / (side + '.png'), preview_path])
    (output / 'preview.kicad_prl').unlink(missing_ok=True)
    require(not list(output.glob('*.lck')), 'Preview is still open/locked')
    sources = {**b_sources, **p_sources}
    for name, expected in sources.items():
        require(sha(ROOT / name) == expected, 'Component model changed during preview generation')
    require(sha(b_pcb) == source_hashes[B_NAME] and sha(p_pcb) == source_hashes[p_name], 'Source PCB changed')
    require(sha(contract_path) == contract_hash and sha(HELPERS) == helpers_hash, 'Helpers or contract changed')
    for name, expected in verification_sources.items():
        require(sha(ROOT / name) == expected, 'Mechanical verifier changed during generation')
    (output / 'README.md').write_text(
        'Review-only Board P + board-b20-draft assembly. Open preview.kicad_pcb in KiCad and use its 3D viewer. '
        'Component models are bundled locally. The display footprint for Board P is BOM/CPL-excluded; never use this '
        'file for fabrication. Source PCBs are unchanged. populated-stack.step is a local-only derivative. Nominal CAD '
        'fit does not qualify installed hardware, wire access or powered behavior. The B20 draft carries the front/back '
        'rail labels but no top-edge pogo row (OPEN).\n')
    mech = json.loads((output / 'mechanical-check.json').read_text())
    report = {'schema_version': 1, 'status': 'PASS', 'board_b': B_NAME, 'board_p': p_name, 'board_p_pcb': ap.P_BOARDS[p_name],
              'draft': True, 'pcb_sha256': source_hashes,
              'generator_sha256': helpers_hash,
              'generator_note': 'generator_sha256 binds the shared helpers in scripts/pcb/export-assembly-preview.py; the B20 '
                                'driver and verifier hashes are in verification_sources_sha256',
              'mechanical_spec_sha256': contract_hash, 'model_sources_sha256': sources,
              'verification_sources_sha256': verification_sources,
              'original_B_nonmodel_geometry_unchanged': True, 'model_only_footprints_added': 1, 'manufacturing_use': False,
              'pd_transform': 'P(x,y) -> B(y-0.5,x+12)', 'board_p_top_z_mm': contract['pd_stack']['nominal_board_p_top_z_mm'],
              'native_step_datums': {B_NAME: b_datum, 'board-p': p_datum},
              'mechanical_check_status': mech['status'], 'pogo_row': mech['pogo_row'],
              'terminal_to_pd_clearance': terminal_screens, 'populated_cross_board_clearance': collision,
              'c5_envelope_clearance': c5_screen, 'header_spacing_comparison': header_spacing,
              'project_support_collar_clearance': support_screen,
              'limits': ['Catalog and maximum-envelope model geometry is illustrative; physical fit, board flex and seating '
                         'tolerances remain unmeasured.',
                         'Only the J5/JOUT1 contact columns may intersect; own-board interfaces are outside this test.',
                         'Support collar columns are project assumptions; the HC11 flat-floor height conflict remains open.',
                         'The B20 pogo row and rail labels are absent (OPEN). No electrical or thermal qualification is implied.'],
              'artifact_sha256': {str(path.relative_to(output)): sha(path) for path in sorted(output.rglob('*')) if path.is_file()}}
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'output': str(output), 'pcb_sha256': source_hashes}))


if __name__ == '__main__':
    main()
