import math
from pathlib import Path
import tempfile
import unittest
from c12_compensation import analyze_waveform, cases, deck, prepare

class CompensationTests(unittest.TestCase):
    def wave(self, path):
        rows=[]
        for i in range(201):
            f=100*10**(i/50)
            magnitude=10**(math.cos(i*math.pi/50)*.3)
            phase=math.radians(-120-i*.4)
            rows.append(f'{f:.15g} {magnitude*math.cos(phase):.15g} {magnitude*math.sin(phase):.15g}')
        path.write_text('\n'.join(rows)+'\n')
        return rows
    def test_retains_ascending_and_descending_crossings(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wave'; self.wave(p); r=analyze_waveform(p)
            self.assertEqual([x['direction'] for x in r['unity_crossings']],['descending','ascending','descending','ascending'])
            self.assertEqual(len(r['minus180_phase_crossings']),1)
    def test_incomplete_nonfinite_duplicate_frequency_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wave'; original=self.wave(p)
            for kind in ('short','nonfinite','duplicate'):
                rows=original.copy()
                if kind=='short': rows.pop()
                elif kind=='nonfinite': rows[40]='nan 1 1'
                else: rows[40]=rows[39]
                p.write_text('\n'.join(rows))
                with self.assertRaises(ValueError): analyze_waveform(p)
    def test_exact_scope_and_output_only_precision(self):
        self.assertEqual(len(list(cases('contract'))),12)
        self.assertEqual(len(list(cases('light'))),4)
        name,case=next(cases('contract')); text=deck(name,case)
        self.assertIn('CCP cz 0 44.65n',text)
        self.assertIn('option numdgt=15',text)
    def test_wrong_model_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'model').write_text('wrong')
            with self.assertRaises(ValueError): prepare('light',p/'model',p/'output')
            self.assertFalse((p/'output').exists())

if __name__=='__main__': unittest.main()
