# V196 — isolated coordinated J1 fanout candidate, NOT ADOPTED

A concrete source candidate replaces the earlier solver-only route proposals. It is based on the exact printed-pattern V148 PCB, not V150 shortened lands or a partial search tree. No V194/V195 solver restart, native KiCad, DRC/fill, physical operation or manufacturing output occurred. The stopped solver strategy remains stopped.

## What changed and why placement did not need to move

The approved scope released local placement/fanout and RAW/GND constraints. Actual CAD inspection showed a smaller coordinated solution using the local RAW freedom, without moving U1 or any support component:
- CC1 via moves from(14.65,6.20) to(14.90,8.45). Its .20mm F.Cu escape and B.Cu join move accordingly, retaining the lower CC1 tree.
- Right DM escape remains atX14.25 throughY8.80, then bends to(14.55,9.50), joining its existing lower tree. Both J1 DM contacts stay connected; all DP objects remain unchanged.
- Upper-left RAW via of the existing four-via array moves(15.50,8.70) to(15.75,8.70), unchanged .60/.30 diameter/drill. Its .60mm F.Cu bridge remains connected to the main vertical RAW conductor. The .60mm B.Cu feeder staysX15.50 alongside the locating hole, then bends below it through(15.50,7.15),(15.75,7.50) to the moved via.
- A local .25mm RAW sense-feed dip uses(15.30,9.00),(15.10,9.10),(14.70,9.10),(14.40,9.00), preserving the rest of that network.

13 existing route objects change;3 segments are added. All27 footprints/106 pads, values/MPNs/topology, Board-L header/holes/outline, project rules, libraries and schematic remain unchanged. All GND and DP route objects are byte/structure preserved; CC2 and other nets unchanged. Full1.5/2mm power trunks unchanged. No component move was required for this source candidate; no fixed-land/process assumption was altered.

## Evidence and geometry

Actual GCT B4 sheet1 image was inspected; printed lands/holes untouched. HUSB Rev2.5 retained pin-table evidence confirms U1.2=D+,U1.3=D-,U1.4=CC1; no USB protocol/topology claim added. Retained STEP bounds from SHA255c08ec961945374741183593e68abfc15fb8f80d0d930632c7e6aaa732a054 and transform Xboard=13.5-Xstep,Yboard=-Zstep place the full nominal model inside the supplied projection. New CC1 disk beginsY8.15, .45mm beyond maximum modelY7.70000000001. It therefore avoids reliance on the prior nominal .125mm vertical underside clearance. This is nominal geometric separation, NOT exactGF/toleranced seating/assembly or insulation acceptance. GF-versus15-A and placement/finish tolerances remain qualified limitations.

The first explicitly constructed candidate failed only two local RAW sense-feed clearances (.160235/.125mm). FIRST-SCREEN, FIRST-OBJECTS and first-study.py preserve it. The local .10mm dip fixes these, with no global search. Corrected SCREEN reports5,693 changed-neighborhood finite-width checks, zero failures, using conservative pad/hole boxes (including custom-pad extents), segment capsules, layer applicability, explicit via drills and distinct same-net drill separation. Conservative boxes may overreject; a passing separation bounds the contained actual shapes. No global native clearance claim.

Min changed copper gap .200mm: modified rightDM escape versus retained rightDP escape. Min changed hole-to-hole gap .250mm: moved RAW via versus right upper RAW via. These meet the source thresholds without nominal extra margin. All four RAW vias remain present, with same sizes/drills; their center spacing now .55mm at that pair. No fabrication tolerance guarantee.

Pad-inclusive before/after connectivity components compare equal. Removing original Q–S object gives identical components and isolates U2GND8 quiet return from COUT2 power return. Connectivity with all .25mm-and-thinner tracks excluded also compares equal, preventing a new full-load dependency on narrow control taps. Changed-route pad contacts are confined to the intended exact rectangular J1 A5 and B7 lands; unchanged custom-pad box contacts cannot introduce a candidate-only equivalence. Native/source independent verification remains necessary.

The .60mm RAW feeder increases3.600000→3.680116mm. At assumed35µm copper/20°C resistivity1.724e-8Ωm, the incremental series resistance is .065772mΩ (.197315mV/.591945mW if conservatively carrying3A). This is resistance arithmetic, not ampacity/thermal qualification or guaranteed current sharing. Overall RAW aggregate route length decreases slightly because another bridge shortens; do not treat that aggregate as a series-current model. Existing current limit, full-power bottleneck and thermal/physical qualifications remain unchanged.

## Source checks and first failure

Exact reversible replacement/addition: REVERSE.json reconstructs V148 SHAec1207594aaf67c510168e95a84886554283ef2409aa33d58decdb5686caa6d1 byte-for-byte. All nonroute AST and untouched route nodes identical. New segment UUIDs deterministic and globally unique; no via stack/drill/width/net changes. Board-edge bounds checked. Candidate281segments67vias, no added zones.

FINALIZE-FIRST.log/first-finalize.py preserve a checker assertion that allowed only A5 contact, overlooking the intended existing B7 pad contact at the modified DM segment tip. Correction explicitly permits A5/B7 only; it did not modify PCB geometry or relax unrelated clearances. FINALIZE-CORRECTED.log records successful checks. Portable copies of exact helpers/inputs and source syntax were checked after paths were made self-contained; no unchanged geometry rerun was performed just for packaging.

## Files and next needed verification

candidate-UNADOPTED/ contains the isolated self-contained PCB/schematic/project/local libraries under the original matching basename to retain lookup behavior. Parent folder/README distinguish the candidate. inputs/design-v148 and V148-original.kicad_pcb retain baseline. Scripts reproduce only source geometry/serialization checks in a disposable copy; no router/native invocation. First versions reference original workspace paths as historical evidence, not consumer entrypoints. No Git ancestry here; existing WSL owner should commit scoped source/artifact changes after review, without diagnostic bulk/dependency installs.

Next: independent changed-source review, then ONE ordinary bounded consumer load/inventory + no-fill DRC of this candidate, with exact hashes/ROinputs and existing safety guards. No CP-SAT solver required. Expect27footprints106pads18namednets+net0,281segments67vias,0zones. Compare against retained V14822 native fixed-land findings; those lands/rules remain unchanged. Any new route/mask/artwork finding needs review; do not claim projected DRC PASS. Schematic/project/library bytes unchanged, so repeated ERC is not independently needed absent a new context issue. V167 exact-input conditional-rule receipt is stale for this PCB and must NOT be reused or silently activated. No manufacturing adoption implied.
