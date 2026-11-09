"""Run with pinned pcbnew Python under the native lock; no board mutation."""
from pathlib import Path
import unittest
import pcbnew
from native_connectivity import pad_polygon_contacts

ROOT = Path(__file__).resolve().parents[3]


class PadContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if pcbnew.GetBuildVersion() != '10.0.6':
            raise RuntimeError('Pinned KiCad 10.0.6 is required')
        cls.board = pcbnew.LoadBoard(str(ROOT/'boards/board-p/board-p.kicad_pcb'))
        cls.pad = next(p for f in cls.board.GetFootprints() if f.GetReference() == 'U1'
                       for p in f.Pads() if p.GetNumber() == '22')

    def rectangle(self, x0, y0, x1, y1, layer=pcbnew.F_Cu):
        cx, cy = (pcbnew.ToMM(self.pad.GetPosition().x), pcbnew.ToMM(self.pad.GetPosition().y))
        poly = pcbnew.SHAPE_POLY_SET()
        poly.NewOutline()
        for x, y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:
            poly.Append(pcbnew.FromMM(cx+x), pcbnew.FromMM(cy+y))
        return poly, [(layer,poly.Outline(0))]

    def test_partial_pad_contact_with_center_outside(self):
        poly, outlines = self.rectangle(.22,-.04,.30,.04)
        self.assertFalse(outlines[0][1].PointInside(self.pad.GetPosition()))
        self.assertEqual(list(pad_polygon_contacts([self.pad],outlines,[poly])),[(0,0)])

    def test_real_copper_gap_is_not_contact(self):
        poly, outlines = self.rectangle(.40,-.04,.50,.04)
        self.assertEqual(list(pad_polygon_contacts([self.pad],outlines,[poly])),[])

    def test_pad_inside_filled_polygon_hole_is_not_contact(self):
        poly, outlines = self.rectangle(-1,-1,1,1)
        hole, _ = self.rectangle(-.45,-.24,.45,.24)
        poly.AddHole(hole.Outline(0))
        # AddHole may reallocate native storage; reacquire borrowed SWIG outlines.
        outlines = [(pcbnew.F_Cu, poly.Outline(0))]
        self.assertEqual(poly.HoleCount(0),1)
        self.assertTrue(outlines[0][1].PointInside(self.pad.GetPosition()))
        self.assertFalse(poly.Contains(self.pad.GetPosition()))
        self.assertEqual(list(pad_polygon_contacts([self.pad],outlines,[poly])),[])

    def test_other_layer_is_not_contact(self):
        poly, outlines = self.rectangle(.22,-.04,.30,.04,pcbnew.B_Cu)
        self.assertEqual(list(pad_polygon_contacts([self.pad],outlines,[poly])),[])


if __name__ == '__main__':
    unittest.main()
