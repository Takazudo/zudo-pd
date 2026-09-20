#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "vtk==9.3.1"]
# ///
"""Check STEP companions against WRL surfaces; optionally apply reviewed translations.

Bounding boxes propose no new transforms here. Each permitted rigid translation
is hash-locked in step-datum-normalizations.json and checked against sampled
surfaces in both directions before any STEP is replaced. WRL, footprints and
PCBs are never changed. This proves consistency with existing visualization,
not exact manufacturer geometry or measured assembly fit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'footprints/kicad/zudo-pd.3dshapes'
REVIEW = Path(__file__).with_name('step-datum-normalizations.json')
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wrl_mesh(path):
    text = path.read_text()
    require(not re.search(r'\bTransform\s*\{', text), 'Unreviewed nested WRL transform: ' + path.name)
    vertices, faces = [], []
    for block in re.split(r'Shape\s*\{', text)[1:]:
        coordinates = re.search(r'point\s*\[([^]]+)\]', block)
        indices = re.search(r'coordIndex\s*\[([^]]+)\]', block)
        if not coordinates or not indices:
            continue
        numbers = [float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?', coordinates.group(1))]
        points = np.array(numbers).reshape(-1, 3) * 2.54
        offset = len(vertices)
        vertices.extend(points)
        polygon = []
        for index in [int(v) for v in re.findall(r'-?\d+', indices.group(1))]:
            if index == -1:
                for j in range(1, len(polygon)-1):
                    faces.append([offset+polygon[0], offset+polygon[j], offset+polygon[j+1]])
                polygon = []
            else:
                require(0 <= index < len(points), 'WRL face index out of range')
                polygon.append(index)
    require(vertices and faces, 'No WRL triangle mesh: ' + path.name)
    return np.array(vertices), np.array(faces)


def locator(vertices, faces):
    data = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.array(vertices, dtype=float), deep=True))
    data.SetPoints(points)
    cells = vtk.vtkCellArray()
    packed = np.hstack([np.full((len(faces), 1), 3), faces]).astype(np.int64).ravel()
    cells.SetCells(len(faces), numpy_to_vtkIdTypeArray(packed, deep=True))
    data.SetPolys(cells)
    tree = vtk.vtkStaticCellLocator()
    tree.SetDataSet(data)
    tree.BuildLocator()
    return tree


def samples(vertices, faces):
    distinct = np.unique(vertices.round(8), axis=0)
    centers = vertices[faces].mean(1)
    if len(distinct) > 2048:
        distinct = distinct[np.linspace(0, len(distinct)-1, 2048, dtype=int)]
    if len(centers) > 1024:
        centers = centers[np.linspace(0, len(centers)-1, 1024, dtype=int)]
    return np.vstack([distinct, centers])


def distances(tree, points):
    closest = [0., 0., 0.]
    cell, sub, squared = vtk.reference(0), vtk.reference(0), vtk.reference(0.)
    result = []
    for point in points:
        tree.FindClosestPoint(point, closest, cell, sub, squared)
        result.append(float(squared)**.5)
    return np.array(result)


def shape_bounds(shape):
    # Ignore any tessellation cache left by surface_check: compare exact B-rep
    # bounds before and after STEP serialization, not mesh-dependent bounds.
    box=Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped,box,False,False)
    x0,y0,z0,x1,y1,z1=box.Get()
    return [[x0,y0,z0],[x1,y1,z1]]


def surface_check(shape, vertices, faces, tolerance, allow_internal=False):
    step_vertices, step_faces = shape.tessellate(.02, .08)
    sv = np.array([v.toTuple() for v in step_vertices])
    sf = np.array(step_faces)
    ws = samples(vertices, faces)
    forward = distances(locator(sv, sf), ws)
    backward = distances(locator(vertices, faces), samples(sv, sf))
    exceptional = ws[forward > tolerance]
    internal_count = 0
    if len(exceptional) and allow_internal:
        internal_count = sum(bool(shape.isInside(cq.Vector(*point), 1e-5)) for point in exceptional)
    require(len(exceptional) == internal_count,
            f'WRL points differ from STEP exterior: maximum {forward.max():.6f} mm; {len(exceptional)-internal_count} unresolved samples')
    require(backward.max() <= tolerance, f'STEP points differ from WRL surface: maximum {backward.max():.6f} mm')
    return {'wrl_to_step_max_mm':float(forward.max()), 'step_to_wrl_max_mm':float(backward.max()),
            'wrl_to_step_p99_mm':float(np.percentile(forward,99)), 'step_to_wrl_p99_mm':float(np.percentile(backward,99)),
            'wrl_samples':len(forward), 'step_samples':len(backward),
            'wrl_samples_strictly_inside_step_exception':internal_count}


def run(normalize=False,board_b=None):
    review = json.loads(REVIEW.read_text())
    tolerance = review['maximum_external_surface_deviation_mm']
    boards=[ROOT/'boards/board-p/board-p.kicad_pcb',board_b or ROOT/'boards/board-b/board-b.kicad_pcb']
    active_names=set()
    for board in boards:
        for footprint in find_all(load(board),'footprint'):
            for model in find_all(footprint,'model'):active_names.add(Path(atom(model[1])).name)
    require(active_names=={item['wrl'] for item in review['models']},
            'Active model set differs from the reviewed datum manifest; update the bounded audit')
    report = {'schema_version':1, 'status':'PASS', 'review_sha256':sha(REVIEW),
              'boards':[{'path':str(board.resolve().relative_to(ROOT)),'sha256':sha(board)} for board in boards],
              'verifier_sha256':sha(Path(__file__)), 'cadquery_version':cq.__version__,
              'vtk_version':vtk.vtkVersion.GetVTKVersion(), 'numpy_version':np.__version__,
              'maximum_external_surface_deviation_mm':tolerance, 'models':[],
              'limits':['Sampled triangle-surface correspondence is a datum/orientation screen, not an exact Hausdorff proof.',
                        'STEP tessellation uses 0.02 mm linear and0.08 rad angular deflection; each direction samples up to2048 distinct vertices and1024 face centers.',
                        'Only STEP companions can change; WRL, model-node transforms, footprints, PCB copper and placements are preserved.',
                        'Agreement with existing WRL does not certify manufacturer accuracy, normalized land-pattern fit, unseen geometry or physical mating. ASPI remains a conservative illustrative envelope.',
                        'The exact BD8 capacitor retains internal WRL faces contained within the STEP solid; its outer STEP-to-WRL screen must still pass.']}
    for item in review['models']:
        wrl = MODELS/item['wrl']
        step = wrl.with_suffix('.step')
        require(sha(wrl)==item['reviewed_wrl_sha256'], 'WRL changed since datum review: '+wrl.name)
        before_sha = sha(step)
        vertices, faces = wrl_mesh(wrl)
        shape = cq.importers.importStep(str(step)).val()
        before_bounds, before_volume = shape_bounds(shape), shape.Volume()
        delta = item.get('reviewed_translation_mm')
        apply = bool(normalize and delta and before_sha==item.get('original_step_sha256'))
        if apply:
            candidate = shape.translate(tuple(delta))
        else:
            candidate = shape
        metrics = surface_check(candidate, vertices, faces, tolerance, item.get('allow_internal_wrl_faces',False))
        require(abs(candidate.Volume()-before_volume) <= max(1e-6,abs(before_volume)*1e-8), 'Translation changed volume: '+step.name)
        if apply:
            backup = ROOT/'tmp/model-audit/originals'/step.name
            backup.parent.mkdir(parents=True,exist_ok=True)
            if backup.exists():require(sha(backup)==before_sha, 'Original backup differs: '+step.name)
            else:backup.write_bytes(step.read_bytes())
            temporary = step.with_suffix('.datum-review.step')
            try:
                cq.exporters.export(candidate,str(temporary))
                temporary.write_text('\n'.join(line.rstrip() for line in temporary.read_text().splitlines())+'\n')
                restored = cq.importers.importStep(str(temporary)).val()
                require(abs(restored.Volume()-before_volume) <= max(1e-6,abs(before_volume)*1e-8), 'Serialized STEP volume changed')
                require(np.max(np.abs(np.array(shape_bounds(restored))-np.array(shape_bounds(candidate))))<.0001,
                        'Serialized STEP bounds changed')
                require(sha(step)==before_sha, 'STEP changed concurrently: '+step.name)
                temporary.replace(step)
            finally:
                if temporary.exists():temporary.unlink()
        result = {'wrl':wrl.name, 'step':step.name, 'uses_at_review':item['uses_at_review'],
                  'wrl_sha256':sha(wrl), 'step_sha256':sha(step), 'input_step_sha256':before_sha,
                  'original_step_sha256':item.get('original_step_sha256'),
                  'reviewed_translation_mm':delta, 'translation_applied_this_run':apply,
                  'before_bounds_mm':before_bounds, 'after_bounds_mm':shape_bounds(candidate),
                  'volume_before_mm3':before_volume, 'volume_after_mm3':candidate.Volume(),
                  'surface_screen':metrics, 'status':'PASS'}
        if 'normalization_owner' in item:result['normalization_owner']=item['normalization_owner']
        report['models'].append(result)
        print(step.name+': PASS'+(' (translated)' if apply else ''),flush=True)
    report['model_pairs_checked']=len(report['models'])
    report['step_translations_applied_this_run']=sum(r['translation_applied_this_run'] for r in report['models'])
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normalize-reviewed',action='store_true')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--board-b',type=Path,help='Board B candidate whose complete model set is checked; Board P uses its active project')
    args=parser.parse_args()
    result=run(args.normalize_reviewed,args.board_b)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'model_pairs_checked':result['model_pairs_checked'],
                      'step_translations_applied_this_run':result['step_translations_applied_this_run']}))


if __name__=='__main__':main()
