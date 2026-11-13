import tempfile
from pathlib import Path
import unittest
from unittest import mock

from extract_reference import derive_decks
import variant_cross_check as vx


def metrics(slope5=0.954850860, current5=0.114510041, slope12=1.474778, current12=0.265259332):
    def rail(slope, current):
        return {'region_v': 0.45, 'peak_slope_in_region_v_per_ms': slope, 'peak_current_in_region_a': current,
                'peak_current_a': current, 'charge_in_region_c': 1e-5}
    return {'+12': rail(0.3, 0.05), '+5': rail(slope5, current5), '-12': rail(slope12, current12)}


class DeckTests(unittest.TestCase):
    def test_labels_and_the_inapplicable_adv_rshunt(self):
        cases, skipped = vx.derive_cases()
        self.assertEqual(list(cases), ['abstol-nom', 'abstol-adv', 'rshunt-nom'])
        self.assertEqual(list(skipped), ['rshunt-adv'])

    def test_each_deck_differs_from_the_executed_deck_by_one_option_only(self):
        executed = {name: deck['executed'] for name, deck in derive_decks().items()}
        edits = {'abstol': ('abstol=1e-9', 'abstol=1e-8'), 'rshunt': ('rshunt=1e10', 'rshunt=1e9')}
        for lbl, (name, variant, text) in vx.derive_cases()[0].items():
            old, new = edits[variant]
            base = executed[name].splitlines()
            varied = text.splitlines()
            self.assertEqual(len(base), len(varied))
            changed = [(a, b) for a, b in zip(base, varied) if a != b]
            self.assertEqual(len(changed), 1, lbl)
            self.assertEqual(changed[0][0].replace(old, new), changed[0][1])
            self.assertTrue(changed[0][0].startswith('.options '))
            self.assertIn('itl4=200', changed[0][1])

    def test_prepare_writes_decks_under_xcheck_with_the_pinned_lib(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'lib').mkdir()
            (work / 'lib' / 'm.lib').write_text('x')
            (work / 'tracking').mkdir()
            (work / 'tracking' / '.spiceinit').write_text('s')
            manifest = vx.prepare(work)
            self.assertEqual(set(manifest['labels']), {'abstol-nom', 'abstol-adv', 'rshunt-nom'})
            for lbl, entry in manifest['labels'].items():
                (name, info), = entry.items()
                deck = work / 'xcheck' / lbl / 'tracking' / f'{name}.cir'
                self.assertEqual(vx.gap.sha(deck.read_bytes()), info['deck_sha256'])
                self.assertTrue((work / 'xcheck' / lbl / 'lib' / 'm.lib').exists())


class ReadingTests(unittest.TestCase):
    def test_identical_rows_are_comparable(self):
        reading, checked = vx.reading(vx.compare(metrics(), metrics()))
        self.assertEqual(reading, 'COMPARABLE')
        self.assertEqual(len(checked), 4)

    def test_the_bound_is_inclusive_and_read_on_both_exception_rails(self):
        within = metrics(current12=0.265259332 * (1 + 0.99e-4))
        self.assertEqual(vx.reading(vx.compare(metrics(), within))[0], 'COMPARABLE')
        over = metrics(slope5=0.954850860 * (1 + 1.01e-4))
        self.assertEqual(vx.reading(vx.compare(metrics(), over))[0], 'NOT COMPARABLE')

    def test_plus12_is_reported_but_not_read(self):
        a, b = metrics(), metrics()
        b['+12']['peak_slope_in_region_v_per_ms'] = 9.0
        diff = vx.compare(a, b)
        self.assertEqual(vx.reading(diff)[0], 'COMPARABLE')
        self.assertAlmostEqual(diff['+12']['peak_slope_in_region_v_per_ms']['difference'], 8.7)

    def test_a_missing_read_quantity_is_not_comparable(self):
        b = metrics()
        b['-12']['peak_slope_in_region_v_per_ms'] = None
        self.assertEqual(vx.reading(vx.compare(metrics(), b))[0], 'NOT COMPARABLE')


class PairTests(unittest.TestCase):
    def run_pair(self, pinned, varied):
        with mock.patch.object(vx, 'pinned_status', return_value=pinned), \
                mock.patch.object(vx, 'variant_status', return_value=varied), \
                mock.patch.object(vx, 'metrics', side_effect=lambda source, name: metrics()):
            return vx.pair('/w', 'abstol-nom', 'nom', 'abstol')

    def test_aborted_variant_is_not_formed_and_keeps_its_abort(self):
        row = self.run_pair({'status': 'COMPLETE', 'run': 'p'}, {'status': 'ABORTED', 'abort': {'time_s': 0.1}})
        self.assertEqual(row['reading'], 'NOT FORMED')
        self.assertEqual(row['variant_abort'], {'time_s': 0.1})
        self.assertNotIn('difference', row)

    def test_aborted_pinned_is_not_formed(self):
        row = self.run_pair({'status': 'ABORTED', 'abort': None}, {'status': 'COMPLETE', 'run': 'v'})
        self.assertEqual(row['reading'], 'NOT FORMED')

    def test_complete_pair_is_read(self):
        row = self.run_pair({'status': 'COMPLETE', 'run': 'p'}, {'status': 'COMPLETE', 'run': 'v'})
        self.assertEqual(row['reading'], 'COMPARABLE')

    def test_check_run_tolerates_only_complete_or_aborted(self):
        with mock.patch.object(vx, 'variant_status', return_value={'status': 'RUN FAILED'}):
            self.assertEqual(vx.check_run('/w', 'rshunt-nom'), {'nom': 'RUN FAILED'})
        with mock.patch.object(vx, 'variant_status', return_value={'status': 'ABORTED'}):
            self.assertEqual(vx.check_run('/w', 'abstol-adv'), {})


class CollectTests(unittest.TestCase):
    def test_collect_picks_up_cross_check_runs(self):
        import extract_reference as ex
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            run = work / 'xcheck' / 'abstol-nom' / 'ladder-x'
            run.mkdir(parents=True)
            (run / 'receipt.json').write_text('{}')
            hashes = ex.collect(work, work / 'evidence')
            self.assertIn('xcheck/abstol-nom/ladder-x/receipt.json', hashes)


if __name__ == '__main__':
    unittest.main()
