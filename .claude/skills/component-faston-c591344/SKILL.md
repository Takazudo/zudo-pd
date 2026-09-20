---
name: component-faston-c591344
description: Use to audit historical Board B FASTON rail tabs 63951-1 C591344 at J6-J9, the geometry alias 1217754-1, manufacturer drawings, current/retention limits, corrected model transform, underside placement and cover clearance and rail assignments.
---

Retired from the active BOM: all placement and cover-transform descriptions below refer to the historical four-Faston guarded revision. Current outputs use [C8465](/docs/components/records/c8465/).

# TE Connectivity 63951-1, C591344

Run the central validator and read the local JSON evidence. Canonical commercial
identity is TE 63951-1/C591344. The shared symbol/footprint is named 1217754-1,
which is a distinct loose-piece orderable. Exact primary TE drawings 63951 Rev L2
and 1217754 Rev D1 were retrieved on 2026-09-20 and confirm their matching geometry;
this does not erase their different commercial identities. Earlier unavailable
primary attempts and mirror evidence remain historical records.

The tab is a vertical metal flag with sideways mating direction, not a flat
pad parallel to the board. Its two posts use 1.4 mm holes at 5.08 mm pitch; nominal
profile height is 8.89 mm and posts extend 3.81 mm below the seating plane. The
6.35 mm mating width runs vertically on the upright blade.

The retained 63951 model has its long axis along raw X, whereas the footprint's
blade outline and two holes run along local Y. The correct model transform is
Z=90 degrees, scale 1, offset (0, 0, 0). The former Z=0 / Y=-7 mm model setting was
wrong. On the front side, rotation270 points left. The historical guarded-revision cover contract
uses bottom-side rotation270, which points inward/right and keeps the metal
inside the board outline. Side changes must be evaluated with the actual native
transform, not by reusing a front-side angle rule. The STEP companion was
normalized by a rigid(+6.9,+0.005,+5.725)mm translation to match the WRL datum;
its solder-leg centers agree within0.0001mm. Physical fit remains unmeasured.
`scripts/pcb/verify-compact-mechanics.py` verifies the real model, holes, rail
nets, edge distances and pogo arrangement, with negative controls.

Both pins are the same metal terminal: historical guarded-revision generated NETS assign J6=-12V,
J7=+12V, J8=+5V, J9=GND. The original baseline's unresolved terminal rows are
historical; the guarded-revision native netlist and PCB parity checks validated both legs.
The family current rating is still not an exact as-built rating. Cable housing
clearance, solder retention and repeated insertion force remain open.

## Human component reference

This local owner retains the retired candidate; it has no active public record.
[Current C8465 replacement](/docs/components/records/c8465/),
[component catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). These pages are generated
from the JSON bundle, which remains authoritative.
