# ALPS RK10J11E0034 / C470643

Selected single-unit, 10 kΩ ±30%, linear 1B potentiometer with 270° ±10° physical stops.
[Primary product](https://tech.alpsalpine.com/e/products/detail/RK10J11E0034/) and
[primary catalog, drawing 1](https://tech.alpsalpine.com/cms.media/product_catalog_rv_03_rk10j_en_780020d1ea.pdf)
were inspected on 2026-09-06. The exact JLCPCB listing showed 6,939 stock / 6,677 available,
Wave Soldering and Economic/Standard PCBA. ALPS specifies Manual soldering: confirm the actual
assembly process before ordering. These observations reserve no stock.

## Corrected single-unit pad identity

EasyEDA C470643 supplied the shared RES-TH_RK10J12E0A0A dual-unit footprint/model.
The original electrical pad numbers must NOT be used. Drawing 1's terminal row is
1 / dummy / 2 / dummy / 3 at X−4/−2/0/+2/+4, Y+5 mm. The project maps these to
1 / MP1 / 2 / MP2 / 3, with upper supports MP3(+5,−5), MP4(−5,−5).
Pin2 is the wiper, pin1 GND, pin3 V3P3. All four MP pads are electrical no-connects.
End-direction versus clockwise motion needs continuity/calibration confirmation.

The two support slots use project-enlarged 0.9 × 1.4 mm holes versus drawing's
0.7(+0.1/0) × 1.2(+0.2/0). Remaining imported hole geometry needs prototype insertion
and solder-fill confirmation. Catalog insertion(t:2mm) is retained verbatim; it is not
asserted to require a 2mm PCB. Our PCB remains 1.6mm.

## Shared-family mechanical preview

The original STEP and WRL bytes are retained under an explicit `_family` basename.
This is supplier-family preview geometry whose exterior was compared to drawing 1,
not an exact ALPS-certified CAD model. External wheel diameter is about14mm (drawing14±0.2),
maximum model reach1.970mm; terminals reach2.100mm below seating (~0.500mm beyond1.6PCB).
Wheel centre is local(0,−2.5), not the footprint origin. The project courtyard includes
14.2mm maximum wheel diameter with0.3mm margin. Full physical seating, handling, soldering
and enclosure recess/finger access remain prototype checks.

- STEP SHA256: `a269286859ddcf169a50c53c80608770861e5dd891d52231b39f04d058c07fa1`
- WRL SHA256: `372effcbbcfb2e64cf17c74f5189531c6dad7f3dc08b706ded614efa26064bfe`
