"""Bundle-audit regressions for the completed D1 OSC-bank and ceiling-corners artifacts (synthetic; no simulation)."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import audit_d1_bundle as audit

HERE = Path(__file__).resolve().parent
REV = '0' * 40
LIBS = {'lib/opax187.lib': 'a' * 64, 'lib/csd18543q3a_ngspice.lib': 'b' * 64}
SPICEINIT = 'c' * 64
DECK = '* deck\n.options method=trap abstol=1e-9 rshunt=1e10\n.end\n'


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def runner_receipt(deck, status):
    return {'image': audit.IMAGE, 'platform': 'linux/amd64', 'variant_policy': 'original-only', 'source_dirty': False,
            'solver_version_output': f'** {audit.SOLVER} : Circuit level simulation program', 'solver_version_returncode': 0,
            'input_sha256': {'.spiceinit': SPICEINIT, 'nom.cir': sha(deck), **LIBS}, 'status': status,
            'cases': {'nom': {'status': status, 'attempts': [{'deck_sha256': sha(deck)}]}}}


def bundle(path, tamper=None):
    """A minimal OSC-bank-shaped bundle: one pinned ABORTED label, its abstol variant COMPLETE."""
    variant = DECK.replace('abstol=1e-9', 'abstol=1e-8')
    result = {'diagnostic': 'OSC-bank baseline (osc-bank-criteria.md); measures only, judges nothing',
              'decks': {'nom-nom': {'pinned': 'ABORTED', 'abort': {'time_s': 0.002}, 'variant_abstol': 'COMPLETE',
                                    'measured_under': 'matched variant abstol (labelled, not pinned)'}},
              'unknown': [], 'variant_cross_check': {'abstol': {'pinned': 'ABORTED', 'variant': 'COMPLETE'}}}
    files = {
        'identity.json': json.dumps({'status': 'REPRODUCED', 'source_revision': REV, 'solver_identity_matches': True,
                                     'cases': {'nom': {'matches': {'executed_deck': True}}}}),
        'manifest.json': json.dumps({'source_revision': REV, 'vendor_sha256': {**LIBS, 'x.zip': 'd' * 64},
                                     'spiceinit_sha256': SPICEINIT}),
        'bank-manifest.json': json.dumps({'criteria': 'osc-bank-criteria.md',
                                          'labels': {'nom-nom': {'nom': {'deck_sha256': sha(DECK)}}}}),
        'osc-bank.json': json.dumps(result),
        'bank/nom-nom/ladder-a/receipt.json': json.dumps(runner_receipt(DECK, 'FAILED')),
        'bank/nom-nom/ladder-a/nom/nom.cir': DECK,
        'bank/v-abstol-nom-nom/ladder-b/receipt.json': json.dumps(runner_receipt(variant, 'COMPLETE')),
        'bank/v-abstol-nom-nom/ladder-b/nom/nom.cir': variant,
        'ladder-c/receipt.json': json.dumps({'status': 'COMPLETE'}),
    }
    hashes = {k: sha(v) for k, v in files.items()}
    if tamper:
        tamper(files, hashes)
    with zipfile.ZipFile(path, 'w') as zf:
        for name, data in files.items():
            zf.writestr(name, data)
        zf.writestr('hashes.json', json.dumps(hashes, indent=2, sort_keys=True) + '\n')
    retained = Path(path).with_name('retained.json')
    retained.write_text(files['osc-bank.json'])
    digest = sha(Path(path).read_bytes())
    meta = {'run': {'id': 1, 'run_attempt': 1, 'head_sha': REV, 'conclusion': 'success'},
            'artifact': {'id': 2, 'digest': f'sha256:{digest}', 'size_in_bytes': Path(path).stat().st_size}}
    return meta, retained


class BundleAuditTests(unittest.TestCase):
    def run_audit(self, tamper=None, meta_edit=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.zip'
            meta, retained = bundle(path, tamper)
            if meta_edit:
                meta_edit(meta)
            return audit.audit(path, meta, 'osc_bank', retained)

    def test_consistent_bundle_verifies_and_keeps_tracks_apart(self):
        receipt = self.run_audit()
        self.assertEqual(receipt['audit_status'], 'VERIFIED', receipt['problems'])
        rows = receipt['diagnostic']['executed_decks']
        self.assertEqual(rows['nom-nom']['track'], 'pinned')
        self.assertEqual(rows['v-abstol-nom-nom']['track'], 'matched variant abstol (labelled)')
        self.assertTrue(rows['v-abstol-nom-nom']['variant_option_only'])
        self.assertEqual(receipt['electrical_acceptance'], 'NOT ESTABLISHED')

    def test_archive_digest_mismatch_fails(self):
        receipt = self.run_audit(meta_edit=lambda m: m['artifact'].update(digest='sha256:' + 'e' * 64))
        self.assertEqual(receipt['audit_status'], 'FAILED VERIFICATION')

    def test_member_hash_mismatch_fails(self):
        receipt = self.run_audit(tamper=lambda f, h: h.update({'osc-bank.json': 'f' * 64}))
        self.assertIn('osc-bank.json', ' '.join(receipt['problems']))

    def test_missing_member_fails(self):
        receipt = self.run_audit(tamper=lambda f, h: h.update({'bank/nom-nom/ladder-a/nom/nom.dat': 'f' * 64}))
        self.assertIn('missing_from_archive', ' '.join(receipt['problems']))

    def test_vendor_model_bytes_fail(self):
        def add_lib(files, hashes):
            files['bank/nom-nom/ladder-a/nom/lib/opax187.lib'] = 'model'
            hashes['bank/nom-nom/ladder-a/nom/lib/opax187.lib'] = sha('model')
        receipt = self.run_audit(tamper=add_lib)
        self.assertIn('vendor_model_members', ' '.join(receipt['problems']))

    def test_variant_deck_with_another_change_fails(self):
        def edit(files, hashes):
            name = 'bank/v-abstol-nom-nom/ladder-b/nom/nom.cir'
            files[name] = files[name].replace('trap', 'gear')
            hashes[name] = sha(files[name])
        receipt = self.run_audit(tamper=edit)
        self.assertIn('v-abstol-nom-nom', ' '.join(receipt['problems']))

    def test_different_solver_model_fails(self):
        def edit(files, hashes):
            name = 'bank/nom-nom/ladder-a/receipt.json'
            r = json.loads(files[name])
            r['input_sha256']['lib/opax187.lib'] = '0' * 64
            files[name] = json.dumps(r)
            hashes[name] = sha(files[name])
        receipt = self.run_audit(tamper=edit)
        self.assertIn("runner identity mismatch ['models']", ' '.join(receipt['problems']))

    def edit_json(self, name, change):
        def tamper(files, hashes):
            data = json.loads(files[name])
            change(data)
            files[name] = json.dumps(data)
            hashes[name] = sha(files[name])
        return self.run_audit(tamper=tamper)

    def test_identity_not_reproduced_fails(self):
        receipt = self.edit_json('identity.json', lambda d: d.update(status='NOT REPRODUCED'))
        self.assertIn('identity control did not reproduce', receipt['problems'])

    def test_identity_from_another_revision_fails(self):
        receipt = self.edit_json('identity.json', lambda d: d.update(source_revision='1' * 40))
        self.assertIn('identity source revision differs from the run head', receipt['problems'])

    def test_pinned_row_without_a_pinned_deck_fails(self):
        receipt = self.edit_json('osc-bank.json', lambda d: d['decks']['nom-nom'].update(pinned='NOT RUN'))
        self.assertIn('pinned row', ' '.join(receipt['problems']))

    def test_manifest_label_never_executed_fails(self):
        receipt = self.edit_json('bank-manifest.json',
                                 lambda d: d['labels'].update({'hi-nom': {'nom': {'deck_sha256': sha('x')}}}))
        self.assertIn('do not cover the manifest labels', ' '.join(receipt['problems']))

    def test_variant_row_without_a_completed_variant_deck_fails(self):
        receipt = self.edit_json('bank/v-abstol-nom-nom/ladder-b/receipt.json', lambda d: d.update(status='FAILED'))
        self.assertIn('variant abstol row has no completed executed deck', ' '.join(receipt['problems']))

    def test_retained_result_must_be_the_artifact_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.zip'
            meta, retained = bundle(path)
            retained.write_text(retained.read_text() + ' ')
            receipt = audit.audit(path, meta, 'osc_bank', retained)
        self.assertIn('retained result differs from the artifact result', receipt['problems'])

    def test_rerun_attempt_fails(self):
        receipt = self.run_audit(meta_edit=lambda m: m['run'].update(run_attempt=2))
        self.assertIn('first attempt', ' '.join(receipt['problems']))


class RetainedRecordTests(unittest.TestCase):
    def test_retained_receipts_check(self):
        self.assertEqual(audit.check(), 0)

    def test_retained_receipts_bind_the_identified_runs(self):
        expected = {'osc_bank': (43221578569, '8daa87f988d99abb02270827b47a4bb905177df9', 13947214643,
                                 'c26999933ee8bcae4aee79220846a1a24e9f627be58ac22860c76f8f42d173e7'),
                    'ceiling_corners': (43232694170, '391992840046121554320a4c58d3a5cbf2474c89', 13953060177,
                                        '026602ed06555b1191accf1e4042c3c515cfc9e6f79df825127013cc4c3fd3fd')}
        for diagnostic, (run, rev, artifact, digest) in expected.items():
            receipt = json.loads((HERE / audit.RECEIPTS[diagnostic][0]).read_text())
            self.assertEqual((receipt['run']['id'], receipt['run']['head_sha'], receipt['run']['run_attempt']), (run, rev, 1))
            self.assertEqual((receipt['artifact']['id'], receipt['artifact']['digest']), (artifact, f'sha256:{digest}'))
            self.assertEqual(receipt['identity_control']['source_revision'], rev)
            self.assertTrue(receipt['deck_derivation']['all_match'])

    def test_no_pinned_cross_check_was_formed(self):
        # The criteria expected a pinned nom to compare against; both runs aborted it, so no difference exists.
        for diagnostic in audit.RECEIPTS:
            receipt = json.loads((HERE / audit.RECEIPTS[diagnostic][0]).read_text())
            check = receipt['diagnostic']['summary']['variant_cross_check']
            self.assertEqual(check, {'abstol': {'pinned': 'ABORTED', 'variant': 'COMPLETE'}})


if __name__ == '__main__':
    unittest.main()
