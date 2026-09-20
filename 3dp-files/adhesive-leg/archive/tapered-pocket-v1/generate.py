#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["cadquery==2.6.1", "trimesh==4.8.3", "networkx==3.5"]
# ///
"""Build the adhesive-base PCB leg using the user's measured rail aperture."""
from pathlib import Path
import hashlib,json,math,zipfile
import cadquery as cq
import numpy as np
import trimesh
import vtk

HERE=Path(__file__).resolve().parent
OUT=HERE/'generated'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def mesh(s):
 vertices,faces=s.tessellate(.01,.08)
 return trimesh.Trimesh(np.array([v.toTuple() for v in vertices]),np.array(faces),process=True)
def build(spec,profile):
 height=spec['seat_height_mm'];base=spec['base'];pole=spec['pole'];bore=spec['screw_bore'];t=base['thickness_mm']
 foot=(cq.Workplane('XY').rect(base['width_mm'],base['depth_mm']).extrude(t)
       .edges('|Z').fillet(base['corner_radius_mm']).val())
 stem=cq.Workplane('XY').workplane(offset=t).circle(pole['diameter_mm']/2).extrude(height-t-pole['top_taper_height_mm']).val()
 tip=cq.Solid.makeCone(pole['diameter_mm']/2,pole['seating_diameter_mm']/2,pole['top_taper_height_mm'],cq.Vector(0,0,height-pole['top_taper_height_mm']))
 body=foot.fuse(stem).fuse(tip).clean()
 root=[e for e in body.Edges() if e.geomType()=='CIRCLE' and abs(e.Center().z-t)<1e-6 and abs(e.Length()-math.pi*pole['diameter_mm'])<1e-6]
 assert len(root)==1,'Ambiguous pole/base junction'
 body=body.fillet(pole['root_fillet_radius_mm'],root)
 grip=(cq.Workplane('XY').polyline(profile).close().extrude(bore['gripping_depth_mm']+.1)
       .translate((0,0,height-bore['gripping_depth_mm'])).val())
 relief=(cq.Workplane('XY').circle(bore['lower_clearance_diameter_mm']/2)
         .extrude(bore['total_blind_depth_mm']-bore['gripping_depth_mm'])
         .translate((0,0,height-bore['total_blind_depth_mm'])).val())
 leg=body.cut(grip.fuse(relief)).clean()
 assert leg.isValid() and len(leg.Solids())==1
 return leg

def render(parts,destination,title,elev=25,azim=-55):
 renderer=vtk.vtkRenderer();renderer.SetBackground(.94,.95,.97);all_points=[]
 for name,shape,color in parts:
  m=mesh(shape);all_points.append(m.vertices);points=vtk.vtkPoints()
  for point in m.vertices:points.InsertNextPoint(*point)
  cells=vtk.vtkCellArray()
  for face in m.faces:
   cells.InsertNextCell(3)
   for index in face:cells.InsertCellPoint(int(index))
  data=vtk.vtkPolyData();data.SetPoints(points);data.SetPolys(cells)
  normals=vtk.vtkPolyDataNormals();normals.SetInputData(data);normals.SetFeatureAngle(40);normals.Update()
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color);actor.GetProperty().SetInterpolationToPhong();renderer.AddActor(actor)
 points=np.concatenate(all_points);lo=points.min(axis=0);hi=points.max(axis=0);center=(hi+lo)/2;span=hi-lo
 a,e=math.radians(azim),math.radians(elev);direction=np.array([math.cos(e)*math.cos(a),math.cos(e)*math.sin(a),math.sin(e)])
 camera=renderer.GetActiveCamera();camera.SetPosition(*(center+direction*np.linalg.norm(span)*2));camera.SetFocalPoint(*center);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();camera.SetParallelScale(np.linalg.norm(span)*.51)
 text=vtk.vtkTextActor();text.SetInput(title);text.SetDisplayPosition(24,1125);text.GetTextProperty().SetFontSize(23);text.GetTextProperty().SetColor(.12,.16,.20);renderer.AddActor2D(text)
 window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1400,1180);window.SetMultiSamples(8);window.AddRenderer(renderer);renderer.ResetCameraClippingRange();window.Render()
 capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(destination));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()

def main():
 spec=json.loads((HERE/'spec.json').read_text());reference=json.loads((HERE/'reference-bore.json').read_text());profile=reference['selected_profile']['centered_vertices_xy_mm']
 assert spec['screw_bore']['gripping_depth_mm']==reference['tested_source_geometry']['through_depth_mm']
 leg=build(spec,profile);OUT.mkdir(exist_ok=True)
 main=OUT/'adhesive-leg-18mm-m3.stl';m=mesh(leg);m.export(main)
 assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split())==1
 cq.exporters.export(leg,str(OUT/'adhesive-leg-18mm-m3.step'))
 four=cq.Compound.makeCompound([leg.translate((x,y,0)) for x,y in [(0,0),(19,0),(0,19),(19,19)]])
 plate=mesh(four);plate.export(OUT/'adhesive-leg-18mm-m3-4x.stl');assert plate.is_watertight and len(plate.split())==4
 render([('leg',leg,(.15,.43,.51))],OUT/'preview.png','18 mm adhesive PCB leg | M3 rail-profile grip')
 cutter=cq.Workplane('XY').box(40,20,40).translate((0,-10,18)).val()
 cutaway=leg.cut(cutter)
 render([('section',cutaway,(.15,.43,.51))],OUT/'section.png','4.5 mm proven grip + screw-tip clearance below',elev=15,azim=-90)
 render([('four',four,(.15,.43,.51))],OUT/'four-up.png','Four separate legs | flat bases on print bed')
 report={'status':'PASS','units':'mm','cad_valid':leg.isValid(),'single_part':{'triangles':len(m.faces),'watertight':m.is_watertight,'winding_consistent':m.is_winding_consistent,'connected_solids':len(m.split()),'bounds_mm':m.bounds.tolist(),'cad_volume_mm3':leg.Volume(),'stl_volume_mm3':float(m.volume)},'four_up':{'connected_solids':len(plate.split()),'watertight':plate.is_watertight,'bounds_mm':plate.bounds.tolist()},'source_sha256':{p.name:sha(p) for p in [Path(__file__),HERE/'spec.json',HERE/'reference-bore.json']},'geometry_only':'Run verify.py for independent source-profile, mounting and populated-assembly checks.'}
 (OUT/'mesh-check.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
