import tempfile
from pathlib import Path
import unittest
from analyze_refinement import supplemental
from prepare_refinement import transform

class SupplementalTests(unittest.TestCase):
    def test_transform_rejects_unreviewed_step_and_preserves_primary_output(self):
        text='\n'.join(['CL12 p12_out cl12 180u','RCL12 cl12 0 50m','CL5 p5_out cl5 120u','RCL5 cl5 0 50m','CLN 0 cln 180u','RCLN cln m12_out 50m','.tran 2u 250m 0 5u','wrdata nom.dat v(p12_out)','.endc'])
        changed=transform(text,'nom')
        self.assertEqual(changed.replace('.tran 2u 250m 0 2u','.tran 2u 250m 0 5u').replace('wrdata nom-osc-cap.txt v(cl12) v(cl5) v(cln)\n',''),text)
        with self.assertRaises(ValueError): transform(text.replace('0 5u','0 10u'),'nom')
    def test_requires_same_time_grid_and_complete_finite_vectors(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'cap.txt';rows=[(0,1),(2e-6,2)]
            p.write_text('0 1 0 2 0 3\n2e-6 4 2e-6 5 2e-6 6\n')
            self.assertEqual(supplemental(p,rows)[1],(2e-6,4,5,6))
            for text in ['0 1 0 2 0 3\n','0 nan 0 2 0 3\n2e-6 4 2e-6 5 2e-6 6\n','0 1 0 2 0 3\n3e-6 4 3e-6 5 3e-6 6\n']:
                p.write_text(text)
                with self.assertRaises(ValueError): supplemental(p,rows)
if __name__=='__main__':unittest.main()
