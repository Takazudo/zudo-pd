import json
import tempfile
import unittest
from pathlib import Path

import d2_fast_discharge as fd
import d2_sequenced as sq

HERE = Path(__file__).parent


class DeckTests(unittest.TestCase):
    def test_243_labels_from_9_banks_and_27_load_corners(self):
        cases = sq.derive_cases()
        self.assertEqual(len(cases), 243)
        self.assertEqual({c[1]['+5'] for c in cases.values()}, {'0', 'planning', 'maximum'})

    def test_deck_changes_only_the_sequencer_firing_q54_and_loads(self):
        _, _, text = sq.derive_cases()['ceil-zzp']
        self.assertIn('CDGN dgn m12_out 68n', text)
        self.assertIn('BHOLD dgn m12_out', text)
        self.assertIn('BQ54 disc dgx', text)
        self.assertNotIn('SWQ54', text)
        self.assertRegex(text, r'RL5 p5_out 0 22\.2916\n')
        self.assertIn('RXDN dna dnb 1.5', text)
        self.assertIn('rshunt=1e10', text)
        base = fd.deck('x', fd.CEILING_BANK, {'+12': '0', '-12': '0', '+5': '0'})
        self.assertEqual(len(base.splitlines()), len(sq.deck('x', fd.CEILING_BANK,
                                                                  {'+12': '0', '-12': '0', '+5': '0'}).splitlines()))

    def test_prepare_writes_under_d2sq(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'lib').mkdir()
            (work / 'lib' / 'm.lib').write_text('x')
            (work / 'tracking').mkdir()
            (work / 'tracking' / '.spiceinit').write_text('s')
            manifest = sq.prepare(work)
            self.assertEqual(len(manifest['labels']), 243)
            self.assertTrue((work / 'd2sq' / 'phnlfl-zzz' / 'tracking' / 'nomR.cir').exists())


class CalcTests(unittest.TestCase):
    def test_sequencer_holds_minus12_until_plus12_is_gone(self):
        caps = fd.banks()['phnlfl']
        corner = {'+12': '0', '-12': '0', '+5': '0'}
        fire = {'+12': 155e-6, '-12': 0.0, '+5': 163e-6}
        self.assertFalse(sq.simulate(caps, corner, fire, sequenced=False)['rvee'])
        out = sq.simulate(caps, corner, fire)
        self.assertTrue(out['pass'])
        self.assertGreater(out['level_s']['-12'], out['level_s']['+12'])

    def test_late_minus12_still_fails_the_other_direction(self):
        caps = fd.banks()['plnhfl']
        fire = {'+12': 120e-6, '-12': 300e-6, '+5': 120e-6}
        self.assertFalse(sq.simulate(caps, {'+12': '0', '-12': '0', '+5': '0'}, fire)['rvee'])

    def test_recorded_calculation_has_no_failures(self):
        rec = json.loads((HERE / 'd2-sequenced-calc-20261114.json').read_text())
        self.assertEqual((rec['cases'], rec['failing']), (10935, 0))


if __name__ == '__main__':
    unittest.main()
