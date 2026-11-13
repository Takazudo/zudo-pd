import tempfile
from pathlib import Path
import unittest
from unittest import mock

import adv_rshunt_free as ar
from extract_reference import HERE, derive_decks, transform


class DeckTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(list(ar.derive_cases()), ['r10-adv', 'abstol-r10-adv'])

    def test_r10_is_the_pre_fallback_refined_deck_plus_the_output_lines(self):
        decks = derive_decks()['adv']
        refined_original = transform((HERE / 'tracking' / 'adv.cir').read_text(), 'adv')
        self.assertEqual(ar.derive_cases()['r10-adv'][1],
                         refined_original.replace('.endc', '\n'.join(decks['added_lines']) + '\n.endc'))

    def test_each_deck_changes_only_the_options_line(self):
        executed = derive_decks()['adv']['executed'].splitlines()
        for lbl, (_, text) in ar.derive_cases().items():
            varied = text.splitlines()
            changed = [(a, b) for a, b in zip(executed, varied) if a != b]
            self.assertEqual(len(executed), len(varied))
            self.assertEqual(len(changed), 1, lbl)
            self.assertIn('rshunt=1e10', changed[0][1])
            self.assertIn('itl4=200', changed[0][1])
            self.assertEqual('abstol=1e-8' in changed[0][1], lbl == 'abstol-r10-adv')

    def test_swap_refuses_an_ambiguous_option(self):
        with self.assertRaises(ValueError):
            ar.swap('rshunt=1e9 rshunt=1e9', 'rshunt=1e9', 'rshunt=1e10', 'x')


class AnalyzeTests(unittest.TestCase):
    def test_aborted_rows_carry_no_figures_and_complete_rows_are_compared(self):
        rails = {'+12': {'a': 1.0}, '+5': {'a': 1.0},
                 '-12': {'peak_slope_in_region_v_per_ms': 1.4690, 'peak_current_in_region_a': 0.2642}}
        def status(work, lbl):
            return {'status': 'ABORTED', 'abort': {'time_s': 0.1}} if lbl == 'r10-adv' else {'status': 'COMPLETE', 'run': 'x'}
        with mock.patch.object(ar, 'status', side_effect=status), \
                mock.patch.object(ar.vx, 'pinned_status', return_value={'status': 'COMPLETE', 'run': 'p'}), \
                mock.patch.object(ar.vx, 'metrics', return_value=rails):
            out = ar.analyze('/w')
        self.assertEqual(out['status'], {'r10-adv': 'ABORTED', 'abstol-r10-adv': 'COMPLETE'})
        self.assertNotIn('rails', out['decks']['r10-adv'])
        d1 = out['decks']['abstol-r10-adv']['minus12_d1']
        self.assertAlmostEqual(d1['peak_current_in_region_a']['relative_to_recorded'], 0.2642 / 0.265259332 - 1)
        self.assertIn('labelled, not pinned', out['decks']['abstol-r10-adv']['setting'])
        self.assertNotIn('pass', str(out).lower().replace('compass', ''))

    def test_prepare_writes_both_decks(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'lib').mkdir()
            (work / 'tracking').mkdir()
            (work / 'tracking' / '.spiceinit').write_text('s')
            manifest = ar.prepare(work)
            for lbl in ('r10-adv', 'abstol-r10-adv'):
                deck = work / 'r10' / lbl / 'tracking' / 'adv.cir'
                self.assertEqual(ar.gap.sha(deck.read_bytes()), manifest['labels'][lbl]['adv']['deck_sha256'])


if __name__ == '__main__':
    unittest.main()
