"""Geometry and identity regressions for polarity-reference.py.

run: python3 -m unittest discover -s scripts/pcb/pd20-order -p 'test_*.py'
"""
import importlib.util, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('polref', HERE / 'polarity-reference.py')
polref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(polref)
P15 = ROOT / 'manufacturing/releases/corner-support-review/board-p15'
PD20 = ROOT / 'manufacturing/releases/pd20-prototype-review'


def rows(release_board, origin):
    name = release_board.name
    return {r['ref']: r for r in polref.board_rows(release_board / 'source' / f'{name}.kicad_pcb',
                                                    release_board / 'cpl.csv', origin)}


class PolarityReference(unittest.TestCase):
    def test_reproduces_the_independent_p15_placement_checklist(self):
        # manufacturing/verification/p15-order-refresh-20261120/placement-checklist.md (KiCad y = -CPL Mid Y)
        got = rows(P15, (0, 0))
        self.assertEqual((got['D5']['pad1_net'], got['D5']['pad1_cpl_mm']), ('VBUS_IN', [20.45, -10.08]))
        self.assertEqual((got['D9']['pad1_net'], got['D9']['pad1_cpl_mm']), ('VDD_LOC', [17.325, -24.95]))
        self.assertEqual((got['U1']['pad1_net'], got['U1']['pad1_cpl_mm']), ('CC1DB', [12.978, -21.288]))

    def test_pd20_bottom_and_top_identities(self):
        b20 = rows(PD20 / 'board-b20-draft', (0.0, 85.0))
        self.assertEqual(b20['D3']['pad1_net'], 'C_SW')
        self.assertEqual((b20['D4']['side'], b20['D4']['pad1_net']), ('Bottom', 'M12_DG'))
        self.assertEqual(sum(r['side'] == 'Bottom' for r in b20.values()), 9)
        self.assertEqual({r for r in b20 if r.startswith('C')}, {'C1', 'CAF1', 'CBF1', 'CCF1', 'CSO3'})
        p = rows(PD20 / 'board-p', (0, 0))
        self.assertIn('C3', p)
        self.assertEqual((p['D12']['side'], p['D12']['pad1_net']), ('Bottom', 'DISCH'))


if __name__ == '__main__':
    unittest.main()
