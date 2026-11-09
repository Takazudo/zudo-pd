"""Drawing-based PROJECT envelopes for two known body-model omissions only."""
import hashlib
import json
import math
from pathlib import Path
import sys
import cadquery as cq

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all
DATA = Path(__file__).with_name('supplemental-envelopes.json')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


def make_envelope(entry, footprint, native, native_origin, sources):
    props = {atom(p[1]): atom(p[2]) for p in find_all(footprint, 'property')}
    require(all(props.get(k) == entry[k] for k in ('Reference', 'Value', 'LCSC')), 'Supplemental component identity changed')
    require(atom(footprint[1]) == entry['footprint'], 'Supplemental footprint identity changed')
    require(atom(find_all(footprint, 'layer')[0][1]) == 'F.Cu', 'Supplemental screen requires reviewed F.Cu placement')
    attrs = [atom(v) for node in find_all(footprint, 'attr') for v in node[1:]]
    require('dnp' not in attrs, 'Supplemental component unexpectedly DNP')
    models = find_all(footprint, 'model')
    require(len(models) == 1 and Path(atom(models[0][1])).name == entry['model'], 'Supplemental model association changed')
    for key, expected in [('offset', [0., 0., 0.]), ('rotate', [0., 0., 0.]), ('scale', [1., 1., 1.])]:
        actual = [float(atom(v)) for v in find_all(find_all(models[0], key)[0], 'xyz')[0][1:]]
        require(actual == expected, 'Unreviewed supplemental model transform: ' + key)
    for path, expected in entry['model_sha256'].items():
        require(sources.get(path) == expected, 'Supplemental model bytes changed: ' + path)
    at = [float(atom(v)) for v in find_all(footprint, 'at')[0][1:]]
    angle = at[2] if len(at) > 2 else 0.
    require(abs(angle / 90 - round(angle / 90)) < 1e-8, 'Supplemental placement must be orthogonal')
    require(len(native_origin)==3 and all(math.isfinite(v) for v in native_origin), 'Invalid native component origin')
    require(math.dist(native_origin[:2], [at[0],-at[1]]) < .003, 'Native component origin differs from footprint')
    body = entry['body_mm']; size = entry['project_envelope_mm']
    require(all(math.isfinite(v) and v > 0 for v in body + size) and all(a >= b for a, b in zip(size, body)), 'Invalid supplemental dimensions')
    expected = cq.Workplane('XY').box(*body, centered=(True, True, False)).val().rotate((0,0,0),(0,0,1),angle).translate(tuple(native_origin))
    require(len(native.Solids()) == 1 and abs(native.Volume()-math.prod(body)) < 1e-5, 'Native body volume differs from reviewed box')
    require(max(abs(a-b) for a,b in zip(bounds(native),bounds(expected))) < .003, 'Native body axis/dimension/datum differs from footprint')
    return cq.Workplane('XY').box(*size, centered=(True, True, False)).val().rotate((0,0,0),(0,0,1),angle).translate(tuple(native_origin))


def screen(tree, native_parts, native_origins, sources, opposite_core, opposite_parts, contract, place):
    data = json.loads(DATA.read_text())
    require([e['Reference'] for e in data['envelopes']] == ['U2','U3'], 'Supplemental coverage changed')
    require([e['project_envelope_mm'] for e in data['envelopes']] == [[6.6,6.9,1.2],[3.55,3.,1.45]], 'Unreviewed PROJECT envelope dimensions')
    tolerance = contract['pd_stack']['collision_policy']['maximum_unintended_intersection_mm3']
    require(tolerance == .005, 'Unreviewed supplemental intersection policy')
    opposite = {'substrate': opposite_core, **opposite_parts}; results=[]; failures=[]
    for entry in data['envelopes']:
        ref=entry['Reference']
        footprints=[f for f in find_all(tree,'footprint') if any(atom(p[1])=='Reference' and atom(p[2])==ref for p in find_all(f,'property'))]
        require(len(footprints)==1 and ref in native_parts and ref in native_origins, 'Missing/duplicate supplemental component '+ref)
        local=make_envelope(entry,footprints[0],native_parts[ref],native_origins[ref],sources)
        world=place(local,contract)
        b=bounds(local); expected=[-b[4]-.5,-b[3]-12,11.1-b[5],-b[1]-.5,-b[0]-12,11.1-b[2]]
        require(max(abs(a-b) for a,b in zip(bounds(world),expected)) < .003, 'Supplemental face-to-face mapping changed')
        pairs=[]
        for other,shape in opposite.items():
            clearance=world.distance(shape)
            volume=world.intersect(shape).Volume() if clearance < 1e-7 else 0.
            require(math.isfinite(clearance) and clearance >= 0 and math.isfinite(volume) and volume >= 0, 'Invalid native clearance/intersection result')
            pairs.append({'opposite_ref':other,'clearance_mm':clearance,'intersection_mm3':volume})
            if volume>tolerance: failures.append({'board_p_ref':ref,**pairs[-1]})
        results.append({'reference':ref,'project_envelope_mm':entry['project_envelope_mm'],'native_origin_mm':native_origins[ref],'native_body_bounds_mm':bounds(native_parts[ref]),'project_envelope_bounds_mm':bounds(world),'closest_pair':min(pairs,key=lambda row:row['clearance_mm']),'pairs':pairs,'basis':entry['basis'],'source':entry['source']})
    return {'status':'FAIL' if failures else 'PASS','classification':data['classification'],'scope':'Only drawing-based PROJECT U2/U3 envelopes against actual opposite-board substrate and fitted solids; existing body assets unchanged','data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),'maximum_unintended_intersection_mm3':tolerance,'results':results,'failures':failures,'limits':data['limits']}
