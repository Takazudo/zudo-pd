"""Fail-closed finalization controls; actual native proof is separate."""
import unittest
import tempfile
from unittest.mock import patch
import finalize_refill as finalizer
from pathlib import Path
from finalize_refill import validate_geometry, validate_drc
from test_staged_geometry import BOARD


class FinalizeTests(unittest.TestCase):
    def test_fill_only_stable_result(self):
        before=BOARD.encode();after=BOARD.replace('(xy 9 9)','(xy 8.99 9)').encode()
        validate_geometry(before,after,after,Path('/same'))
        validate_geometry(after,after,after,Path('/same'))

    def test_second_process_difference_rejected(self):
        with self.assertRaisesRegex(ValueError,'not byte-identical'):
            validate_geometry(BOARD.encode(),BOARD.encode(),(BOARD+'\n').encode(),Path('/same'))

    def test_nonfill_and_identity_changes_rejected(self):
        for old,new in [('(drill 0.2)','(drill 0.3)'),('(width 0.25)','(width 0.3)'),('(uuid "fp")','(uuid "different")')]:
            changed=BOARD.replace(old,new).encode()
            with self.subTest(change=new),self.assertRaises(ValueError):
                validate_geometry(BOARD.encode(),changed,changed,Path('/same'))

    def test_uuid_swaps_and_duplicates_rejected(self):
        swapped=BOARD.replace('(uuid "fp")','(uuid "temporary")').replace('(uuid "t")','(uuid "fp")').replace('(uuid "temporary")','(uuid "t")')
        with self.assertRaisesRegex(ValueError,'identity associations'):
            validate_geometry(BOARD.encode(),swapped.encode(),swapped.encode(),Path('/same'))
        duplicated=BOARD.replace('(uuid "t")','(uuid "fp")')
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate_geometry(BOARD.encode(),duplicated.encode(),duplicated.encode(),Path('/same'))

    def test_identical_child_nodes_remain_bound_to_their_parent(self):
        original=BOARD[BOARD.index(' (footprint'):BOARD.index('\n (segment')]
        first=original.replace('(pad "1"','(pad "1" (uuid "p1")')
        second=first.replace('(uuid "fp")','(uuid "fp2")').replace('"U1"','"U2"').replace('(at 10 20 90)','(at 20 20 90)').replace('(uuid "p1")','(uuid "p2")')
        before=BOARD.replace(original,first+'\n'+second)
        after=before.replace('(uuid "p1")','(uuid "temp")').replace('(uuid "p2")','(uuid "p1")').replace('(uuid "temp")','(uuid "p2")')
        with self.assertRaisesRegex(ValueError,'identity associations'):
            validate_geometry(before.encode(),after.encode(),after.encode(),Path('/same'))

    def test_midrun_native_context_change_refuses_adoption(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'input.kicad_pcb';source.write_text(BOARD)
            project=root/'board-b20-draft.kicad_pro';project.write_text('{}')
            for name in ['board-b20-draft.kicad_sch','fp-lib-table','sym-lib-table']:
                (root/name).write_text('original')
            stage=root/'stage';stage.mkdir();output=root/'output.kicad_pcb'
            def mutate(stage,number):
                if number==1:(root/'fp-lib-table').write_text('concurrent edit')
                return BOARD.encode(),['stub']
            with patch.object(finalizer.tempfile,'mkdtemp',return_value=str(stage)), patch.object(finalizer,'run_refill',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'context/checker changed'):
                    finalizer.finalize(source,output,project,root/'receipt.json')
            self.assertFalse(output.exists())
            self.assertEqual((root/'fp-lib-table').read_text(),'concurrent edit')
            self.assertEqual(project.read_text(),'{}')

    def test_only_specific_native_dispositions_accepted(self):
        report={'unconnected_items':[],'schematic_parity':[],'violations':[
            {'severity':'warning','type':'lib_footprint_mismatch','items':[{'description':'Footprint '+ref}]}
            for ref in ['J6','J7','J10','J11']]}
        validate_drc(report)
        report['violations'][0]['items'][0]['description']='Footprint U6'
        with self.assertRaises(ValueError):validate_drc(report)
        report['violations'][0]['severity']='error'
        with self.assertRaises(ValueError):validate_drc(report)
        report['unconnected_items']=[{}]
        with self.assertRaises(ValueError):validate_drc(report)


if __name__=='__main__':unittest.main()
