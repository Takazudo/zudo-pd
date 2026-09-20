#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "trimesh==4.8.3", "matplotlib==3.10.6", "networkx==3.5"]
# ///
"""Build the zudo-pd underside Faston guard from its shared PCB contract.

CAD/world: PCB X, negative PCB Y, Z up; PCB top=0, bottom=-1.6 mm.
Print STLs are separate parts placed on Z=0. STEP/WRL assembly assets keep
world coordinates. The generated guard is a fit prototype, not strain relief.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import sys
import zipfile

import cadquery as cq
import numpy as np
import trimesh
import vtk

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / 'pcb-contract.json'
OUT = HERE / 'generated'
FASTON_STEP = ROOT / 'footprints/kicad/zudo-pd.3dshapes/CONN-TH_63951-1.step'
FASTON_WRL = FASTON_STEP.with_suffix('.wrl')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(x0, y0, x1, y1, z0, z1):
    """Box specified using PCB XY and world Z bounds."""
    return cq.Workplane('XY').box(x1-x0, y1-y0, z1-z0).translate(((x0+x1)/2, -(y0+y1)/2, (z0+z1)/2)).val()


def cylinder(x, y, diameter, z0, z1):
    return cq.Workplane('XY').center(x, -y).circle(diameter/2).extrude(z1-z0).translate((0,0,z0)).val()


def notch_profile(notch):
    edges = notch['edge_path_top_to_bottom']
    start = edges[0]['start']
    wire = cq.Workplane('XY').moveTo(start[0], -start[1])
    for edge in edges:
        end = edge['end']
        if edge['type'] == 'line':
            wire = wire.lineTo(end[0], -end[1])
        else:
            mid = edge['mid']
            wire = wire.threePointArc((mid[0],-mid[1]), (end[0],-end[1]))
    return wire.close()


def key(notch, clearance, z0, z1):
    return notch_profile(notch).offset2D(-clearance).extrude(z1-z0).translate((0,0,z0)).val()


def mesh(shape):
    vertices, faces = shape.tessellate(.035, .12)
    return trimesh.Trimesh(np.array([v.toTuple() for v in vertices]), np.array(faces), process=True)


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]


def overlaps(a,b):
    aa,bb=bounds(a),bounds(b)
    return all(aa[i]<bb[i+3]-.0001 and aa[i+3]>bb[i]+.0001 for i in range(3))


def make_guard(c, socket_diameter):
    g=c['guard'];x0,y0,x1,y1=g['outer_xy_mm'];w=g['wall_mm']
    low,inside,top=g['outer_floor_z_mm'],g['inner_floor_z_mm'],g['wall_top_z_mm']
    body=box(x0,y0,x1,y1,low,inside)
    body=body.fuse(box(x0,y0,x0+w,y1,inside,top))
    for a,b in [(y0,y0+w),(y1-w,y1)]+[(n['center_y_mm']-w/2,n['center_y_mm']+w/2) for n in c['notch_geometry']['notches']]:
        body=body.fuse(box(x0,a,x1,b,inside,top))
    # Narrow floor vents avoid the centerline of each blade. They provide
    # ventilation, not a thermal rating or an ingress-protection claim.
    for fp in c['fastons']['placements']:
        y=fp['center_mm'][1]
        for delta in [-2.8,2.8]:
            body=body.cut(box(10,y+delta-.6,28,y+delta+.6,low-.1,inside+.1))
    for groove in g['exit_shutter']['grooves']:
        body=body.cut(box(groove['x_mm'][0],groove['y_mm'][0],groove['x_mm'][1],groove['y_mm'][1],*groove['z_mm']))
    caps=[]
    for n in c['notch_geometry']['notches']:
        y=n['center_y_mm']
        # 45-degree gussets support the wider T head without a long bridge.
        ramp=(cq.Workplane('XY').workplane(offset=-4.2).center(2,-y).rect(4,1.6)
              .workplane(offset=2).rect(4,5.6).loft(combine=True).val())
        body=body.fuse(ramp).fuse(key(n,c['notch_geometry']['key_clearance_mm'],-2.2,g['cap_bottom_z_mm']))
        z=g['cap_bottom_z_mm'];d=g['pin_diameter_mm'];h=g['pin_height_mm']
        pin=cylinder(2.2,y,d,z,z+h-.3)
        tip=(cq.Workplane('XY').workplane(offset=z+h-.3).center(2.2,-y).circle(d/2)
             .workplane(offset=.3).circle((d-.4)/2).loft(combine=True).val())
        body=body.fuse(pin).fuse(tip)
        cap=box(*[g['cap_x_bounds_mm'][0],y-g['cap_xy_half_y_mm'],g['cap_x_bounds_mm'][1],y+g['cap_xy_half_y_mm']],z,z+g['cap_thickness_mm'])
        cap=cq.Workplane(obj=cap).edges('|Z').fillet(.6).val()
        cap=cap.cut(cylinder(2.2,y,socket_diameter,z-.05,z+g['socket_depth_mm']))
        # Small lead-in guides the calibrated press fit; its retained overlap
        # with the peg is intentional and checked separately from collisions.
        lead=(cq.Workplane('XY').workplane(offset=z-.01).center(2.2,-y).circle((socket_diameter+.35)/2)
              .workplane(offset=.25).circle(socket_diameter/2).loft(combine=True).val())
        cap=cap.cut(lead)
        caps.append((f'cap-{int(y)}',cap))
    caps.append(('j8-exit-shutter',shutter(c)))
    return body.clean(),caps


def shutter(c, sweep=False):
    config=c['guard']['exit_shutter'];result=None
    for part in config['parts']:
        x1=part['x_mm'][1]+(config['insertion_distance_mm'] if sweep else 0)
        solid=box(part['x_mm'][0],part['y_mm'][0],x1,part['y_mm'][1],*part['z_mm'])
        result=solid if result is None else result.fuse(solid)
    return result.clean()


def theoretical_board(c):
    width,height=c['world']['pcb_size_mm'];bottom=c['world']['pcb_bottom_z_mm']
    board=box(0,0,width,height,bottom,0)
    for n in c['notch_geometry']['notches']:
        cut=notch_profile(n).extrude(3).translate((0,0,-2)).val()
        board=board.cut(cut)
    # Exact solder-hole pattern is part of the terminal contract. Other holes
    # are omitted in this reference substrate, conservatively for collisions.
    for f in c['fastons']['placements']:
        x,y=f['center_mm']
        for dx in [-2.54,2.54]:
            board=board.cut(cylinder(x+dx,y,1.4,bottom-.5,.5))
    return board


def terminal_models(c):
    s=cq.importers.importStep(str(FASTON_STEP)).val()
    b=bounds(s)
    target=[-3.26,-.40505,-3.8,17.06,.40505,8.9]
    if any(abs(a-v)>.02 for a,v in zip(b,target)):
        raise ValueError('Faston STEP is not normalized to the reviewed WRL datum: '+str(b))
    result=[]
    # Reviewed model Z90 plus bottom footprint270 results in raw X -> PCB+X,
    # raw Y -> CAD-Y and raw Z -> -Z. This is a180-degree X rotation.
    rotated=s.rotate((0,0,0),(1,0,0),180)
    for f in c['fastons']['placements']:
        x,y=f['center_mm']
        result.append((f['reference'],rotated.translate((x,-y,c['world']['pcb_bottom_z_mm']))))
    return result


def clean_step(path):
    path=Path(path)
    path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')


def export_wrl(parts, destination):
    lines=['#VRML V2.0 utf8','# zudo-pd guard only. World XYZ in mm/2.54; CAD Y is already negative PCB Y.']
    for name,shape,color in parts:
        m=mesh(shape);v=m.vertices/2.54
        lines += ['Shape { appearance Appearance { material Material { diffuseColor '+' '.join(map(str,color))+' } } geometry IndexedFaceSet { ccw TRUE solid TRUE coord Coordinate { point [',
                  ',\n'.join(' '.join(f'{x:.8f}' for x in point) for point in v),
                  '] } coordIndex [',',\n'.join(','.join(str(x) for x in face)+',-1' for face in m.faces),'] } }']
    destination.write_text('\n'.join(lines)+'\n')


def render(parts, path, title, elev=-28, azim=-52, limits=None):
    # Native depth-buffer rendering avoids per-object painter-order artifacts.
    renderer=vtk.vtkRenderer();renderer.SetBackground(.94,.95,.97)
    all_points=[]
    for name,shape,color in parts:
        m=mesh(shape);all_points.append(m.vertices)
        points=vtk.vtkPoints()
        for point in m.vertices:points.InsertNextPoint(*point)
        cells=vtk.vtkCellArray()
        for face in m.faces:
            cells.InsertNextCell(3)
            for index in face:cells.InsertCellPoint(int(index))
        data=vtk.vtkPolyData();data.SetPoints(points);data.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(data);normals.SetFeatureAngle(35);normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetInterpolationToPhong();renderer.AddActor(actor)
    if limits is None:
        points=np.concatenate(all_points);lo=points.min(axis=0);hi=points.max(axis=0)
    else:lo,hi=np.array(limits[0]),np.array(limits[1])
    center=(hi+lo)/2;span=hi-lo;distance=np.linalg.norm(span)*2
    a,e=math.radians(azim),math.radians(elev)
    direction=np.array([math.cos(e)*math.cos(a),math.cos(e)*math.sin(a),math.sin(e)])
    camera=renderer.GetActiveCamera();camera.SetPosition(*(center+direction*distance));camera.SetFocalPoint(*center)
    camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();camera.SetParallelScale(np.linalg.norm(span)*.49)
    text=vtk.vtkTextActor();text.SetInput(title);text.SetDisplayPosition(30,1220)
    text.GetTextProperty().SetFontSize(27);text.GetTextProperty().SetColor(.12,.16,.20);renderer.AddActor2D(text)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1600,1280);window.SetMultiSamples(8);window.AddRenderer(renderer)
    renderer.ResetCameraClippingRange();window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()


def emit_print(name, shape, rotation=None):
    print_shape=shape if rotation is None else shape.rotate(*rotation)
    b=bounds(print_shape);print_shape=print_shape.translate((-b[0],-b[1],-b[2]))
    output=OUT/'stl'/f'{name}.stl';cq.exporters.export(print_shape,str(output),tolerance=.035,angularTolerance=.12)
    m=trimesh.load_mesh(output)
    if not(m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1):
        raise ValueError('Invalid/disconnected print mesh: '+name)
    if abs(m.bounds[0,2])>1e-5:
        raise ValueError('Print mesh does not rest on Z=0: '+name)
    return {'name':name,'file':str(output.relative_to(HERE)),'sha256':sha(output),
            'bounds_mm':m.bounds.tolist(),'volume_mm3':float(m.volume),
            'watertight':True,'connected_solids':1,'print_bottom_z_mm':float(m.bounds[0,2])}


def build(socket_diameter=None):
    c=json.loads(CONTRACT.read_text());g=c['guard']
    socket_diameter=g['socket_diameter_mm'] if socket_diameter is None else socket_diameter
    if not 2.5<=socket_diameter<=3.1:raise ValueError('Socket diameter outside coupon range')
    for folder in ['stl','preview']: (OUT/folder).mkdir(parents=True,exist_ok=True)
    guard,caps=make_guard(c,socket_diameter)
    printed=[('guard',guard,(.12,.32,.42))]+[(n,s,(.82,.56,.18)) for n,s in caps]
    board=theoretical_board(c);terminals=terminal_models(c)
    checks=[]
    for name,shape,_ in printed:
        if not shape.isValid() or len(shape.Solids())!=1:raise ValueError('Invalid CAD body: '+name)
        volume=shape.intersect(board).Volume()
        if volume>.001:raise ValueError(f'{name} intersects PCB substrate: {volume}')
        checks.append({'pair':[name,'contract PCB substrate'],'intersection_mm3':volume})
        for ref,metal in terminals:
            volume=shape.intersect(metal).Volume() if overlaps(shape,metal) else 0
            if volume>.001:raise ValueError(f'{name} intersects {ref}: {volume}')
            checks.append({'pair':[name,ref],'intersection_mm3':volume})
    fit=[]
    for name,cap in caps:
        if not name.startswith('cap-'):continue
        overlap=guard.intersect(cap).Volume()
        allowed=math.pi/4*max(0,g['pin_diameter_mm']**2-socket_diameter**2)*g['pin_height_mm']+.02
        if overlap>allowed:raise ValueError(f'Unexpected guard/cap collision: {name}: {overlap}')
        fit.append({'pair':['guard',name],'intentional_press_fit_intersection_mm3':overlap,
                    'diametral_interference_mm':g['pin_diameter_mm']-socket_diameter})
    # Incoming female housing design envelope excludes the PCB and the bare
    # terminal itself; only the printed guard must leave this corridor open.
    envelope=g['nominal_mating_envelope']
    for f in c['fastons']['placements']:
        y=f['center_mm'][1];half=envelope['each_row_y_half_mm']
        segments=envelope.get('row_overrides',{}).get(f['reference'],[{'x_mm':envelope['x_mm'],'z_mm':envelope['z_mm']}])
        for index,seg in enumerate(segments):
            bay=box(seg['x_mm'][0],y-half,seg['x_mm'][1],y+half,*seg['z_mm'])
            volume=guard.intersect(bay).Volume()
            if volume>.001:raise ValueError(f'Nominal housing bay blocked: {f["reference"]}: {volume}')
            checks.append({'pair':['guard',f['reference']+f' clear access segment{index+1}'],'intersection_mm3':volume})
    sweep=shutter(c,sweep=True)
    for name,solid in [('guard',guard),('PCB substrate',board),*terminals]:
        volume=sweep.intersect(solid).Volume() if overlaps(sweep,solid) else 0
        if volume>.001:raise ValueError(f'Shutter insertion blocked by {name}: {volume}')
        checks.append({'pair':['complete8mm shutter insertion sweep',name],'intersection_mm3':volume})
    wire=box(29.7,73-envelope['each_row_y_half_mm'],46,73+envelope['each_row_y_half_mm'],-11.8,-4.8)
    volume=sweep.intersect(wire).Volume()
    if volume>.001:raise ValueError('Shutter sweeps through declared crimp/wire envelope')
    checks.append({'pair':['complete8mm shutter insertion sweep','declared crimp/wire extension'],'intersection_mm3':volume})
    stop_volume=guard.intersect(shutter(c).translate((-.5,0,0))).Volume()
    if stop_volume<.01:raise ValueError('Shutter closed-end stop does not prevent inward overtravel')
    checks.append({'pair':['shutter0.5mm forbidden inward overtravel','positive stop'],'expected_stop_intersection_mm3':stop_volume})
    entries=[emit_print('guard',guard)]
    for name,cap in caps:
        # Closed cap face down: the blind socket opens upward during printing.
        entries.append(emit_print(name,cap,((0,0,0),(1,0,0),180)))
    # Independent calibration pieces keep trial prints small.
    coupon_peg=box(0,0,8,8,0,2).fuse(cylinder(4,4,g['pin_diameter_mm'],2,2.9))
    peg_tip=(cq.Workplane('XY').workplane(offset=2.9).center(4,-4).circle(g['pin_diameter_mm']/2)
             .workplane(offset=.3).circle((g['pin_diameter_mm']-.4)/2).loft(combine=True).val())
    coupon_peg=coupon_peg.fuse(peg_tip)
    entries.append(emit_print('coupon-peg-2.8',coupon_peg))
    for d in [2.6,2.7,2.8,2.9,3.0]:
        coupon=box(0,0,8,8,0,2).cut(cylinder(4,4,d,2-g['socket_depth_mm'],2.1))
        lead=(cq.Workplane('XY').workplane(offset=1.75).center(4,-4).circle(d/2)
              .workplane(offset=.26).circle((d+.35)/2).loft(combine=True).val())
        coupon=coupon.cut(lead)
        entries.append(emit_print(f'coupon-socket-{d:.1f}',coupon))
    first=c['notch_geometry']['notches'][0]
    for gap in [.2,.3,.4]:
        coupon=key(first,gap,0,2).fuse(box(0,first['center_y_mm']-1,1.5,first['center_y_mm']+1,-1,0))
        entries.append(emit_print(f'coupon-t-key-{gap:.1f}',coupon))
    rail_coupon=box(30,66.2,36,79,-5.4,-4.8)
    for y0,y1 in [(66.2,67.8),(77.4,79)]:rail_coupon=rail_coupon.fuse(box(30,y0,36,y1,-4.8,-2.4))
    for groove in g['exit_shutter']['grooves']:
        rail_coupon=rail_coupon.cut(box(groove['x_mm'][0],groove['y_mm'][0],groove['x_mm'][1],groove['y_mm'][1],*groove['z_mm']))
    entries.append(emit_print('coupon-shutter-grooves',rail_coupon))
    assembly=cq.Assembly(name='zudo_pd_faston_guard')
    for name,shape,color in printed:assembly.add(shape,name=name,color=cq.Color(*color))
    assembly.export(str(OUT/'faston-cover.step'));clean_step(OUT/'faston-cover.step')
    export_wrl(printed,OUT/'faston-cover.wrl')
    cq.exporters.export(board,str(OUT/'preview/pcb-substrate-reference.step'));clean_step(OUT/'preview/pcb-substrate-reference.step')
    overview=printed+[('PCB substrate',board,(.12,.42,.23))]+[(n,s,(.72,.73,.75)) for n,s in terminals]
    render(overview,OUT/'preview/assembled-underneath.png','Underside guard — inward-facing terminals')
    bay_board=board.intersect(box(0,31,40,79,-1.6,0))
    bays=printed+[('PCB roof',bay_board,(.12,.42,.23))]+[(n,s,(.72,.73,.75)) for n,s in terminals]
    render(bays,OUT/'preview/mating-bays.png','Four isolated bays — viewed from the inward cable side',elev=-3,azim=5)
    render(printed,OUT/'preview/guard-and-caps.png','Guard and press-fit caps — assembly coordinates',elev=26,azim=-48)
    exploded=[('guard',guard,(.12,.32,.42))]+[(n,s.translate((0,0,7)),(.82,.56,.18)) for n,s in caps]
    exploded += [('PCB substrate',board,(.12,.42,.23))]+[(n,s,(.72,.73,.75)) for n,s in terminals]
    render(exploded,OUT/'preview/exploded.png','T-keys insert from below; caps press on from above',elev=23,azim=-58)
    manifest={'schema_version':1,'revision':c['revision'],'status':'FIT PROTOTYPE — physical fit, retention and temperature unmeasured',
              'world':c['world'],'config':{'socket_diameter_mm':socket_diameter,'contract':c['guard']},
              'source_sha256':{'generate.py':sha(__file__),'pcb-contract.json':sha(CONTRACT),
                               str(FASTON_STEP.relative_to(ROOT)):sha(FASTON_STEP),str(FASTON_WRL.relative_to(ROOT)):sha(FASTON_WRL)},
              'parts':entries,'assembly_files':{n:sha(OUT/n) for n in ['faston-cover.step','faston-cover.wrl']},
              'nominal_geometry_checks':checks,'intentional_fits':fit,
              'assembled_bounds_mm':{name:bounds(shape) for name,shape,_ in printed},
              'pcb_instance_check':'PENDING — run verify.py against the final matching PCB',
              'limitations':['Exact female receptacle and insulating sleeve are not selected; nominal open bay is an envelope, not proven mating compatibility.',
                             'Cap retention depends on printer/material and coupon-selected interference; no rated cable strain relief.',
                             'Cover changes convection near the power stage; repeat thermal qualification with it installed.',
                             'The PCB reference in previews is generated from the contract; full populated-board collisions require final PCB verification.']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(OUT/'print-parts.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for e in entries:archive.write(HERE/e['file'],Path(e['file']).name)
        archive.write(CONTRACT,'pcb-contract.json')
        archive.write(OUT/'manifest.json','manifest.json')
        if (HERE/'README.md').exists():archive.write(HERE/'README.md','README.md')
    print(json.dumps({'status':'PASS','print_parts':len(entries),'intersection_checks':len(checks),
                      'output':str(OUT),'physical_fit':'NOT MEASURED'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket-diameter',type=float)
    args=parser.parse_args();build(args.socket_diameter)
