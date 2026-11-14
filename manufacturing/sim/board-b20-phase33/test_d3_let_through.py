import unittest

import d3_let_through as lt


def rows(current, enn=0.0, col=1):
    """Synthetic waveform: time, then the 11 VECTORS; `current(t)` on column `col`, EN_N on column 4."""
    out = []
    for k in range(1501):
        t = k * 1e-6
        r = [t] + [0.0] * 11
        r[col] = current(t)
        r[4] = enn
        out.append(tuple(r))
    return out


class DeckTests(unittest.TestCase):
    def test_36_labels(self):
        cases = lt.derive_cases()
        self.assertEqual(len(cases), 36)
        self.assertEqual({c[0] for c in cases.values()}, set(lt.RAILS))
        self.assertEqual({c[1] for c in cases.values()}, set(lt.FAULTS))

    def test_deck_carries_the_drawn_chain_and_the_fault(self):
        text = lt.derive_cases()['n12-sht-fs'][3]
        self.assertTrue(text.startswith('* d3lt n12-sht-fs'))
        for line in ('RF1 p5sup faultn 10k', 'CF1 p5sup faultn 100n', 'MQ31 flt_lx faultn p5sup p5sup PQ31',
                     'RF2 flt_lx flt_l 4.7k', 'CF3 flt_l 0 100n', 'MQ39 en_e flt_l 0 0 NQ39',
                     'REN p5sup enn 10k', 'LFLT m12_out fx 100n', 'VTN m12_q m12_out 0'):
            self.assertIn(line, text)
        self.assertIn('.model PQ31 PMOS(LEVEL=1 VTO=-1.0', text)
        self.assertIn('.model NQ39 NMOS(LEVEL=1 VTO=1.5', text)
        self.assertIn('-i(VTN)-1.996', text)
        self.assertIn('.tran 0.1u 1.5m 0 0.1u', text)
        self.assertIn('CEN enn 0 5e-09', text)

    def test_overload_resistance(self):
        text = lt.derive_cases()['p12-x20-ss'][3]
        self.assertIn('BFLT p12_out 0 I=v(p12_out)/2.85714*', text)
        self.assertNotIn('RL12 ', text)


class ReadTests(unittest.TestCase):
    def test_square_overload(self):
        def i(t):
            return 3.0 if 0.5e-3 <= t < 0.7e-3 else 0.0
        r = lt.read(rows(i), '+12')
        self.assertTrue(r['enabled_before_fault'] and r['opened'])
        self.assertAlmostEqual(r['peak_a'], 3.0)
        self.assertAlmostEqual(r['duration_above_max_ms'], 0.2, places=3)
        self.assertAlmostEqual(r['i2t_a2s'], 9 * 0.2e-3, delta=9 * 2e-6)
        self.assertAlmostEqual(r['excess_i2t_a2s'], 0.81 * 0.2e-3, delta=0.81 * 2e-6)
        self.assertAlmostEqual(r['detect_ms'], 0.0)
        self.assertAlmostEqual(r['detection_to_off_ms'], 0.2, places=3)

    def test_negative_rail_sign_and_not_enabled(self):
        r = lt.read(rows(lambda t: -2.5 if t >= 0.5e-3 else 0.0, enn=5.0, col=3), '-12')
        self.assertFalse(r['enabled_before_fault'])
        self.assertFalse(r['opened'])
        self.assertAlmostEqual(r['peak_a'], 2.5)


if __name__ == '__main__':
    unittest.main()
