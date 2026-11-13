"""Controls for verify-insert-parts.py: a new part with copper on its own nets passes, anything else is refused."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PCB = HERE.parents[2] / 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
PRO = PCB.with_suffix('.kicad_pro')
SCRIPT = HERE / 'verify-insert-parts.py'
_spec = importlib.util.spec_from_file_location('verify_insert_parts', SCRIPT)
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)

# A copy of R76 renamed RX1, placed in an open spot, with its pads on two test nets plus one track on each.
NET_A, NET_B = 'TEST_A', 'TEST_B'
AT = (150.0, 5.0)


def footprint_block(text, ref):
    start = text.rindex('\n\t(footprint ', 0, text.index(f'(property "Reference" "{ref}"'))
    depth, i = 0, start + 1
    while True:
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1


def segment(net, a, b, layer='F.Cu'):
    return (f'\n\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width 0.2)\n\t\t(layer "{layer}")'
            f'\n\t\t(net "{net}")\n\t\t(uuid "00000000-0000-4000-8000-{abs(hash((net, a, b))) % 10**12:012d}")\n\t)')


class VerifyInsertParts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PCB.read_text()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.before = Path(cls.tmp.name) / 'before.kicad_pcb'
        cls.before.write_text(cls.text)
        cls.pro = cls.before.with_suffix('.kicad_pro')
        cls.pro.write_text(PRO.read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def inserted(self, net_a=NET_A, base=None):
        base = self.text if base is None else base
        start, end = footprint_block(base, 'R76')
        block = base[start:end].replace('"R76"', '"RX1"', 1)
        block = re.sub(r'\(at [-0-9.]+ [-0-9.]+\)', f'(at {AT[0]} {AT[1]})', block, count=1)
        nets = iter([net_a, NET_B])
        block = re.sub(r'\(net "[^"]+"\)', lambda _m: f'(net "{next(nets)}")', block)
        tracks = segment(net_a, (AT[0] - 2, AT[1]), (AT[0] - 4, AT[1])) + segment(NET_B, (AT[0] + 2, AT[1]), (AT[0] + 4, AT[1]))
        text = base[:end] + block + base[end:]
        first_segment = text.index('\n\t(segment')
        return text[:first_segment] + tracks + text[first_segment:]

    def split(self, ref='R75', pad='1'):
        """RX1 in series with REF.PAD: RX1 takes the pad's net and the pad moves to TEST_B."""
        start, end = footprint_block(self.text, ref)
        block = self.text[start:end]
        at = block.index(f'(pad "{pad}"')
        m = re.compile(r'\(net "([^"]+)"\)').search(block, at)
        moved = block[:m.start()] + f'(net "{NET_B}")' + block[m.end():]
        return m.group(1), self.inserted(m.group(1), self.text[:start] + moved + self.text[end:])

    def check(self, text, refs='RX1', extra=(), repins=None, pro_after=None, **kw):
        after = Path(self.tmp.name) / 'after.kicad_pcb'
        after.write_text(text)
        after.with_suffix('.kicad_pro').write_text(pro_after or self.pro.read_text())
        return verify.verify(str(self.before), str(after), set(refs.split(',')), list(extra), repins, **kw)

    def refused(self, text, message, **kw):
        with self.assertRaises(SystemExit) as caught:
            self.check(text, **kw)
        self.assertIn(message, str(caught.exception))

    def test_new_part_with_own_net_copper_passes(self):
        result = self.check(self.inserted())
        self.assertEqual(result['added_parts'], ['RX1'])
        self.assertEqual(result['part_nets'], [NET_A, NET_B])
        self.assertEqual(len(result['added_copper']), 2)
        self.assertEqual(result['removed_copper'], [])
        self.assertEqual(result['fill_vertices_changed_inside_region'], {})

    def test_copper_on_another_net_is_refused(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        text = text[:at] + segment('GND', (AT[0], AT[1] + 3), (AT[0] + 1, AT[1] + 3)) + text[at:]
        self.refused(text, 'outside the allowed set')

    def test_extra_net_must_be_named_and_used(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        text = text[:at] + segment('GND', (AT[0], AT[1] + 3), (AT[0] + 1, AT[1] + 3)) + text[at:]
        result = self.check(text, extra=['GND'])
        self.assertEqual(result['extra_nets'], ['GND'])
        self.refused(self.inserted(), 'allowed but not changed', extra=['GND'])

    def test_moved_existing_footprint_is_refused(self):
        text = self.inserted()
        start, end = footprint_block(text, 'R75')
        block = re.sub(r'\(at ([-0-9.]+) ', lambda m: f'(at {float(m.group(1)) + 0.1:g} ', text[start:end], count=1)
        self.refused(text[:start] + block + text[end:], 'Existing footprint R75 changed')

    def test_unexpected_or_missing_part_is_refused(self):
        self.refused(self.inserted(), 'differ from expected', refs='RX1,RX2')
        start, end = footprint_block(self.text, 'R75')
        self.refused(self.text[:start] + self.text[end:], 'Footprints removed', refs='RX1')

    def test_legend_change_is_refused(self):
        text = self.inserted()
        at = text.index('(gr_text "')
        text = text[:at] + '(gr_text "X' + text[at + len('(gr_text "'):]
        self.refused(text, 'Non-copper board content changed')

    def test_split_pad_must_be_named(self):
        net, text = self.split()
        result = self.check(text, repins={'R75.1': NET_B})
        self.assertEqual(result['repinned_pads'], [{'pad': 'R75.1', 'from': net, 'to': NET_B}])
        self.assertEqual(result['part_nets'], sorted([net, NET_B]))
        self.refused(text, 'Existing footprint R75 changed')
        self.refused(self.inserted(net), 'is not on TEST_B in AFTER', repins={'R75.1': NET_B})

    def test_repin_outside_part_nets_is_refused(self):
        _net, text = self.split()
        self.refused(text, 'must move between two pads of one new part', repins={'R75.1': 'GND'})
        self.refused(text, 'does not exist', repins={'R75.9': NET_B})

    def test_repin_to_an_existing_net_is_refused(self):
        start, end = footprint_block(self.text, 'R75')
        block = self.text[start:end]
        m = re.compile(r'\(net "([^"]+)"\)').search(block, block.index('(pad "1"'))
        other = re.compile(r'\(net "([^"]+)"\)').search(block, block.index('(pad "2"')).group(1)
        moved = self.text[:start] + block[:m.start()] + f'(net "{other}")' + block[m.end():] + self.text[end:]
        text = self.inserted(m.group(1), moved).replace(f'(net "{NET_B}")', f'(net "{other}")')
        self.refused(text, 'already exists in BEFORE', repins={'R75.1': other})

    def test_far_copper_on_part_net_is_refused(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        far = segment(NET_A, (AT[0] - 40, AT[1] + 30), (AT[0] - 41, AT[1] + 30))
        self.refused(text[:at] + far + text[at:], 'beyond 10.0 mm of the new parts')

    def test_relaxed_rule_is_refused(self):
        pro = json.loads(self.pro.read_text())
        pro['board']['design_settings']['rules']['min_clearance'] = 0.1
        self.refused(self.inserted(), 'Project design rules changed', pro_after=json.dumps(pro))

    def test_long_segment_between_anchors_is_checked_along_its_length(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        detour = segment(NET_A, (AT[0] - 4, AT[1]), (AT[0] - 4, AT[1] + 40)) + segment(NET_A, (AT[0] - 4, AT[1] + 40), (AT[0] - 3, AT[1]))
        self.refused(text[:at] + detour + text[at:], 'beyond 10.0 mm of the new parts')

    def test_fracture_slits_do_not_count_as_fill_change(self):
        square = [('0', '0'), ('10', '0'), ('10', '10'), ('0', '10')]
        hole = [('4', '4'), ('4', '6'), ('6', '6'), ('6', '4')]
        low = [square[0], square[1], square[2], square[3], ('0', '4'), *hole, ('4', '4'), ('0', '4')]
        high = [square[0], square[1], square[2], square[3], ('0', '6'), ('4', '6'), ('6', '6'), ('6', '4'), ('4', '4'),
                ('4', '6'), ('0', '6')]
        expected = verify.collections.Counter(square + hole)
        self.assertEqual(verify.ring_corners(low), expected)
        self.assertEqual(verify.ring_corners(high), expected)
        moved = [square[0], square[1], square[2], square[3], ('0', '4'), ('4', '4'), ('4', '6.5'), ('6', '6'),
                 ('6', '4'), ('4', '4'), ('0', '4')]
        self.assertNotEqual(verify.ring_corners(moved), expected)

    def test_far_slit_only_change_passes(self):
        text = self.inserted()
        at = text.index('(filled_polygon')
        xy = re.compile(r'\(xy ([-0-9.]+) ([-0-9.]+)\)')
        a = xy.search(text, at)
        b = xy.search(text, a.end())
        mx, my = (float(a.group(1)) + float(b.group(1))) / 2, (float(a.group(2)) + float(b.group(2))) / 2
        spike = f' (xy {mx:.6f} {my:.6f}) (xy {mx + 0.5:.6f} {my + 0.5:.6f}) (xy {mx:.6f} {my:.6f})'
        self.assertGreater(abs(mx - AT[0]) + abs(my - AT[1]), 10)
        result = self.check(text[:a.end()] + spike + text[a.end():])
        self.assertEqual(result['fill_vertices_changed_inside_region'], {})

    def test_far_near_duplicate_vertex_cluster_move_is_refused(self):
        text = self.inserted()
        for x in ('69.535926', '69.535929', '69.535931'):
            self.assertIn(f'(xy {x} 21.8495)', text)
            text = text.replace(f'(xy {x} 21.8495)', f'(xy {x} 22.2495)')
        self.refused(text, 'changed outside the edit region')

    XY = re.compile(r'\(xy ([-0-9.]+) ([-0-9.]+)\)')

    def far_polygon(self, text, need_slit, need_sibling=False):
        """(start, end, points) of the first filled polygon far from AT, optionally with a fracture slit or a sibling."""
        at = 0
        while True:
            start = text.index('(filled_polygon', at)
            end = text.index('(filled_polygon', start + 1) if '(filled_polygon' in text[start + 1:] else len(text)
            end = min(end, text.index('\n\t)', start))
            pts = [m for m in self.XY.finditer(text, start, end)]
            coords = [(m.group(1), m.group(2)) for m in pts]
            far = all(abs(float(x) - AT[0]) + abs(float(y) - AT[1]) > 20 for x, y in coords)
            edges = set(zip(coords, coords[1:] + coords[:1]))
            zone_end = text.find('\n\t(zone', end)
            sibling = text.find('(filled_polygon', end) != -1 and (zone_end == -1 or text.find('(filled_polygon', end) < zone_end)
            if far and (not need_slit or any((b, a) in edges for a, b in edges)) and (not need_sibling or sibling):
                return start, end, pts
            at = end

    def test_far_move_within_max_error_is_recorded(self):
        text = self.inserted()
        _start, _end, pts = self.far_polygon(text, False)
        m = pts[0]
        moved = f'(xy {float(m.group(1)) + 0.003:.6f} {m.group(2)})'
        result = self.check(text[:m.start()] + moved + text[m.end():])
        self.assertEqual(result['fill_max_error_mm'], 0.005)
        (zone, record), = result['fill_retessellated_outside_region'].items()
        self.assertEqual(record['vertices'], 2)
        self.assertTrue(0 < record['max_distance_mm'] <= 0.003)

    def test_far_hole_removed_is_refused(self):
        text = self.inserted()
        _start, _end, pts = self.far_polygon(text, True)
        coords = [(m.group(1), m.group(2)) for m in pts]
        n = len(coords)
        edges = set(zip(coords, coords[1:] + coords[:1]))
        i = next(k for k in range(n) if (coords[(k + 1) % n], coords[k]) in edges and coords[k] != coords[(k + 1) % n])
        j = next(k for k in range(i + 2, n) if coords[k] == coords[i])
        cut = text[:pts[i].end()] + text[pts[j].end():]
        self.refused(cut, 'more than max_error')

    def test_far_island_removed_is_refused(self):
        text = self.inserted()
        start, end, _pts = self.far_polygon(text, False, True)
        block_start = text.rindex('\n', 0, start)
        self.refused(text[:block_start] + text[end:], 'outside the edit region')

    def test_fill_change_far_away_is_refused(self):
        text = self.inserted()
        at = text.index('(filled_polygon')
        xy = re.compile(r'\(xy ([-0-9.]+) ([-0-9.]+)\)')
        m = xy.search(text, at)
        moved = f'(xy {float(m.group(1)) + 0.01:g} {m.group(2)})'
        self.assertGreater(abs(float(m.group(1)) - AT[0]) + abs(float(m.group(2)) - AT[1]), 10)
        self.refused(text[:m.start()] + moved + text[m.end():], 'changed outside the edit region')


if __name__ == '__main__':
    unittest.main()
