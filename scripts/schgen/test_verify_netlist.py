"""Regression coverage for KiCad's net-label slash encoding."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from verify_netlist import read_netlist_nets, verify


class NetlistNamesTest(unittest.TestCase):
    def read(self, names):
        entries = ''.join(
            f'(net (name "{name}") (node (ref R1) (pin 1)))'
            for name in names
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.net'
            path.write_text(f'(export (nets {entries}))')
            return read_netlist_nets(path)

    def test_native_slash_encoding_keeps_membership_strict(self):
        actual = self.read(['{slash}DC-DC Conversion{slash}+13.5V OUT'])
        spec = SimpleNamespace(NETS={'/DC-DC Conversion/+13.5V OUT': ['R1.1']}, NO_CONNECT=[])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(verify(spec, actual))
            self.assertFalse(verify(spec, {'/DC-DC Conversion/+13.5V OUT': {'R1.2'}}))
            self.assertFalse(verify(spec, {'/DC-DC Conversion/+13.6V OUT': {'R1.1'}}))

    def test_colliding_decoded_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate net name'):
            self.read(['a{slash}b', 'a/b'])


if __name__ == '__main__':
    unittest.main()
