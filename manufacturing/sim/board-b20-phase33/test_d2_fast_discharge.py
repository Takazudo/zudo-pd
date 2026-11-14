import json
import math
import re
import tempfile
from pathlib import Path
import unittest

import d2_fast_discharge as fd


def waveform(t_disc=1.03e-3, tau=(1e-4, 5e-5, 2.2e-4), fire=1.06e-3, start=(12.48, 5.2, -12.37)):
    """Synthetic rows in VECTORS order (tau for +12, +5, -12): rails decay exponentially from the firing time; pass currents stop at t_disc."""
    rows = []
    for k in range(0, 3001):
        t = k * 1e-6
        on = t >= fire
        v = [s * (math.exp(-(t - fire) / tc) if on else 1.0) for s, tc in zip(start, tau)]
        enn = 5.0 if t >= 1e-3 else 0.0
        ip = [0.5 if t < t_disc else 0.0] * 3
        idis = [abs(x) / r if on else 0.0 for x, r in zip(v, (0.5, 0.5, 1.5))]
        rows.append((t, v[0], v[1], v[2], enn, *ip, *idis, 0.0))
    return rows


class DeckTests(unittest.TestCase):
    def test_162_labels_from_9_banks_and_18_load_corners(self):
        cases = fd.derive_cases()
        self.assertEqual(len(cases), 162)
        self.assertEqual(len({c[0] for c in cases.values()}), 9)

    def test_deck_carries_the_candidate_and_the_corner_loads(self):
        _, corner, text = fd.derive_cases()['ceil-mzm']
        self.assertEqual(corner, {'+12': 'maximum', '-12': '0', '+5': 'maximum'})
        self.assertIn('RXD12 d12a d12b 0.5', text)
        self.assertIn('RXDN dna dnb 1.5', text)
        self.assertIn('RXD5 d5a d5b 0.5', text)
        self.assertRegex(text, r'RL12 p12_out 0 5\.71429')
        self.assertRegex(text, r'RL5 p5_out 0 10\b')
        self.assertNotIn('RLN ', text)
        self.assertIn('CL12 p12_out cl12 0.00018', text)
        self.assertIn('rshunt=1e10', text)
        self.assertEqual(len(re.findall(r'^wrdata nomR\.dat (.*)$', text, re.M)[0].split()), 11)

    def test_prepare_writes_each_deck_with_the_lib(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'lib').mkdir()
            (work / 'lib' / 'm.lib').write_text('x')
            (work / 'tracking').mkdir()
            (work / 'tracking' / '.spiceinit').write_text('s')
            manifest = fd.prepare(work)
            self.assertEqual(len(manifest['labels']), 162)
            deck = work / 'd2fd' / 'ceil-zzz' / 'tracking' / 'nomR.cir'
            self.assertEqual(fd.gap.sha(deck.read_bytes()), manifest['labels']['ceil-zzz']['deck_sha256'])
            self.assertTrue((work / 'd2fd' / 'ceil-zzz' / 'lib' / 'm.lib').exists())

    def test_calculation_passes_every_bank(self):
        self.assertEqual(fd.calc()['banks_failing'], [])


class ReadTests(unittest.TestCase):
    def test_matched_decay_after_disconnect_passes(self):
        out = fd.read(waveform())
        self.assertTrue(out['pass'], out['rows'])
        self.assertAlmostEqual(out['discharge_onset_ms'], 0.06, places=3)

    def test_discharge_before_disconnect_fails(self):
        out = fd.read(waveform(t_disc=1.08e-3))
        self.assertFalse(out['rows']['disconnect_before_discharge'])

    def test_minus12_leaving_first_fails_rvee(self):
        out = fd.read(waveform(tau=(4e-4, 1e-4, 5e-5)))
        self.assertFalse(out['rows']['rvee'])
        self.assertFalse(out['pass'])


class RecordTests(unittest.TestCase):
    def test_attempt2_record_is_fail_on_rvee_only(self):
        rec = json.loads((Path(__file__).parent / 'd2-fast-discharge-attempt2-20261114.json').read_text())
        self.assertEqual((rec['reading'], rec['complete'], len(rec['failing'])), ('FAIL (SIM)', 92, 8))
        for lbl in rec['failing']:
            rows = rec['cases'][lbl]['rows']
            self.assertEqual([k for k, ok in rows.items() if not ok], ['rvee'])
            self.assertTrue(lbl.startswith('phnl'))


if __name__ == '__main__':
    unittest.main()
