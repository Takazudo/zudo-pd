"""Power declarations must match the exact net and position, not merely #FLG syntax."""
import copy
import pathlib
import tempfile
import unittest

import schgen_core
import test_spec_smoke
import verify_geometry


class PowerFlagGeometryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.spec = type('Spec', (), {k: copy.deepcopy(v) for k, v in vars(test_spec_smoke).items() if k.isupper()})
        self.spec.OUT = str(pathlib.Path(self.directory.name) / 'flags.kicad_sch')
        self.spec.ERC_POWER_FLAGS = {'SMOKE_A': (38.1, 76.2)}
        schgen_core.generate(self.spec)

    def test_declared_flag_is_checked(self):
        self.assertEqual(verify_geometry.run_check(self.spec, self.spec.OUT), [])
        self.spec.ERC_POWER_FLAGS = {'SMOKE_B': (38.1, 76.2)}
        self.assertTrue(any('#FLG001.1' in error for error in verify_geometry.run_check(self.spec, self.spec.OUT)))

    def test_wrong_position_and_undeclared_flags_fail(self):
        self.spec.ERC_POWER_FLAGS = {'SMOKE_A': (40.64, 76.2)}
        self.assertTrue(any('position differs' in error for error in verify_geometry.run_check(self.spec, self.spec.OUT)))
        self.spec.ERC_POWER_FLAGS = {}
        self.assertTrue(any('#FLG001.1' in error for error in verify_geometry.run_check(self.spec, self.spec.OUT)))

    def test_unknown_flagged_net_is_rejected_by_generator(self):
        self.spec.ERC_POWER_FLAGS = {'NO_SUCH_NET': (38.1, 76.2)}
        with self.assertRaises(schgen_core.SchgenError):
            schgen_core.generate(self.spec)


if __name__ == '__main__':
    unittest.main()
