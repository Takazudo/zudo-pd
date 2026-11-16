#!/usr/bin/env python3
"""Derive G020 CAD from the supplier's taller SS-12D01-GX family solid.

Requires Python 3.12+, cadquery-ocp==7.9.3.1.1.
Only the actuator above housing+2 mm is removed. There is no geometry scaling.
"""
from pathlib import Path
import hashlib
import json
import re

from OCP.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / 'SW-TH_SS-12D01-GX.step'
TARGET = ROOT / 'footprints/kicad/zudo-led-lamp.3dshapes/SW-TH_SS-12D01-G020'
EXPECTED_SOURCE = 'f6c8743b8d28de4a7cbed027ee66539c66e565d853dd9f9d756137ad410e2356'
CASE_TOP = 3.5
ACTUATOR = 2.0
SEATING_OFFSET = .5  # Match supplier WRL's approximately +0.4963 mm seating frame.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(shape):
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    return list(box.Get())


def read_step(path):
    reader = STEPControl_Reader()
    assert reader.ReadFile(str(path)) == IFSelect_RetDone
    reader.TransferRoots()
    return reader.OneShape()


def solids(shape):
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


def volume(shape):
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, properties)
    return properties.Mass()


def cut(a, b):
    result = BRepAlgoAPI_Cut(a, b)
    assert result.IsDone()
    return result.Shape()


def common(a, b):
    result = BRepAlgoAPI_Common(a, b)
    assert result.IsDone()
    return result.Shape()


def box(z, height=30):
    return BRepPrimAPI_MakeBox(gp_Pnt(-15, -15, z), 30, 30, height).Shape()


def mesh(shape):
    tessellation = BRepMesh_IncrementalMesh(shape, .005, False, .1, False)
    assert tessellation.IsDone()
    vertices, triangles = [], []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, location)
        assert triangulation is not None
        offset = len(vertices)
        for index in range(1, triangulation.NbNodes()+1):
            point = triangulation.Node(index).Transformed(location.Transformation())
            vertices.append((point.X(), point.Y(), point.Z()))
        for index in range(1, triangulation.NbTriangles()+1):
            a, b, c = triangulation.Triangle(index).Get()
            if face.Orientation() == TopAbs_REVERSED:
                b, c = c, b
            triangles.append((offset+a-1, offset+b-1, offset+c-1))
        explorer.Next()
    return vertices, triangles


def near(a, b, tol=1e-5):
    return len(a) == len(b) and all(abs(x-y) < tol for x, y in zip(a, b))


def main():
    assert sha(SOURCE) == EXPECTED_SOURCE, 'Re-audit changed supplier source'
    source = read_step(SOURCE)
    assert BRepCheck_Analyzer(source).IsValid() and solids(source) == 1
    assert near(bounds(source), [-4.4, -1.95, -4.8, 4.4, 1.95, 7.5])
    pin_region = common(source, box(-6, 5))
    explorer = TopExp_Explorer(pin_region, TopAbs_SOLID)
    terminal_bounds = []
    while explorer.More():
        terminal_bounds.append(bounds(explorer.Current()))
        explorer.Next()
    terminal_bounds.sort()
    assert len(terminal_bounds) == 3
    for actual, x in zip(terminal_bounds, [-2.5, 0, 2.5]):
        assert near(actual, [x-.25, -.15, -4.8, x+.25, .15, -1]), actual
    # The exact source has housing top at 3.5 mm; only the actuator rises above it.
    upper = box(CASE_TOP)
    upper_bounds = bounds(common(source, upper))
    assert near(upper_bounds, [-1.75, -.75, 3.5, -.25, .75, 7.5]), upper_bounds
    cut_z = CASE_TOP + ACTUATOR
    cutter = box(cut_z)
    shortened = cut(source, cutter)
    assert BRepCheck_Analyzer(shortened).IsValid() and solids(shortened) == 1
    assert near(bounds(shortened), [-4.4, -1.95, -4.8, 4.4, 1.95, cut_z])
    # Boolean volume checks prove no housing, terminal or actuator geometry below the cut changed.
    below = box(-15, cut_z+15)
    expected = common(source, below)
    assert volume(cut(expected, shortened)) < 1e-7
    assert volume(cut(shortened, expected)) < 1e-7
    translation = gp_Trsf()
    translation.SetTranslation(gp_Vec(0, 0, SEATING_OFFSET))
    model = BRepBuilderAPI_Transform(shortened, translation, True).Shape()
    assert near(bounds(model), [-4.4, -1.95, -4.3, 4.4, 1.95, 6.0])
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    step = TARGET.with_suffix('.step')
    writer = STEPControl_Writer()
    assert writer.Transfer(model, STEPControl_AsIs) == IFSelect_RetDone
    assert writer.Write(str(step)) == IFSelect_RetDone
    # Fixed header date makes repeated exports deterministic; this does not alter STEP geometry.
    text = step.read_text()
    text = re.sub(r"'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d'", "'2026-09-06T00:00:00'", text, count=1)
    step.write_text(text)
    reloaded = read_step(step)
    assert BRepCheck_Analyzer(reloaded).IsValid() and solids(reloaded) == 1
    assert near(bounds(reloaded), bounds(model))
    assert abs(volume(reloaded)-volume(model)) < 1e-6
    # Mesh the same exported BRep. KiCad WRL coordinates are 0.1 inch units, hence /2.54.
    vertices, triangles = mesh(reloaded)
    lines = ['#VRML V2.0 utf8',
             '# Project-derived G020: supplier family solid, 2 mm actuator, +0.5 mm seating offset.',
             '# Neutral gray; STEP mm coordinates divided by 2.54 for KiCad WRL units.',
             'Shape { appearance Appearance { material Material { diffuseColor 0.48 0.49 0.50 } }',
             'geometry IndexedFaceSet { ccw TRUE solid FALSE creaseAngle 0.5',
             'coord Coordinate { point [']
    lines.extend(f'{v[0]/2.54:.9f} {v[1]/2.54:.9f} {v[2]/2.54:.9f},' for v in vertices)
    lines.append('] } coordIndex [')
    lines.extend(f'{a},{b},{c},-1,' for a, b, c in triangles)
    lines.extend(['] } }', ''])
    wrl = TARGET.with_suffix('.wrl')
    wrl.write_text('\n'.join(lines))
    assert near([min(v[0] for v in vertices), min(v[1] for v in vertices), min(v[2] for v in vertices),
                 max(v[0] for v in vertices), max(v[1] for v in vertices), max(v[2] for v in vertices)],
                bounds(reloaded), .006)
    report = {
        'source_sha256': sha(SOURCE), 'source_bounds_mm': bounds(source),
        'source_volume_mm3': volume(source), 'terminal_bounds_in_source_mm': terminal_bounds, 'actuator_projection_mm': ACTUATOR,
        'source_actuator_only_bounds_mm': upper_bounds,
        'cut_plane_in_source_mm': cut_z, 'seating_translation_z_mm': SEATING_OFFSET,
        'derived_bounds_mm': bounds(reloaded), 'derived_volume_mm3': volume(reloaded),
        'unchanged_below_cut': True, 'valid_solid_count': solids(reloaded),
        'vertices': len(vertices), 'triangles': len(triangles),
        'step_sha256': sha(step), 'wrl_sha256': sha(wrl),
    }
    (HERE / 'model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
