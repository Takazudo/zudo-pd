# Print the adhesive PCB legs

Units: mm. Import at 100% scale.

- adhesive-leg-18mm-m3.stl: one leg; print four copies.
- adhesive-leg-18mm-m3-4x.stl: four separate legs, already spaced on one plate.

Place the broad flat adhesive bases on the print bed, with screw openings upward.
Use the material and hole-compensation settings that worked for the tested rail.
No external support structures are needed.

Each leg is 18 mm high, with a 14 × 14 × 2 mm flat base, an 8 mm pole and 7 mm PCB seat.
The upper 4.5 mm of the bore preserves the exact 27-vertex hole from bar-30hp.stl.
A larger 3.4 mm pocket below provides screw-tip space; total blind depth is 10 mm.
No tap, modeled thread or threaded insert is part of this design.

Use an M3 × 8 mm non-countersunk screw from the PCB back into each leg. Through a
1.6 mm board, insertion is 6.4 mm, including the complete 4.5 mm gripping section.
A washer reduces insertion by its thickness. Fit all four legs before applying
adhesive to their flat undersides.

The existing PCB holes are nominally 3.0 mm; confirm the actual M3 screws pass
freely through the finished holes. The PCB fabrication files are unchanged.
The four bases require 116 × 91 mm of mounting space, 3 mm beyond each PCB edge.

The files have passed mesh and nominal assembly checks. Printed fit, screw
retention and adhesive grip still depend on the actual print and hardware.
