# R1–R4 corrective layout: development review

This is an implementation record, not an independent approval or an order
release. The November 8 independent review remains the historical baseline.
The candidate preserves the 20 V / 5 A contract, adopted components, outline,
connectors and mounting geometry. Native DRC/parity and local R1–R4 geometry **passed on 2026-11-10 JST** for
PCB SHA-256 `56cbe0ab48b3bd25b6bab4223e3826ef437e3b972474b15481c5b86b7e889348`.
The native receipts bind the tested bytes and source hashes. Functional probe
artwork correction passed the bounded native checks; electrical, supplier-process
and thermal acceptance are separate. Failed routing candidates must not replace the canonical PCB.

## Reproducible owners

`search-two-sided.json` fixes C30/C34 placement and explicit pad-distance limits.
`pours.json` fixes thermal via geometry, back copper islands, short regulator
supply escapes and local return vias. The builder checks the actual native pad
positions. No heuristic placement search is part of the ordinary rebuild.
The router sees these fixed copper features before routing other nets.
C30 uses a 3.0 mm implementation-derived pad-distance target, revised from an
initial 2.5 mm target to preserve D9 courtyard clearance and the adjacent PDOK
escape. This is not a manufacturer-specified numeric limit. Actual routed
supply length (maximum 4.5 mm) and return length (maximum 1.0 mm) remain separate
checks, and independent review must assess the actual geometry.

`verify-corrections.py` records actual routed supply lengths and transitions,
return lengths, local via hole separation from both-side mask/paste pad openings,
thermal annulus containment, filled copper connectivity/area, conditioned losses
and source/evidence hashes. Run it only with the pinned native toolchain after
rebuilding; its output is not a substitute for DRC/parity or independent review.
See the builder README for mandatory regressions and Mac locking.

## Thermal via and assembly limits

R1 adds four 0.50/0.20 mm vias inside the U2 exposed GND pad. R2 adds four drain
vias for Q1 and connected B.Cu VBUS_OUT spreading. R3 adds three drain vias for
Q3 and connected B.Cu EF_IN spreading. These geometries provide 0.15 mm radial
annular rings. Actual filled-copper geometry, clearance and connectivity still
require native verification on the final revision.

[TI's TPS16630 PWP0020T drawing](https://www.ti.com/lit/ds/symlink/tps1663.pdf) distinguishes the 2.96 mm square solderable exposed
pad from the recommended 3.4 × 6.5 mm masked PCB heat spreader. The current pad
size is not, by itself, a package-pad error. The added array and connected copper
are an adaptation; neither establishes the reference board's thermal resistance.

The existing thermal pads have paste openings. Tenting is not a seal and does
not establish acceptable solder wicking. The supplier must review via finish,
stencil apertures and solder-volume consequences before an order. No epoxy-fill,
copper-fill or capped-via price/process option has been silently adopted.
The reviewed [JLC capability table](https://jlcpcb.com/capabilities/Capab) prefers
0.20 mm drills and documents annular-ring/spacing constraints; the
[via-finish guidance](https://jlcpcb.com/blog/five-via-finishes) explains tenting
and restrictions on ink plugging near exposed openings. Catalog capability is
not acceptance of this exact layout or a quotation.

## Shared land/paste evidence still requiring disposition

The exact [CSD18543Q3A drawing](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf), pages 8–10, has source-row datum −1.55 mm and recommended
central drain rectangle left edge −0.56 mm (width 1.775 mm); the adopted library
uses −1.475 mm and −0.4375 mm respectively. Nominal package drain overlap remains,
so this is not proof of an open connection. Full terminal tolerances, wetting
and the chosen stencil remain unqualified. The adopted full drain paste area
is about 4.349 mm²; TI's four example apertures total about 3.173 mm² before
corner rounding. This affects P/Q3 and B20/Q1–Q6.

The [DMP3036SFG](https://www.diodes.com/assets/Datasheets/DMP3036SFG.pdf) page 7 land union also differs from its suggested drawing. The current
drain union is about 5.685 mm² versus about 4.960 mm² in the suggested notched
union; both cover the nominal central package electrode. The present union
extends farther toward the source pads and has shallower notches. This is not
proof of a contact failure, and it is not demonstrated stencil/wetting adequacy.
It affects P/Q1 and B20/Q24, Q31, Q34, Q54 and Q56. Shared footprints were not
changed by this corrective layout. Retain an explicit pre-order land/stencil
review gate rather than treating native DRC as fabrication approval.

## Electrical and physical limits

Conditioned I²R arithmetic uses exact-part owner evidence and named assumptions;
installed thermal resistance remains UNKNOWN. Added copper does not establish
a measured 5 A rating. R5 turn-off/undershoot testing, R7 conditional SOA and
all unperformed physical acceptance sheets remain open/NOT RUN. No lower current
ceiling, component substitution or electrical-contract change is adopted here.

## Native warning disposition at the checked 56cbe candidate

The native report has zero electrical/clearance/courtyard errors and zero
unconnected items. Its three parity findings are **only MH1–MH3**, mechanical
footprints excluded from BOM/CPL. The complete 95 warning objects remain in
`native-drc.json`; the categories below account for every warning.

| Category | Count | Disposition |
| --- | ---: | --- |
| `via_dangling` | 2 | Retained functional F.Cu annular junctions described below; unused barrels, not test points or electrical dead ends. |
| `lib_footprint_issues` | 3 | Only the unavailable global `MountingHole` library for MH1–MH3. Embedded mechanical geometry and placement are preserved; no electrical footprint exception is inferred. |
| `lib_footprint_mismatch` | 3 | J2/J3 contact legends and D5 pin1 marker are board-local artwork adaptations only. The exact semantic delta proof preserves pads, nets, placement, copper and every non-approved object; shared library footprints remain unchanged. |
| `silk_over_copper` | 30 | Remaining reference/polarity/artwork collisions require explicit legibility/placement review. None involve the corrected functional probe artwork. Native warning severity is not manufacturing acceptance. |
| `silk_overlap` | 57 | Reference/package-artwork collisions. Retained for development review with original native SVGs available; no blanket artwork waiver or check suppression. |

The SCL via at (11.55, 21.65) joins a fixed F.Cu fan-out ending there to a routed
F.Cu segment ending at (11.55, 21.45): the centerline endpoints differ by
0.200 mm. The ATT via at (11.45, 24.25) joins its fan-out to a routed F.Cu segment
ending at (11.55, 24.40): the offset is about 0.180 mm. Both vias have 0.50 mm outer diameters and 0.30 mm drills (0.10 mm radial
rings), with no used B.Cu transition. Their annular copper provides the actual
same-layer junction; deleting the vias would remove that junction metal (SCL
would at best become a point-touch between rounded track ends). They are not
documented test-access points. The independently reviewed disposition is to
retain these functional junctions and classify their unused barrels, rather than
remove them merely to suppress warnings. A future replacement needs deliberate
F.Cu bridging and fresh native verification.

## Functional probe artwork correction, November 10

The generic footprint's J3 `VDD`/`RST` text was incorrect for this board:
actual J3.4 is VBUS_IN and J3.5 is GND. `finish_details.py` now applies front
contact ordinals and indexed reverse-side role tables with `4 VBUS`/`5 GND`.
The initial contact-label stage used 30 identified artwork objects:
14 contact/edge texts, two inset edge guides and 14 reverse-side map rows.
The final stage includes four additional polarity-related artwork objects
described below; all other objects remain immutable.
Shared footprints, frozen P15, pads, electrical contracts and component geometry
are unchanged. The strict serialization fingerprint excludes only those exact
artwork UUID nodes and proves that all remaining copper/fill/geometry/settings are unchanged.
The retained proof chain runs from checked 7b44 through 76ff to the current
56cbe candidate.

All functional glyphs are 1.0 mm high with 0.15 mm strokes. Conservative native
bounding-box clearance to resolved same-side pad mask openings is at least
0.17175 mm; edge clearance is at least 0.35175 mm. J3 ordinal4 is shifted 0.83 mm
upward from its pad center to clear R31 and is verified closest to pad4. The
retained official supplier Legend snapshot and its hash/date are recorded in
`fabrication-legend-constraints.json`. This CAD/mask screen is not observation
of supplier tenting or printed legibility; drill dots in a copper-layer render
are not physical print evidence. Supplier preview remains pending.

Native DRC has no finding involving any corrected functional artwork object;
text-height and silk-edge-clearance counts are now zero. The parent independently
reviewed the exact front/back native renders before adoption. Native regression
proves two transforms are byte-identical, another transform is idempotent, and
a deliberately wrong J3.4 net is rejected. `probe-silk-check.json` records the
exact semantic delta and native report identity.

The earlier full fresh-builder/saved-route/fill proof is retained with its
historical source hashes in `native-full-builder-replay-20261110.json`.
`native-replay.json` explicitly records the final artwork-stage scope; no fresh
heuristic router or copper refill is claimed. Final DRC/parity and the actual
R1–R4 correction verifier were rerun on the adopted artwork candidate with the
canonical project restored before DRC. Remaining 95 warnings and manufacturing
holds above are not waived.

## Final polarity cue follow-up

Independent per-object review found Q3 reference text over D5's pin1 cue and
D13 reference text over both D8 cathode bars. The final stage moves only those
two reference fields to their existing same-side fabrication layers. All other
Fab artwork and all component properties remain unchanged. D8's original
cathode bars are exposed without editing them.

D5 had two silk dots, including a 0.03 mm radius/0.06 mm stroke duplicate. The
tiny duplicate is retained on the nonmanufacturing comments layer. One filled
0.35 mm outer-diameter marker with 0.15 mm stroke now sits at (10.05,12.10),
on the lower-left pin1 corner. Native pin1 is (10.65,11.575), GND, and the
marker is explicitly checked nearest that pad. Its conservative mask-opening
gap is 0.302 mm; gaps to the exact D5 2.1 mm maximum body and adjacent Q3
3.25 mm maximum body are 0.276/0.350 mm. Exact TVS owner facts/pin map and
Q3 facts are bound in the artwork receipt. These are CAD geometry screens,
not supplier print observations or physical acceptance.

The parent independently reviewed the exact front/back native renders and
D5 corner crop before adoption. A four-object-only prototype fingerprint
proved every other serialized object unchanged from 76ff; the owned final
stage reproduced those exact reviewed PCB bytes. Actual final native DRC/
parity, R1–R4 geometry checks, byte-identical twins/idempotence, source/output
project-sidecar preservation and wrong J3/D5 net negative controls passed.
`SaveBoard(..., True)` preserves project settings and its return is checked.

The superseded 76ff PCB and reports remain locally archived with their hashes
in `polarity-artwork-history-20261110.json`. There are now 95 classified native
warnings; none involve corrected contact or polarity artwork. No copper refill,
rerouting, component movement or model change was performed. Remaining ordinary
artwork and supplier-placement/print review are not waived.
