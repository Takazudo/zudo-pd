"""Synthetic geometry controls, not an actual assembled-board clearance result."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import cadquery as cq

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('supplement',HERE/'supplemental-clearance.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from sexp import parse,tokenize,find_all
DATA=json.loads(s.DATA.read_text())
CONTRACT={'pd_stack':{'collision_policy':{'maximum_unintended_intersection_mm3':.005}}}


def place(shape,contract):
    return shape.rotate((0,0,0),(1,-1,0),180).translate((-.5,-12,11.1))


def fixture(angle=0):
    fps=[];parts={};sources={};origins={}
    for i,e in enumerate(DATA['envelopes']):
        x=i*20
        fp=parse(tokenize(f'''(footprint "{e['footprint']}" (layer "F.Cu") (at {x} 0 {angle}) (attr smd)
          (property "Reference" "{e['Reference']}") (property "Value" "{e['Value']}") (property "LCSC" "{e['LCSC']}")
          (model "{e['model']}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'''))
        fps.append(fp);sources.update(e['model_sha256']);origins[e['Reference']]=[x,0,.04]
        parts[e['Reference']]=cq.Workplane('XY').box(*e['body_mm'],centered=(True,True,False)).val().rotate((0,0,0),(0,0,1),angle).translate((x,0,.04))
    return [('atom','kicad_pcb'),*fps],parts,origins,sources


class EnvelopeTests(unittest.TestCase):
    def test_clear_geometry_and_orthogonal_rotation(self):
        for angle in [0,90,-90,180]:
            tree,parts,origins,sources=fixture(angle)
            result=s.screen(tree,parts,origins,sources,cq.Workplane('XY').box(1,1,1).translate((100,100,100)).val(),{},CONTRACT,place)
            self.assertEqual(result['status'],'PASS')
            self.assertEqual(len(result['results']),2)
            self.assertTrue(all(r['closest_pair']['clearance_mm']>0 for r in result['results']))
    def test_omitted_lead_region_collision_is_detected(self):
        tree,parts,origins,sources=fixture()
        obstacle=place(cq.Workplane('XY').box(.2,.2,.2).translate((3.1,0,.5)).val(),CONTRACT)
        self.assertEqual(place(parts['U2'],CONTRACT).intersect(obstacle).Volume(),0)
        result=s.screen(tree,parts,origins,sources,obstacle,{},CONTRACT,place)
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['failures'][0]['board_p_ref'],'U2')
    def test_wrong_native_axis_or_datum_is_rejected(self):
        tree,parts,origins,sources=fixture(90)
        for wrong in [cq.Workplane('XY').box(*DATA['envelopes'][0]['body_mm'],centered=(True,True,False)).val(),parts['U2'].translate((0,0,.1))]:
            with self.assertRaisesRegex(ValueError,'axis/dimension/datum'):
                s.make_envelope(DATA['envelopes'][0],find_all(tree,'footprint')[0],wrong,origins['U2'],sources)
    def test_wrong_stack_axis_is_rejected(self):
        tree,parts,origins,sources=fixture()
        with self.assertRaisesRegex(ValueError,'face-to-face'):
            s.screen(tree,parts,origins,sources,cq.Workplane('XY').box(1,1,1).val(),{},CONTRACT,lambda shape,c:shape)
    def test_identity_and_model_hash_fail_closed(self):
        tree,parts,origins,sources=fixture();entry=DATA['envelopes'][0];fp=find_all(tree,'footprint')[0]
        wrong=copy.deepcopy(entry);wrong['Value']='substitute'
        with self.assertRaisesRegex(ValueError,'identity'):s.make_envelope(wrong,fp,parts['U2'],origins['U2'],sources)
        with self.assertRaisesRegex(ValueError,'bytes'):s.make_envelope(entry,fp,parts['U2'],origins['U2'],{})

if __name__=='__main__':unittest.main()
