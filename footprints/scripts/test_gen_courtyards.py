"""Geometry and file-safety regressions for the courtyard generator/checker."""
import contextlib
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gen_courtyards as generator


BOX = (-1.75, -1.25, 1.75, 1.25)
BODY = '''(footprint "fixture" (layer "F.Cu")
 (fp_rect (start -1 -1) (end 1 1) (stroke (width 0.1) (type solid))
   (fill none) (layer "F.Fab"))
 (pad "1" smd rect (at -1 0) (size 1 1) (layers "F.Cu" "F.Mask"))
 (pad "2" smd rect (at 1 0) (size 1 1) (layers "F.Cu" "F.Mask"))
'''
RECT = ''' (fp_rect (start -1.75 -1.25) (end 1.75 1.25)
   (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
'''
LINES = ''' (fp_line (start 1.75 1.25) (end 1.75 -1.25) (layer F.CrtYd) (width 0.05))
 (fp_line (start -1.75 -1.25) (end -1.75 1.25) (layer F.CrtYd) (width 0.05))
 (fp_line (start -1.75 1.25) (end 1.75 1.25) (layer F.CrtYd) (width 0.05))
 (fp_line (start 1.75 -1.25) (end -1.75 -1.25) (layer F.CrtYd) (width 0.05))
'''


def footprint(courtyard=RECT):
    return BODY + courtyard + ')\n'


class CourtyardGeometryTests(unittest.TestCase):
    def test_rect_and_unordered_reversed_lines_are_equivalent_and_unchanged(self):
        for text in (footprint(), footprint(LINES)):
            with self.subTest(text=text):
                self.assertEqual(generator.compute_courtyard(text), BOX)
                self.assertEqual(generator.courtyard_box(text), BOX)
                self.assertEqual(generator.rewrite(text), text)

    def test_numeric_and_whitespace_formatting_does_not_cause_drift(self):
        text = footprint().replace('1.75', '1.750000').replace('0.05', '5e-2')
        self.assertEqual(generator.rewrite(text), text)

    def test_actual_inductor_is_geometry_correct_without_reserialization(self):
        text = (generator.MASTER_DIR/'ASPI-0630LR_L7.5-W6.85.kicad_mod').read_text()
        self.assertEqual(generator.courtyard_box(text), (-4.45, -3.75, 4.45, 3.75))
        self.assertEqual(generator.rewrite(text), text)

    def test_missing_and_wrong_geometry_are_repaired(self):
        for text in (footprint(''), footprint(RECT.replace('-1.75', '-1.50')),
                     footprint(RECT.replace('1.75', '2.75'))):
            with self.subTest(text=text):
                self.assertFalse(generator.courtyard_matches(text, BOX))
                repaired = generator.rewrite(text)
                self.assertEqual(generator.courtyard_box(repaired), BOX)
                self.assertEqual(generator.rewrite(repaired), repaired)
                self.assertEqual(generator.strip_courtyard(repaired),
                                 generator.strip_courtyard(text))

    def test_same_bbox_does_not_hide_open_diagonal_or_duplicate_edges(self):
        lines = LINES.splitlines(keepends=True)
        cases = [LINES.replace('(end 1.75 -1.25)', '(end 1.75 -1.20)', 1),
                 LINES.replace('(end 1.75 -1.25)', '(end -1.75 -1.25)', 1),
                 ''.join(lines[:-1] + [lines[0]]), ''.join(lines[:-1]),
                 LINES + lines[0]]
        for courtyard in cases:
            with self.subTest(courtyard=courtyard):
                self.assertFalse(generator.courtyard_matches(footprint(courtyard), BOX))

    def test_stroke_fill_and_unsupported_shapes_are_not_ignored(self):
        cases = [RECT.replace('0.05', '0.10'), RECT.replace('type solid', 'type dash'),
                 RECT.replace('fill none', 'fill solid'),
                 RECT.replace('fp_rect', 'fp_circle'), RECT + RECT]
        for courtyard in cases:
            with self.subTest(courtyard=courtyard):
                self.assertFalse(generator.courtyard_matches(footprint(courtyard), BOX))

    def test_degenerate_and_nonfinite_rectangles_fail(self):
        for rect in (RECT.replace('(end 1.75 1.25)', '(end -1.75 1.25)'),
                     RECT.replace('(end 1.75 1.25)', '(end nan 1.25)')):
            self.assertFalse(generator.courtyard_matches(footprint(rect), BOX))


class ReviewedNominalCourtyardTests(unittest.TestCase):
    def setUp(self):
        self.text = (generator.MASTER_DIR/'WJ500V-5.08-2P_C8465.kicad_mod').read_text()

    def test_exact_nominal_policy_preserves_frozen_terminal(self):
        expected = (-6.03, -5.85, 5.43, 4.85)
        self.assertEqual(generator.compute_courtyard(self.text), expected)
        self.assertEqual(generator.courtyard_box(self.text), expected)
        self.assertEqual(generator.rewrite(self.text), self.text)
        # The exception is explicit, not an accidental equality with the default.
        self.assertNotEqual(generator.envelope(generator.parse(generator.tokenize(self.text))), expected)

    def test_even_larger_unreviewed_bounds_are_drift(self):
        changed = self.text.replace('(start -6.03 -5.85)', '(start -6.13 -5.85)')
        self.assertFalse(generator.courtyard_matches(changed, generator.compute_courtyard(changed)))
        self.assertEqual(generator.courtyard_box(generator.rewrite(changed)),
                         (-6.03, -5.85, 5.43, 4.85))

    def test_moved_pad_invalidates_review_instead_of_growing_box(self):
        changed = self.text.replace('(at 2.54 0)', '(at 6 0)')
        self.assertNotEqual(changed, self.text)
        with self.assertRaisesRegex(ValueError, 'pads/Fab'):
            generator.rewrite(changed)

    def test_fab_growth_is_not_hidden_by_two_decimal_rounding(self):
        changed = self.text.replace('(end 5.08 4.5)', '(end 5.181 4.5)')
        self.assertNotEqual(changed, self.text)
        with self.assertRaisesRegex(ValueError, 'pads/Fab'):
            generator.compute_courtyard(changed)

    def test_silk_must_stay_inside_reviewed_rectangle(self):
        changed = self.text.replace('(end 5.2 4.62)', '(end 5.44 4.62)')
        self.assertNotEqual(changed, self.text)
        with self.assertRaisesRegex(ValueError, 'silkscreen'):
            generator.compute_courtyard(changed)

    def test_unlisted_footprint_does_not_inherit_exception(self):
        changed = self.text.replace('WJ500V-5.08-2P_C8465', 'different-terminal')
        self.assertEqual(generator.compute_courtyard(changed), (-5.93, -5.87, 5.45, 4.87))
        self.assertNotEqual(generator.rewrite(changed), changed)


class CourtyardFileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.master = Path(self.temporary.name)/'master'
        self.pretty = self.master/'library.pretty'
        self.pretty.mkdir(parents=True)
        self.path = self.master/'fixture.kicad_mod'
        self.copy = self.pretty/self.path.name
        self.path.write_text(footprint())
        self.copy.write_text(footprint())

    def run_check(self, *args):
        with patch.object(generator, 'MASTER_DIR', self.master), \
                patch.object(generator, 'PRETTY_DIR', self.pretty), \
                contextlib.redirect_stdout(io.StringIO()):
            return generator.main(list(args))

    def test_check_accepts_synced_equivalent_format_without_writes(self):
        before = [p.read_bytes() for p in (self.path, self.copy)]
        self.assertEqual(self.run_check('--check'), 0)
        self.assertEqual([p.read_bytes() for p in (self.path, self.copy)], before)

    def test_check_rejects_missing_copy_without_creating_it(self):
        self.copy.unlink()
        self.assertEqual(self.run_check('--check'), 1)
        self.assertFalse(self.copy.exists())

    def test_check_rejects_byte_different_copy_even_if_geometry_matches(self):
        self.copy.write_text(footprint(LINES))
        before = self.copy.read_bytes()
        self.assertEqual(self.run_check('--check'), 1)
        self.assertEqual(self.copy.read_bytes(), before)

    def test_generation_repairs_geometry_and_creates_missing_copy(self):
        self.path.write_text(footprint(''))
        self.copy.unlink()
        self.assertEqual(self.run_check(), 0)
        self.assertEqual(self.path.read_bytes(), self.copy.read_bytes())
        self.assertEqual(generator.courtyard_box(self.path.read_text()), BOX)
        self.assertEqual(self.run_check('--check'), 0)

    def test_full_library_check_is_read_only(self):
        paths = list(generator.MASTER_DIR.glob('*.kicad_mod')) + list(generator.PRETTY_DIR.glob('*.kicad_mod'))
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.main(['--check']), 0)
        self.assertEqual({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, before)


if __name__ == '__main__':
    unittest.main()
