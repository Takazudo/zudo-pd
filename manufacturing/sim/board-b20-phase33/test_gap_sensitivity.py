import json
from pathlib import Path
import re
import tempfile
import unittest

import extract_reference as ex
import gap_sensitivity as gap

HERE = Path(__file__).resolve().parent
CRITERIA = HERE / 'd1-gap-criteria.md'


class DeckTests(unittest.TestCase):
    def test_eight_variant_cases_and_their_offsets(self):
        labels = gap.labels()
        self.assertEqual(sorted(labels), ['g12', 'g16', 'g20', 'worst'])
        self.assertEqual(sum(len(v) for v in labels.values()), 8)
        for rail in gap.RAILS:
            for g in gap.TARGET_GAPS_V:
                kind, shift = labels[f'g{int(round(g * 10)):02d}'][rail]
                self.assertEqual(kind, 'enabled-gated')
                self.assertAlmostEqual(gap.BASELINE_GAP_V[rail] - shift, g, places=6)
            self.assertEqual(labels['worst'][rail], ('constant', -gap.WORST_EXTRA_V))

    def test_offset_lines_keep_nodes_and_gate_on_enable(self):
        self.assertEqual(gap.offset_line('+5', 'enabled-gated', 0.4434),
                         'BVO2 p5_g p5_gi V=0-0.4434*0.5*(1+tanh((2.5-v(enn))*4))')
        self.assertEqual(gap.offset_line('-12', 'enabled-gated', 1.6668),
                         'BVO3 m12_g m12_gi V=0.5-1.6668*0.5*(1+tanh((2.5-v(enn))*4))')
        self.assertEqual(gap.offset_line('+5', 'constant', -0.3), 'VO2 p5_g p5_gi 0.3')
        self.assertEqual(gap.offset_line('-12', 'constant', -0.3), 'VO3 m12_g m12_gi 0.8')

    def test_variant_changes_only_the_registered_lines(self):
        decks = ex.derive_decks()
        for rail, spec in gap.RAILS.items():
            name = spec['case']
            base = decks[name]['executed']
            text = gap.variant(base, name, rail, 'enabled-gated', 0.4)
            removed = set(base.splitlines()) - set(text.splitlines())
            added = set(text.splitlines()) - set(base.splitlines())
            self.assertEqual(removed, {spec['line'], gap.DISABLE_LINE[0]})
            self.assertEqual(added, {gap.offset_line(rail, 'enabled-gated', 0.4), gap.DISABLE_LINE[1], gap.gap_line(name)})
        with self.assertRaisesRegex(ValueError, 'expected exactly one'):
            gap.variant(decks['nom']['executed'], 'nom', '-12', 'constant', -0.3)


class MeasurementTests(unittest.TestCase):
    def series(self, f, stop=0.25, step=1e-6):
        times = [k * step for k in range(int(stop / step) + 1)]
        return times, [f(t) for t in times]

    def test_overshoot_drop_and_extremes(self):
        times, values = self.series(lambda t: min(t, 0.1) * 10 + (0.05 if 0.15 <= t < 0.16 else 0.0))
        self.assertAlmostEqual(gap.overshoot(times, values, 1, 0.04, 0.2345), 0.05, places=6)
        drop = gap.largest_drop(times, values, 1, 0.04, 0.2345)  # a step inside a bin splits across two bin means
        self.assertLess(drop, -0.025)
        self.assertGreaterEqual(drop, -0.05 - 1e-9)
        lo, hi = gap.extremes(times, values, 0.002, 0.04)
        self.assertAlmostEqual(lo, 0.02, places=4)
        self.assertAlmostEqual(hi, 0.4, places=4)

    def test_within_resolves_to_vntol(self):
        self.assertTrue(gap.within((0.0, 1.0), (0.0, 1.0 - gap.VNTOL_V / 2)))
        self.assertFalse(gap.within((0.0, 1.0), (0.0, 1.0 - 2 * gap.VNTOL_V)))

    def test_screen_pass_requires_slope_straddle_and_current(self):
        ok = {'recorded_bound_exceeding_segments': 0, 'voltage_boundary_straddling_segments': 0,
              'exception': {'current_ceiling_exceeded_in_saved_samples': False}}
        self.assertTrue(gap.screen_passes(ok))
        for key, value in (('recorded_bound_exceeding_segments', 1), ('voltage_boundary_straddling_segments', 1)):
            self.assertFalse(gap.screen_passes({**ok, key: value}))
        self.assertFalse(gap.screen_passes({**ok, 'exception': {'current_ceiling_exceeded_in_saved_samples': True}}))


class CriteriaDocumentTests(unittest.TestCase):
    def test_document_mirrors_the_constants(self):
        text = CRITERIA.read_text()
        self.assertIn('model sensitivity only', text)
        for rail, value in gap.BASELINE_GAP_V.items():
            self.assertIn(f'**{value:.4f} V**', text)
        for label, rails in gap.labels().items():
            self.assertIn(f'| {label} |', text)
            for rail, (kind, shift) in rails.items():
                if kind == 'enabled-gated':
                    self.assertIn(f'shift +{shift:.4f} V', text)
        self.assertIn(gap.DISABLE_LINE[1], text)
        self.assertIn(gap.GATE_ON, text)
        self.assertIn('1e-5 V', text)
        self.assertIn('110–115 ms', text)
        self.assertIn('40–234.5 ms', text)
        self.assertEqual(gap.gap_line('{case}'), re.search(r'`(wrdata \{case\}-gap\.txt [^`]+)`', text).group(1))


class CollectTests(unittest.TestCase):
    def test_collect_includes_gap_ladders_without_vendor_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'work'
            for run in (work / 'ladder-a', work / 'gaps' / 'g20' / 'ladder-b'):
                (run / 'nom' / '0' / 'tracking').mkdir(parents=True)
                (run / 'nom' / '0' / 'lib').mkdir()
                (run / 'nom' / '0' / 'lib' / 'x.lib').write_text('vendor')
                (run / 'receipt.json').write_text('{}')
                (run / 'nom' / '0' / 'tracking' / 'nom.cir').write_text('deck')
                (run / 'nom' / '0' / 'tracking' / 'nom-gap.txt').write_text('1 2')
            hashes = ex.collect(work, Path(tmp) / 'evidence')
            self.assertIn('gaps/g20/ladder-b/nom/nom-gap.txt', hashes)
            self.assertIn('ladder-a/nom/nom.cir', hashes)
            self.assertFalse(any(k.endswith('.lib') for k in hashes))


if __name__ == '__main__':
    unittest.main()
