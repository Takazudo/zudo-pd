#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "trimesh==4.8.3", "networkx==3.5"]
# ///
"""Independently check emitted leg geometry, source aperture and installed fit.

Never imports the leg generator or modifies PCB/model/print source assets.
Collision calculations use the Board B CAD frame. Export/render use gravity
orientation: floor Z0, nominal PCB front Z18, nominal PCB back Z19.6.
"""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
import vtk
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'generated'
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load
helper_path=ROOT/'scripts/pcb/export-assembly-preview.py'
modspec=importlib.util.spec_from_file_location('assembly_geometry',helper_path)
helper=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(helper)

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bounds(shape):return helper.bounds(shape)
def overlap(a,b):return all(a[k]<b[k+3]-1e-7 and a[k+3]>b[k]+1e-7 for k in range(3))
def box_distance(a,b):return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
def tessellate(shape,tolerance=.005,angular=.04):
    v,f=shape.tessellate(tolerance,angular)
    return trimesh.Trimesh(np.array([p.toTuple() for p in v]),np.array(f),process=True)

def plane_loops(mesh,z):
    edges=set();coords={}
    for triangle in mesh.triangles:
        dz=triangle[:,2]-z
        if dz.min()>1e-9 or dz.max() < -1e-9:continue
        hits=[]
        for a,b,da,db in zip(triangle,np.roll(triangle,-1,axis=0),dz,np.roll(dz,-1)):
            if abs(da)<1e-9:hits.append(a[:2])
            if da*db < -1e-18:hits.append((a+(b-a)*(-da/(db-da)))[:2])
        distinct=[]
        for q in hits:
            if not any(np.linalg.norm(q-r)<1e-7 for r in distinct):distinct.append(q)
        if len(distinct)==2:
            keys=[tuple(np.round(q,6)) for q in distinct]
            if keys[0]!=keys[1]:
                edges.add(tuple(sorted(keys)))
                for k,q in zip(keys,distinct):coords[k]=q
    adjacency={}
    for a,b in edges:adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
    assert adjacency and all(len(v)==2 for v in adjacency.values()),(z,'open/nonmanifold section')
    unseen=set(adjacency);loops=[]
    while unseen:
        start=min(unseen);order=[start];prev=None;cur=start
        while True:
            nxt=next(k for k in adjacency[cur] if k!=prev)
            if nxt==start:break
            assert nxt not in order
            order.append(nxt);prev,cur=cur,nxt
        unseen-=set(order);loops.append(np.array([coords[k] for k in order]))
    return sorted(loops,key=area,reverse=True)

def area(v):
    b=np.roll(v,-1,axis=0);return abs(np.sum(v[:,0]*b[:,1]-b[:,0]*v[:,1]))/2

def point_dist(q,poly):
    a=poly;b=np.roll(poly,-1,axis=0);d=b-a;t=np.sum((q-a)*d,axis=1)/np.sum(d*d,axis=1);t=np.clip(t,0,1);return np.sqrt(np.sum((a+t[:,None]*d-q)**2,axis=1)).min()

def samples(poly):
    return np.concatenate([poly, .5*(poly+np.roll(poly,-1,axis=0))])

def deviation(a,b):return max(float(point_dist(q,b)) for q in samples(a))

def simplified(v,tolerance=1e-6):
    v=list(v);changed=True
    while changed and len(v)>3:
        changed=False
        for i in range(len(v)):
            a=np.array(v[i-1]);b=np.array(v[i]);c=np.array(v[(i+1)%len(v)]);d=c-a
            if np.linalg.norm(d)>0 and abs(d[0]*(b-a)[1]-d[1]*(b-a)[0])/np.linalg.norm(d)<tolerance and np.dot(b-a,b-c)<=tolerance:
                del v[i];changed=True;break
    return np.array(v)

def measure_mesh(mesh,profile):
    results=[]
    for z in [1,7.9,8.1,9,12,13.4,13.6,14,16,17.5,17.999]:
        loops=plane_loops(mesh,z);r={'z_mm':z,'loop_count':len(loops)}
        if z<8:
            assert len(loops)==1,'Unexpected opening below blind floor';r['closed_bore_floor']=True
        elif z<13.5:
            assert len(loops)==2
            q=loops[1];radius=np.linalg.norm(q,axis=1);r.update(inner_bounds_mm=[q.min(0).tolist(),q.max(0).tolist()],radius_mm=[float(radius.min()),float(radius.max())],area_mm2=area(q));assert abs(radius.min()-1.7)<.012 and abs(radius.max()-1.7)<.012
        else:
            assert len(loops)==2;q=loops[1];simple=simplified(q);forward=deviation(q,profile);back=deviation(profile,q);r.update(inner_vertices_after_collinear_reduction=len(simple),inner_bounds_mm=[q.min(0).tolist(),q.max(0).tolist()],area_mm2=area(q),profile_to_section_max_sampled_mm=back,section_to_profile_max_sampled_mm=forward);assert max(forward,back)<2e-6
        results.append(r)
    return results


def exact_polygon(actual,expected,tolerance=2e-6):
    q=simplified(actual);expected=np.asarray(expected)
    require(len(q)==len(expected),'Grip vertex count changed')
    distances=np.linalg.norm(q[:,None,:]-expected[None,:,:],axis=2);indices=distances.argmin(axis=1)
    error=float(distances.min(axis=1).max());steps=(np.roll(indices,-1)-indices)%len(q)
    require(len(set(indices))==len(q) and (np.all(steps==1) or np.all(steps==len(q)-1)),
            'Grip vertices no longer follow the exact source polygon')
    require(error<tolerance,'Grip profile differs from source: '+str(error))
    return error


def mesh_checks(stl,four,leg,spec,reference,source_path):
    profile=np.array(reference['selected_profile']['centered_vertices_xy_mm'])
    original=np.array(reference['selected_profile']['source_vertices_xy_mm'])
    center=np.array(reference['selected_profile']['original_bbox_center_xy_mm'])
    require(np.max(np.abs(original-center-profile))<1e-12,'Recorded source translation changed')
    require(len(profile)==27 and spec['screw_bore']['gripping_depth_mm']==4.5,
            'The exact27-vertex/4.5mm proven gripping section must be retained')
    source_review={'status':'NOT REOPENED','basename':reference['source_basename'],'sha256':reference['source_sha256']}
    if source_path:
        require(sha(source_path)==reference['source_sha256'],'Supplied original STL hash differs')
        source_mesh=trimesh.load_mesh(source_path,process=True)
        require(source_mesh.is_watertight,'Original source STL is not watertight')
        holes=[v for v in plane_loops(source_mesh,2.25) if np.ptp(v[:,0])<10]
        holes.sort(key=lambda v:float((v[:,0].min()+v[:,0].max())/2))
        require(len(holes)==30,'Source STL hole count changed')
        selected=holes[reference['selected_profile']['source_hole_index_left_to_right']-1]
        error=exact_polygon(selected-center,profile)
        source_review.update(status='PASS',source_hole_count=30,selected_hole=12,
                             translated_source_vertex_max_error_mm=error,source_file_reopened=True)
    mesh=trimesh.load_mesh(stl,process=True);plate=trimesh.load_mesh(four,process=True)
    require(mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,'Main STL must be one watertight solid')
    require(plate.is_watertight and plate.is_winding_consistent and len(plate.split())==4,'Four-up STL must have four watertight solids')
    require(np.max(np.abs(mesh.bounds-np.array([[-7,-7,0],[7,7,18]])))<1e-5,'Print bounds differ from the18mm/14mm contract')
    require(abs(float(mesh.volume)-leg.Volume())/leg.Volume()<.001,'STEP/STL volumes differ beyond tessellation allowance')
    sections=measure_mesh(mesh,profile);step_sections=measure_mesh(tessellate(leg),profile)
    exact_sections=[]
    for tag,m in [('STL',mesh),('STEP tessellation',tessellate(leg))]:
        for z in (14,16,17.9,17.999):
            loops=plane_loops(m,z);require(len(loops)==2,'Expected outer wall and bore boundary')
            exact_sections.append({'format':tag,'z_mm':z,'ordered_vertex_max_error_mm':exact_polygon(loops[1],profile)})
        relief=plane_loops(m,10);require(len(relief)==2,'Missing lower tip pocket')
        radii=np.linalg.norm(relief[1],axis=1);require(np.max(np.abs(radii-1.7))<.002,'Tip pocket is notØ3.4mm')
        require(len(plane_loops(m,7))==1,'Blind floor is open belowZ8')
    four_checks=[]
    for part in plate.split():
        xy=(part.bounds[0,:2]+part.bounds[1,:2])/2
        require(min(np.linalg.norm(xy-v) for v in [(0,0),(19,0),(0,19),(19,19)])<1e-5,'Unexpected four-up placement')
        require(abs(float(part.volume)-float(mesh.volume))/float(mesh.volume)<1e-5,'Four-up component differs from main STL')
        q=plane_loops(part,16)[1]-xy
        four_checks.append({'center_xy_mm':xy.tolist(),'profile_error_mm':exact_polygon(q,profile)})
    return {'status':'PASS','original_reference':source_review,'main_stl_watertight':True,'four_up_watertight_solids':4,
            'stl_sections':sections,'step_sections':step_sections,'exact_grip_sections':exact_sections,
            'four_up_profile_checks':four_checks,'cad_volume_mm3':leg.Volume(),'stl_volume_mm3':float(mesh.volume),
            'profile_tolerance_mm':2e-6,'grip_assumption':'The user-proven untapped aperture is retained exactly; lower tip relief/blind floor are explicit new geometry.'}


def render(parts,destination):
    renderer=vtk.vtkRenderer();renderer.SetBackground(.94,.95,.97);all_bounds=[]
    for name,shape,color in parts:
        vertices,faces=shape.tessellate(.12,.3);points=vtk.vtkPoints();cells=vtk.vtkCellArray()
        for v in vertices:points.InsertNextPoint(*v.toTuple())
        for face in faces:
            cells.InsertNextCell(3)
            for index in face:cells.InsertCellPoint(int(index))
        data=vtk.vtkPolyData();data.SetPoints(points);data.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(data);normals.SetFeatureAngle(40);normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color);actor.GetProperty().SetInterpolationToPhong();renderer.AddActor(actor)
        all_bounds.append(bounds(shape))
    bb=np.array(all_bounds);lo=bb[:,:3].min(0);hi=bb[:,3:].max(0);center=(lo+hi)/2;span=hi-lo
    az,el=math.radians(-125),math.radians(16);direction=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    camera=renderer.GetActiveCamera();camera.SetPosition(*(center+direction*np.linalg.norm(span)*2));camera.SetFocalPoint(*center);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();camera.SetParallelScale(np.linalg.norm(span)*.46)
    title=vtk.vtkTextActor();title.SetInput('18 mm adhesive legs | PCB components face downward');title.SetDisplayPosition(24,1125);title.GetTextProperty().SetFontSize(23);title.GetTextProperty().SetColor(.12,.16,.20);renderer.AddActor2D(title)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1400,1180);window.SetMultiSamples(8);window.AddRenderer(renderer);renderer.ResetCameraClippingRange();window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(destination));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reference-stl',type=Path);args=parser.parse_args()
    spec_path=HERE/'spec.json';reference_path=HERE/'reference-bore.json';spec=json.loads(spec_path.read_text());reference=json.loads(reference_path.read_text())
    step=OUT/'adhesive-leg-18mm-m3.step';stl=OUT/'adhesive-leg-18mm-m3.stl';four=OUT/'adhesive-leg-18mm-m3-4x.stl'
    assembly_step=ROOT/spec['assembly']['populated_step'];assembly_report_path=ROOT/'boards/board-b/assembly-preview/verification.json';assembly_report=json.loads(assembly_report_path.read_text())
    require(sha(assembly_step)==spec['assembly']['populated_step_sha256']==assembly_report['artifact_sha256']['populated-stack.step'],'Populated assembly STEP changed')
    for board,digest in assembly_report['pcb_sha256'].items():require(sha(ROOT/'boards'/board/(board+'.kicad_pcb'))==digest,'Source PCB changed: '+board)
    for name,digest in assembly_report['model_sources_sha256'].items():require(sha(ROOT/name)==digest,'Source component model changed: '+name)
    tracked=[Path(__file__),HERE/'generate.py',spec_path,reference_path,step,stl,four,assembly_step,assembly_report_path,
             ROOT/'boards/board-b/mechanical.json',ROOT/'boards/board-b/board-b.kicad_pcb',ROOT/'boards/board-p/board-p.kicad_pcb',helper_path]
    before={str(p.relative_to(ROOT)):sha(p) for p in tracked}
    leg=cq.importers.importStep(str(step)).val();require(leg.isValid() and len(leg.Solids())==1,'Leg STEP must be one valid solid')
    require(np.max(np.abs(np.array(bounds(leg))-[-7,-7,0,7,7,18]))<.001,'Leg STEP dimensions differ')
    mesh_report=mesh_checks(stl,four,leg,spec,reference,args.reference_stl)
    print('Printed STEP/STL and exact source grip: PASS',flush=True)
    imported=helper.NativeAssembly.load(str(assembly_step));parts={c.name:c.toCompound() for c in imported.children}
    expected={'board_b_substrate','board_p_substrate'}
    for tag in ('b','p'):
        expected|={'board_'+tag+'_'+ref for ref in assembly_report['native_step_datums']['board-'+tag]['component_bounds_mm']}
    require(set(parts)==expected,'Native assembly component coverage changed')
    boxes={ref:bounds(shape) for ref,shape in parts.items()}
    max_native=max(v[5] for v in boxes.values());require(max_native<18,'Existing assembly reaches the proposed floor')
    # Verify actual current PCB hole diameters without changing the PCB.
    pcb=load(ROOT/spec['assembly']['board_b_pcb']);fps={helper.properties(f).get('Reference'):f for f in find_all(pcb,'footprint')}
    hole_checks=[];legs={};fit=[]
    for ref,(x,y) in spec['assembly']['corner_centers_pcb_mm'].items():
        pads=find_all(fps[ref],'pad');require(len(pads)==1 and atom(pads[0][2])=='np_thru_hole','Expected independent NPTH: '+ref)
        drill=float(atom(find_all(pads[0],'drill')[0][1]));require(drill==3,'PCB support hole changed')
        at=[float(atom(v)) for v in find_all(fps[ref],'at')[0][1:3]];require(at==[x,y],'Support centre changed')
        hole_checks.append({'reference':ref,'hole_nominal_mm':drill,'screw_nominal_mm':3,'diametral_clearance_mm':0,
                            'free_pass_qualification':'NOT ESTABLISHED; actual M3 passage must be checked. This does not fail print CAD or enlarge the PCB.'})
        installed=leg.rotate((0,0,0),(1,0,0),180).translate((x,-y,18));legs[ref]=installed;lb=bounds(installed);collisions=[];checked=0
        for name,part in parts.items():
            if not overlap(lb,boxes[name]):continue
            volume=installed.intersect(part).Volume();checked+=1
            if volume>.005:collisions.append({'component':name,'intersection_mm3':volume})
        require(not collisions,ref+': populated assembly collision '+str(collisions))
        closest=None
        for name in sorted((n for n in parts if n!='board_b_substrate'),key=lambda n:box_distance(lb,boxes[n])):
            if closest and box_distance(lb,boxes[name])>closest['distance_mm']:break
            distance=installed.distance(parts[name])
            if closest is None or distance<closest['distance_mm']:closest={'component':name,'distance_mm':distance}
        fit.append({'reference':ref,'status':'PASS','bbox_overlap_pairs_tested':checked,'collisions':collisions,'closest_existing_geometry_excluding_seating_board':closest})
    envelope_checks=[]
    for row in assembly_report['terminal_to_pd_clearance']:
        bb=row['conservative_housing_world_bounds_mm'];require(abs(bb[5]-14.2)<1e-6,'Terminal maximum-height envelope changed')
        envelope=cq.Workplane('XY').box(bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2]).translate(((bb[0]+bb[3])/2,(bb[1]+bb[4])/2,(bb[2]+bb[5])/2)).val()
        for ref,installed in legs.items():
            volume=installed.intersect(envelope).Volume() if overlap(bounds(installed),bb) else 0
            require(volume<=.005,'Leg intersects maximum terminal envelope')
            envelope_checks.append({'leg':ref,'terminal':row['reference'],'intersection_mm3':volume})
    print('Four legs versus complete native assembly and terminal maxima: PASS',flush=True)
    # Reorient the whole rigid assembly into gravity coordinates for both outputs.
    def gravity(shape):return shape.rotate((0,0,0),(1,0,0),180).translate((0,0,18))
    display=[];output_assembly=cq.Assembly(name='adhesive_legs_installed')
    for name,shape in {**parts,**{'leg_'+k:v for k,v in legs.items()}}.items():
        color=(.12,.47,.56) if name.startswith('leg_') else ((.12,.38,.20) if 'substrate' in name else (.63,.65,.67))
        shape=gravity(shape);display.append((name,shape,color));output_assembly.add(shape,name=name,color=cq.Color(*color))
    output_assembly.export(str(OUT/'installed-assembly.step'));helper.clean_step(OUT/'installed-assembly.step')
    render(display,OUT/'installed.png')
    require(before=={str(p.relative_to(ROOT)):sha(p) for p in tracked},'Input changed during verification')
    report={'schema_version':1,'status':'PASS','units':'mm','source_inputs_sha256':before,'source_pcb_sha256':assembly_report['pcb_sha256'],
            'profile_and_mesh':mesh_report,'corner_fit':fit,'maximum_terminal_envelope_checks':envelope_checks,
            'collision_frame':'Board B CAD: front planeZ0, positiveZ toward legs/floor; installed leg = X180 rotation + (holeX,-holeY,18)',
            'output_frame':'Whole installed assembly rotatedX180 then translatedZ18; adhesive facesZ0, nominal PCB frontZ18/backZ19.6',
            'source_files_unchanged':True,'floor_clearance':{'maximum_native_downward_projection_mm':max_native,'terminal_drawing_maximum_mm':14.2,
                'floor_plane_in_collision_frame_mm':18,'minimum_floor_gap_using_terminal_max_mm':18-max(14.2,max_native),
                'minimum_gap_to_base_inner_plane_mm':16-max(14.2,max_native),'adhesive_thickness_included':False},
            'adhesive_floor_footprint_mm':{'bounds_pcb_xy':[-3,-3,113,88],'size':[116,91],'overhang_each_board_edge_mm':3},
            'pcb_screw_passage':hole_checks,'screw_engagement':{'initial_screw':'M3x8','insertion_after1.6mmPCB_mm':6.4,'proven_profile_engagement_mm':4.5,'clearance_to_blind_floor_mm':3.6},
            'limits':['The upper untapped grip copies the user-proven source geometry. No modeled threads or replacement circular pilot were introduced.',
                      'The lower relief, blind depth, printing outcome and adhesive retention are properties of this new prototype.',
                      'The installed CAD includes existing illustrative component models and a14.2mm terminal envelope; wires, adhesive layers and metal screws are not modeled.',
                      'Zero nominal screw/PCB-hole clearance remains an actual free-pass check, separate from the proven printed grip.'],
            'artifact_sha256':{name:sha(OUT/name) for name in ['installed-assembly.step','installed.png']}}
    (OUT/'fit-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','report':str((OUT/'fit-check.json').relative_to(ROOT)),'corner_fit':fit,'floor_clearance':report['floor_clearance']}))


if __name__=='__main__':main()
