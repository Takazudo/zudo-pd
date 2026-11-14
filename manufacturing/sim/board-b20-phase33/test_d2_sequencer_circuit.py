import unittest

import d2_sequencer_circuit as sc


class DeckTests(unittest.TestCase):
    def test_972_labels_from_4_combos(self):
        cases = sc.derive_cases()
        self.assertEqual(len(cases), 972)
        self.assertEqual({c[0] for c in cases.values()}, set(sc.COMBOS))

    def test_network_replaces_the_behavioural_clamp(self):
        text = sc.derive_cases()['hlrh-phnlfl-zmz'][3]
        self.assertNotIn('BHOLD', text)
        self.assertIn('MQH dgn sqg m12_out m12_out NSQH', text)
        self.assertIn('MQP sqpd sqen dis dis PSQP', text)
        self.assertIn('.model NSQN NMOS(LEVEL=1 VTO=0.5', text)
        self.assertIn('.model NSQR NMOS(LEVEL=1 VTO=1.5', text)
        self.assertIn('.model DZSQ D(BV=3.0', text)
        self.assertIn('CDGN dgn m12_out 68n', text)
        self.assertTrue(text.startswith('* d2sc hlrh-phnlfl-zmz'))


if __name__ == '__main__':
    unittest.main()
