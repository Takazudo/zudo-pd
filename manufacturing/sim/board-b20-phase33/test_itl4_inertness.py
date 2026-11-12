import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import gap_sensitivity as gap
import itl4_inertness as it
import t2_rev2


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


DECK = '* deck\n.options method=trap reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 rshunt=1e10\n.end\n'


class ReferenceTests(unittest.TestCase):
    def test_reference_covers_the_recorded_pinned_set(self):
        ref = it.reference()
        self.assertEqual(ref['source']['workflow_run'], 43187732133)
        self.assertEqual(len(ref['decks']), 35)
        states = [d['status'] for d in ref['decks'].values()]
        self.assertEqual((states.count('COMPLETE'), states.count('ABORTED')), (13, 22))
        for key, d in ref['decks'].items():
            self.assertEqual(d['outputs'] is None, d['status'] == 'ABORTED', key)
            if d['outputs']:
                self.assertFalse(any(k.endswith(('.log', '.cir')) for k in d['outputs']), key)
        self.assertEqual(list(it.decks_by_label(ref))[0], 'run')

    def test_derived_rev2_decks_match_the_record(self):
        ref = it.reference()['decks']
        for label, decks in t2_rev2.derive_cases().items():
            for name, text in decks.items():
                self.assertEqual(sha(text), ref[f'{label}/{name}']['deck_sha256'], f'{label}/{name}')
                self.assertEqual(text.count(it.PINNED), 1)


class PrepareTests(unittest.TestCase):
    def tree(self, root, label):
        src = it.source_root(root, label)
        (src / 'tracking').mkdir(parents=True)
        (src / 'lib').mkdir()
        (src / 'tracking' / '.spiceinit').write_text('init')
        (src / 'tracking' / 'nom.cir').write_text(DECK)

    def test_only_itl4_changes(self):
        self.assertEqual(it.raise_itl4(DECK), DECK.replace('itl4=200', 'itl4=1000'))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            it.raise_itl4(DECK.replace('itl4=200', ''))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            it.raise_itl4(DECK + DECK)

    def test_prepare_copies_and_raises(self):
        ref = {'source': {}, 'decks': {'t2/nom': {'status': 'COMPLETE', 'deck_sha256': sha(DECK), 'outputs': {}}}}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(it, 'reference', return_value=ref):
            self.tree(Path(tmp), 't2')
            manifest = it.prepare(tmp)
            out = Path(tmp) / 'itl4' / 't2' / 'tracking' / 'nom.cir'
            self.assertIn('itl4=1000', out.read_text())
            self.assertTrue((Path(tmp) / 'itl4' / 't2' / 'lib').is_dir())
            self.assertEqual(manifest['labels']['t2']['nom']['pinned_deck_sha256'], sha(DECK))

    def test_prepare_refuses_a_deck_that_differs_from_the_record(self):
        ref = {'source': {}, 'decks': {'t2/nom': {'status': 'COMPLETE', 'deck_sha256': sha('other'), 'outputs': {}}}}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(it, 'reference', return_value=ref):
            self.tree(Path(tmp), 't2')
            with self.assertRaisesRegex(ValueError, 'differs from the recorded deck'):
                it.prepare(tmp)

    def test_the_baseline_pair_comes_from_the_work_tree(self):
        self.assertEqual(it.source_root('/w', 'run'), Path('/w'))
        self.assertEqual(it.source_root('/w', 'hot'), Path('/w/t2/hot'))


class AnalyzeTests(unittest.TestCase):
    REF = {'source': {'workflow_run': 1}, 'decks': {
        'run/nom': {'status': 'COMPLETE', 'deck_sha256': 'x', 'outputs': {'nom.dat': 'a', 'nom-ref.txt': 'b'}},
        't2/adv': {'status': 'ABORTED', 'deck_sha256': 'y', 'outputs': None},
        'hot/nom': {'status': 'ABORTED', 'deck_sha256': 'z', 'outputs': None}}}

    def run_with(self, states, got):
        def status(root, name):
            return {'status': states[f'{Path(root).name}/{name}'], 'run': Path('r'), 'abort': {'cause': 'x'}}
        with mock.patch.object(it, 'reference', return_value=self.REF), \
                mock.patch.object(gap, 'case_status', side_effect=status), \
                mock.patch.object(it, 'outputs', return_value=got):
            return it.analyze('/w')

    def test_inert_when_every_completing_deck_is_identical(self):
        out = self.run_with({'run/nom': 'COMPLETE', 't2/adv': 'COMPLETE', 'hot/nom': 'ABORTED'},
                            {'nom.dat': 'a', 'nom-ref.txt': 'b'})
        self.assertEqual(out['verdict'], 'INERT')
        self.assertEqual(out['rescued'], ['t2/adv'])
        self.assertEqual(out['still_aborting'], ['hot/nom'])

    def test_any_byte_difference_is_not_inert(self):
        out = self.run_with({'run/nom': 'COMPLETE', 't2/adv': 'ABORTED', 'hot/nom': 'ABORTED'},
                            {'nom.dat': 'a', 'nom-ref.txt': 'changed'})
        self.assertEqual(out['verdict'], 'NOT INERT')
        self.assertEqual(out['completing_decks']['run/nom']['difference'], ['nom-ref.txt'])

    def test_a_missing_output_is_a_difference(self):
        out = self.run_with({'run/nom': 'COMPLETE', 't2/adv': 'ABORTED', 'hot/nom': 'ABORTED'}, {'nom.dat': 'a'})
        self.assertEqual(out['verdict'], 'NOT INERT')

    def test_a_completing_deck_that_now_aborts_is_not_inert(self):
        out = self.run_with({'run/nom': 'ABORTED', 't2/adv': 'ABORTED', 'hot/nom': 'ABORTED'}, {})
        self.assertEqual(out['verdict'], 'NOT INERT')

    def test_a_run_failure_leaves_it_undetermined(self):
        out = self.run_with({'run/nom': 'RUN FAILED', 't2/adv': 'ABORTED', 'hot/nom': 'ABORTED'}, {})
        self.assertEqual(out['verdict'], 'NOT DETERMINED')
        self.assertEqual(out['run_failed'], ['run/nom'])


class AbortDetailTests(unittest.TestCase):
    def test_node_named_and_unrecorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            log, dat = Path(tmp) / 'a.log', Path(tmp) / 'a.dat'
            log.write_text('Reference value :  2.47650e-01doAnalyses: TRAN:  Timestep too small; time = 0.24765, '
                           'timestep = 2.5e-18: trouble with node "p12_g"\n\nrun simulation(s) aborted\n')
            dat.write_text(' 0.0 1.0 0.0 2.0\n 0.1 3.0 0.1 4.0\n\n')
            d = gap.abort_detail(log, dat)
            self.assertEqual((d['time_s'], d['node'], d['cause']), (0.24765, 'p12_g', 'node named'))
            self.assertEqual(d['last_sample'], {'time_s': 0.1, 'values': [3.0, 4.0]})
            log.write_text('doAnalyses: TRAN:  Timestep too small; time = 0.00199188, timestep = 2.5e-18: '
                           'cause unrecorded.\n')
            d = gap.abort_detail(log)
            self.assertEqual((d['node'], d['cause']), (None, 'unrecorded (ngspice named no node)'))
            log.write_text('nothing\n')
            self.assertEqual(gap.abort_detail(log)['cause'], 'no abort line found')


class CriteriaTests(unittest.TestCase):
    def test_criteria_file_states_the_rule(self):
        text = (it.HERE / 'itl4-inertness-criteria.md').read_text()
        for phrase in ('byte-identical', 'NOT INERT', 'not a verdict run', 'itl4=1000', '43187732133'):
            self.assertIn(phrase, text)


if __name__ == '__main__':
    unittest.main()
