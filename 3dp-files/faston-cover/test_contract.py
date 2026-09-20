"""Ensure geometry mutations cannot pass the cover's PCB contract."""
from pathlib import Path
import copy
import json
import unittest
from contract import check_pcb,find_all
HERE=Path(__file__).resolve().parent
C=json.loads((HERE/'pcb-contract.json').read_text())
def a(value):return ('atom',str(value))
def q(value):return ('str',str(value))
def line(x,y):return [a('gr_line'),[a('start'),*map(a,x)],[a('end'),*map(a,y)],[a('layer'),q('Edge.Cuts')]]
def fixture():
 t=[a('kicad_pcb'),[a('general'),[a('thickness'),a(1.6)]]]
 for start,end in [((0,0),(110,0)),((110,0),(110,85)),((110,85),(0,85))]:t.append(line(start,end))
 prev=[0,0]
 for n in C['notch_geometry']['notches']:
  path=n['edge_path_top_to_bottom'];t.append(line(prev,path[0]['start']))
  for e in path:
   item=[a('gr_'+e['type'])]
   for k in ['start','mid','end']:
    if k in e:item.append([a(k),*map(a,e[k])])
   item.append([a('layer'),q('Edge.Cuts')]);t.append(item)
  prev=path[-1]['end']
 t.append(line(prev,[0,85]))
 for f in C['fastons']['placements']:
  model=[a('model'),q('reviewed.wrl')]
  for name,values in [('rotate',[0,0,90]),('offset',[0,0,0]),('scale',[1,1,1])]:
   model.append([a(name),[a('xyz'),*map(a,values)]])
  t.append([a('footprint'),q(C['fastons']['footprint']),
            [a('property'),q('Reference'),q(f['reference'])],
            [a('property'),q('LCSC'),q('C591344')],
            [a('layer'),q('B.Cu')],[a('at'),*map(a,f['center_mm']),a(270)],model])
 return t
class ContractTests(unittest.TestCase):
 def test_expected(self):self.assertEqual(check_pcb(fixture(),C)['status'],'PASS')
 def test_missing_notch_arc(self):
  t=fixture();t.remove(find_all(t,'gr_arc')[0])
  with self.assertRaises(ValueError):check_pcb(t,C)
 def test_wrong_side(self):
  t=fixture();find_all(find_all(t,'footprint')[0],'layer')[0][1]=q('F.Cu')
  with self.assertRaises(ValueError):check_pcb(t,C)
 def test_wrong_direction(self):
  t=fixture();find_all(find_all(t,'footprint')[0],'at')[0][-1]=a(90)
  with self.assertRaises(ValueError):check_pcb(t,C)
 def test_wrong_model_origin(self):
  t=fixture();m=find_all(find_all(t,'footprint')[0],'model')[0];find_all(find_all(m,'offset')[0],'xyz')[0][2]=a(-7)
  with self.assertRaises(ValueError):check_pcb(t,C)
 def test_extra_outline(self):
  t=fixture();t.append([a('gr_circle'),[a('layer'),q('Edge.Cuts')]])
  with self.assertRaises(ValueError):check_pcb(t,C)
 def test_thickness(self):
  t=fixture();find_all(find_all(t,'general')[0],'thickness')[0][1]=a(2)
  with self.assertRaises(ValueError):check_pcb(t,C)
if __name__=='__main__':unittest.main()
