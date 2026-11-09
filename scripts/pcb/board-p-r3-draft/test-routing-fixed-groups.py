"""Focused host regression for multiple fixed copper groups containing numpy masks."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

SOURCE = Path(__file__).with_name('route-signals.py')


class FixedGroupTests(unittest.TestCase):
    def test_nearer_second_fixed_group_routes_without_array_equality(self):
        def pad(ref, x, y):
            return {'ref':ref,'num':'1','net':'VBUS_IN','layers':['B'],
                    'center':[x,y],'bbox':[x-.3,y-.3,x+.3,y+.3],'drill':0}
        geometry={'pads':[pad('A',8.25,8),pad('B',5.25,5)],'rule_areas':[],'tracks':[],'vias':[]}
        pours={'pours':[{'net':'VBUS_IN','layer':'F.Cu','outlines':[[[1,1],[3,1],[3,3],[1,3]]]}],
               'tracks':[{'net':'VBUS_IN','layer':'B','w':.4,'a':[8,8],'b':[8.5,8]},
                         {'net':'VBUS_IN','layer':'B','w':.4,'a':[5,5],'b':[5.5,5]}],'vias':[]}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'geom.json').write_text(json.dumps(geometry))
            (root/'pours.json').write_text(json.dumps(pours))
            previous=sys.argv
            try:
                sys.argv=[str(SOURCE),str(root/'geom.json'),str(root/'pours.json'),str(root/'unused.json')]
                scope={'__name__':'router_unit_fixture'}
                # Import the real setup/functions, omitting only the full-board multi-pass CLI driver.
                exec(compile(SOURCE.read_text().split('for k in range(0 if JOIN')[0],str(SOURCE),'exec'),scope)
                failures,victims=scope['route_net']('VBUS_IN')
                self.assertEqual(failures,[])
                self.assertEqual(victims,set())
                self.assertEqual(len(scope['FIXED_TRACKS']),2)
                self.assertTrue(scope['routed_tracks'])
            finally:
                sys.argv=previous


if __name__=='__main__':
    unittest.main()
