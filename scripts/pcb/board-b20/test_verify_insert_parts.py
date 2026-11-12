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
        cls.pro = Path(cls.tmp.name) / 'before.kicad_pro'
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
        pro = Path(self.tmp.name) / 'after.kicad_pro'
        pro.write_text(pro_after or self.pro.read_text())
        return verify.verify(str(self.before), str(after), set(refs.split(',')), list(extra), repins,
                             str(self.pro), str(pro), **kw)

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
        self.refused(text, 'must move between two different new-part nets', repins={'R75.1': 'GND'})
        self.refused(text, 'does not exist', repins={'R75.9': NET_B})

    def test_far_copper_on_part_net_is_refused(self):
        text = self.inserted()
        at = text.index('\n\t(segment')
        far = segment(NET_A, (AT[0] - 40, AT[1] + 30), (AT[0] - 41, AT[1] + 30))
        self.refused(text[:at] + far + text[at:], 'beyond 10.0 mm of the new parts')

    def test_relaxed_rule_is_refused(self):
        pro = json.loads(self.pro.read_text())
        pro['board']['design_settings']['rules']['min_clearance'] = 0.1
        self.refused(self.inserted(), 'Project design rules changed', pro_after=json.dumps(pro))

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
