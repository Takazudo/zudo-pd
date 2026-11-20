"""Controls for verify-insert-parts.py: a new part with copper on its own nets passes, anything else is refused."""
import importlib.util
import json
import os
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

    def value_changed(self, ref, base=None):
        base = self.text if base is None else base
        start, end = footprint_block(base, ref)
        block = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "SYNCED"', base[start:end], count=1)
        return base[:start] + block + base[end:]

    def test_field_sync_allows_value_text_only(self):
        result = self.check(self.value_changed('R61', self.inserted()), field_sync={'R61'})
        self.assertEqual(result['field_synced_parts'], ['R61'])
        self.refused(self.value_changed('R61', self.inserted()), 'Existing footprint R61 changed')

    def test_field_sync_refuses_a_moved_footprint(self):
        text = self.value_changed('R61', self.inserted())
        start, end = footprint_block(text, 'R61')
        block = re.sub(r'\(at ([-0-9.]+) ', lambda m: f'(at {float(m.group(1)) + 0.5} ', text[start:end], count=1)
        self.refused(text[:start] + block + text[end:], 'Existing footprint R61 changed', field_sync={'R61'})

    def test_replaced_footprint_may_change_and_must_change(self):
        text = self.inserted()
        start, end = footprint_block(text, 'R61')
        block = re.sub(r'\(at ([-0-9.]+) ', lambda m: f'(at {float(m.group(1)) + 0.5} ', text[start:end], count=1)
        result = self.check(text[:start] + block + text[end:], replaced={'R61'})
        self.assertEqual(result['replaced_parts'], ['R61'])
        self.refused(self.inserted(), 'did not change', replaced={'R61'})

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
        self.refused(text[:at] + far + text[at:], 'beyond 10.0 mm')

    def test_relaxed_rule_is_refused(self):
        pro = json.loads(self.pro.read_text())
        pro['board']['design_settings']['rules']['min_clearance'] = 0.1
        self.refused(self.inserted(), 'Project design rules changed', pro_after=json.dumps(pro))

    def test_long_segment_between_anchors_is_checked_along_its_length(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        detour = segment(NET_A, (AT[0] - 4, AT[1]), (AT[0] - 4, AT[1] + 40)) + segment(NET_A, (AT[0] - 4, AT[1] + 40), (AT[0] - 3, AT[1]))
        self.refused(text[:at] + detour + text[at:], 'beyond 10.0 mm')

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

    def test_fill_change_far_away_is_refused(self):
        text = self.inserted()
        at = text.index('(filled_polygon')
        xy = re.compile(r'\(xy ([-0-9.]+) ([-0-9.]+)\)')
        m = xy.search(text, at)
        moved = f'(xy {float(m.group(1)) + 0.01:g} {m.group(2)})'
        self.assertGreater(abs(float(m.group(1)) - AT[0]) + abs(float(m.group(2)) - AT[1]), 10)
        self.refused(text[:m.start()] + moved + text[m.end():], 'changed outside the edit region')


class OutsideFillGain(VerifyInsertParts):
    """--allow-outside-fill-gain: a pure copper gain outside the edit region passes; a loss, a gain on a net that is not
    allowed, and every non-fill change are still refused (negative controls)."""
    ZONE = 'effbc381-86bc-5185-a325-99ab337d2695'   # the main GND zone on B.Cu
    IN1 = '66bdc61b-a697-57c7-8c21-d31d7ae259ea'

    def zone_span(self, text, uuid):
        at = text.index(f'(uuid "{uuid}")')
        start = text.rindex('\n\t(zone', 0, at)
        depth, i = 0, start + 1
        while True:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    return start, i + 1
            i += 1

    def rings(self, text):
        return verify.fill_rings(verify.parse(verify.tokenize(text)))

    def free_square(self, text, uuid, layer, inside):
        """A 0.6 mm square, 1 mm clear of the fill boundary, wholly outside (or inside) the zone's fill, far from AT."""
        rings = self.rings(text)[(uuid, layer)]
        for x in range(5, 105):
            for y in range(5, 80):
                c = (x + 0.5, y + 0.5)
                if verify.fill_inside(c, rings) == inside and verify.fill_boundary_distance(c, rings) > 1.0:
                    return [(c[0] - 0.3, c[1] - 0.3), (c[0] + 0.3, c[1] - 0.3), (c[0] + 0.3, c[1] + 0.3), (c[0] - 0.3, c[1] + 0.3)]
        self.skipTest('no free square found')

    def with_gnd_track(self):
        """The inserted RX1 plus one GND segment beside it, so that GND is an allowed (changed) net."""
        text = self.inserted()
        at = text.index('\n\t(segment')
        return text[:at] + segment('GND', (AT[0] - 2, AT[1] + 3), (AT[0] - 4, AT[1] + 3)) + text[at:]

    def add_island(self, text, uuid, layer, square):
        start, end = self.zone_span(text, uuid)
        pts = ' '.join(f'(xy {x:.6f} {y:.6f})' for x, y in square)
        island = f'\n\t\t(filled_polygon\n\t\t\t(layer "{layer}")\n\t\t\t(pts {pts})\n\t\t)'
        return text[:end - 2] + island + text[end - 2:]

    def gain_text(self):
        text = self.with_gnd_track()
        return self.add_island(text, self.ZONE, 'B.Cu', self.free_square(text, self.ZONE, 'B.Cu', inside=False))

    def test_far_gain_is_refused_without_the_option(self):
        self.refused(self.gain_text(), 'changed outside the edit region', extra=['GND'])

    def test_far_gain_passes_with_the_option(self):
        result = self.check(self.gain_text(), extra=['GND'], allow_outside_fill_gain=True)
        gain = result['fill_gain_outside_region'][f'{self.ZONE}/B.Cu']
        self.assertEqual((gain['corners_removed_outside'], gain['corners_added_outside']), (0, 4))
        self.assertEqual(result['fill_gain_eps_mm'], 0.01)

    def test_far_island_removed_is_refused(self):
        text = self.with_gnd_track()
        start, end = self.zone_span(text, self.ZONE)
        block = text[start:end]
        polys = [m.start() for m in re.finditer(r'\(filled_polygon', block)]
        sizes = []
        for i, p in enumerate(polys):
            q = polys[i + 1] if i + 1 < len(polys) else len(block) - 2
            sizes.append((q - p, p, q))
        _, p, q = min(sizes)
        cut = block[:p].rstrip('\t\n ') + '\n\t\t' + block[q:].lstrip('\t\n ')
        self.refused(text[:start] + cut + text[end:], 'lost copper outside the edit region', extra=['GND'],
                     allow_outside_fill_gain=True)

    def test_far_new_hole_is_refused(self):
        text = self.with_gnd_track()
        square = self.free_square(text, self.IN1, 'In1.Cu', inside=True)
        start, end = self.zone_span(text, self.IN1)
        block = text[start:end]
        m = re.compile(r'\(pts\s*\(xy ([-0-9.]+) ([-0-9.]+)\)').search(block, block.index('(filled_polygon'))
        foot = f'(xy {m.group(1)} {m.group(2)})'
        hole = ' '.join(f'(xy {x:.6f} {y:.6f})' for x, y in [square[0], square[3], square[2], square[1], square[0]])
        block = block[:m.end()] + ' ' + hole + ' ' + foot + block[m.end():]
        self.refused(text[:start] + block + text[end:], 'lost copper outside the edit region', extra=['GND'],
                     allow_outside_fill_gain=True)

    def test_gain_on_a_net_that_is_not_allowed_is_refused(self):
        text = self.inserted()
        text = self.add_island(text, self.ZONE, 'B.Cu', self.free_square(text, self.ZONE, 'B.Cu', inside=False))
        self.refused(text, 'net that is not allowed', allow_outside_fill_gain=True)

    def test_option_does_not_admit_other_net_copper(self):
        text = self.gain_text()
        m = re.search(r'\(segment\s*\(start ([-0-9.]+) ([-0-9.]+)\)(?:(?!\(segment)[\s\S])*?\(net "(?!GND|TEST_)[^"]+"\)', text)
        moved = text[:m.start(1)] + f'{float(m.group(1)) + 0.1:g}' + text[m.end(1):]
        self.refused(moved, 'Copper on a net outside the allowed set changed', extra=['GND'], allow_outside_fill_gain=True)

    def test_option_does_not_admit_a_zone_setting_change(self):
        text = self.gain_text()
        start, end = self.zone_span(text, self.ZONE)
        block = text[start:end]
        self.assertIn('(clearance 0.25)', block)
        changed = block.replace('(clearance 0.25)', '(clearance 0.2)', 1)
        self.refused(text[:start] + changed + text[end:], 'Non-copper board content changed', extra=['GND'],
                     allow_outside_fill_gain=True)

    @unittest.skipUnless(os.environ.get('B20_D2_BEFORE'), 'set B20_D2_BEFORE to the D2 BEFORE board (main b377136)')
    def test_d2_refilled_board_passes_only_with_the_option(self):
        before = Path(os.environ['B20_D2_BEFORE'])
        args = dict(refs=set('C44,C45,CDG12,CDG5,D4,D5,Q13,Q7,Q8,Q9,R81,R82,RDG12,RDG5,RSQ1,RSQ2,RSQ3,RSQ4,RXN2,RXN3'.split(',')),
                    extra_nets=[], replaced=set('Q51,Q52,Q55,RX12,RX5,R76'.split(',')), field_sync={'R61', 'R62'},
                    reach_mm=12, added_reach_mm=26)
        with self.assertRaisesRegex(SystemExit, 'changed outside the edit region'):
            verify.verify(str(before), str(PCB), **args)
        result = verify.verify(str(before), str(PCB), allow_outside_fill_gain=True, **args)
        self.assertEqual(len(result['fill_gain_outside_region']), 3)



for _name in [n for n in vars(VerifyInsertParts) if n.startswith('test_')]:
    setattr(OutsideFillGain, _name, None)   # run the base controls once, in their own class

if __name__ == '__main__':
    unittest.main()
