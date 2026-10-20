# Aluminum heat-spreader concept for Board B (screen)

**Status: concept analysis only. Nothing here is designed, adopted, drilled or fabricated.** No PCB, schematic, spec, footprint or owner-bundle change. Every board stays an unvalidated draft, and **nothing on this page is measured**. Thermal-pad properties come from an unverified sales listing and are treated as unknown. Every number is a calculation (calc), a project assumption (PA) or unavailable (UNAV). The proposed measurements have **not** been run and need owner approval.

**Which board is "existing": the renewal Board B** (owner-stated reference: the `releases/corner-support-review/` package at `f25194f`; see [`as-built-and-controller.md`](as-built-and-controller.md) §1.1). Which package state was built is not recorded; S3 (`f25194f`) adds the U8 divider R26–R28 and changes U6–U8 part numbers but no hot-part position used here; it also changed Board B F_Cu, mask, paste and silk, so the screened copper may differ between built states. §§1–5 screen the existing renewal Board B. §A screens the earlier combined board (v0.3.0 / v0.4.0 family) and is kept for history only.

Request: zudo-pd#218 comment 6286606035, item 2. The owner's images of the proposed cutout plates were not available to this analysis; the plate outlines below are built from the written description (cutout plates over regulator and inductor regions, weaving around capacitors, 3–4 inexpensive plates, pads of different thickness bridging height differences).

## 0. Inputs and what they are worth

| Input | Source | Class |
|---|---|---|
| Part positions, layer, pad nets | `boards/board-b/board-b.kicad_pcb` (current active board) | Project data, unvalidated draft |
| Tab potentials | Pad 6 nets in the PCB; [`component-renewal-ldos`](../.claude/skills/component-renewal-ldos/SKILL.md) (LT1963A tab = GND, LT3015 tab = IN); [`component-lm2596s-adj-c347423`](../.claude/skills/component-lm2596s-adj-c347423/SKILL.md) (inverting U4 tab rides the negative rail) | Netlist + owner bundles |
| Thermal vias and pour areas | [`power-layout.json`](power-layout.json): 12 thermal vias each at U4, U6, U7, U8; U4 −14.145 V pour 463 / 421 mm² (F/B), U8 293 / 253 mm² | Layout report; not thermal qualification |
| LDO dissipation screens | [`power-budget.md`](power-budget.md): about 4.23 W (+12 V), 1.95 W (+5 V), 3.52–3.54 W (−12 V); θJA limits about 20.1 / 43.5 / 24.0–24.2 °C/W at 40 °C ambient | calc, unverified |
| Installed orientation and stack | `CLAUDE.md`, [`boards/board-b/mechanical.json`](../boards/board-b/mechanical.json): Board B component face **down** on 18 mm legs; Board P 27 × 40 mm mates face-to-face on F.Cu at nominal Z +11.1 mm, transform P(x,y) → B(y − 0.5, x + 12) | Project data; stack tolerance unmeasured |
| Old concept | `doc/.../overview/mechanical-design.md` "Aluminum PCB Heatsink Concept" (archived) | **Historical only.** Its parts (L7812, L7805, CJ7912, Fastons), heights, dissipations and prices are superseded and are not used here |
| Plate construction | Owner's aluminum blank panels (`Takazudo/zudo-blanks`, `panels/alumi-blanks-v1-3U-8hp`; product page) | Gerber/drill set confirmed; material stack UNAV (§B) |
| Thermal pad | [AliExpress listing](https://ja.aliexpress.com/item/1005010519398949.html) the owner already holds (the old page lists it as "24 W/m·K") | **Unverified sales claim.** Conductivity, dielectric strength, hardness and compression set are all UNAV |

## A. Historical combined board, v0.3.0 / v0.4.0 family (screen; not the existing hardware)

Source: root `zudo-pd.kicad_pcb` (historical v0.4.0; read only, not regenerated). Positions are its own mm coordinates. The committed CPLs `jlcpcb-order-snapshots/v0_3_0/used-for-order/CPL-zudo-pd.csv` and the v0.4.0 snapshot give **identical** placements and rotations for U2–U4, U6–U8 and L1–L3, so the hot-part layout below applies to both on placement. Tab nets, vias and holes were read from the v0.4.0 PCB only; v0.3.0's copper is **not screened**, and the post-#93 variant is not screened separately. The installed orientation of the arrived boards and the role of nearby vias (thermal or stitching) are **not established in the repo**.

| Part | Position | Package | Tab potential | Vias within 8 mm (count only) |
|---|---|---|---|---|
| U2 LM2596S-ADJ (+ rail buck) | (49, 25.1) | TO-263-5 | **GND** | 25 |
| U3 LM2596S-ADJ (+ rail buck) | (49.2, 45.9) | TO-263-5 | **GND** | 22 |
| U4 LM2596S-ADJ inverting | (48.56, 64.4) | TO-263-5 | **−13.5 V OUT** | 3 |
| U6 L7812CD2T | (29.46, 47.9) | TO-263-2 | **GND** | 21 |
| U7 L7805ABD2T | (32.97, 82.5) | TO-263-2 | **GND** | 20 |
| U8 CJ7912 | (44.65, 83.8) | TO-252-3 | **−13.5 V** (its input) | 1 |
| L1–L3 100 µH | x ≈ 67, y 25.5 / 42.7 / 65.3 | 13.8 × 12.8 mm land | switch node on one pin | — |
| D1–D3 SS34 | (70.66, 34.1), (63.86, 34.1), (60.56, 55.6) | SMA | switch node (cathode) | — |
| U1 STUSB4500 | (44.9, 12.9) | QFN-24 | On this board; there is no Board P daughterboard | — |

All parts are on F.Cu. NPTH M3 (3.2 mm) holes: corners (1, 7), (1, 92), (69, 92), and interior **(53, 35.5), (53, 55), (44.5, 73), (54.25, 7)**. The interior holes sit beside the regulator column and are the only candidate plate mounts that need no new hole; their clearance to parts, and whether they are free in the installed fixture, are unverified.

Plates by potential (concept, not designed):

| Plate | Covers | Potential | Candidate mount |
|---|---|---|---|
| V1 | U2 + U3 (LM2596 bucks) | GND | (53, 35.5) between them |
| V2 | U6 L7812 | GND | (53, 35.5) or (53, 55), with a bar; not measured |
| V3 | U7 L7805 | GND | (44.5, 73) |
| V4 | U4 + U8 (negative chain) | −13.5 V | (53, 55) / (44.5, 73); must stay insulated from V1–V3 |

Inductors and SS34 diodes stay out of every plate (switch nodes). V1–V3 share GND and could be one plate if their geometry allows. The §4 analysis (pad resistance, plate-to-air resistance, compression, vent keep-outs, EMI) applies unchanged. The weak thermal-via evidence near U4 and U8 (3 and 1 vias in 8 mm) suggests their PCB path is weaker than the others', which a plate cannot fix by itself.

## B. Plate construction: the owner's aluminum blank-panel stack

Owner reference (zudo-pd#218 comments 6286650616 and 6286691733): the existing aluminum blank panels ([product page](https://takazudomodular.com/products/blanks-large-intro/); repo `Takazudo/zudo-blanks`, `panels/alumi-blanks-v1-3U-8hp`, read only), cut to heat-spreader outlines, with the **fully soldermasked face toward the components** and full silkscreen as extra insulation. Different pad thicknesses to bridge component heights are intentional, and the pad material is in hand.

### B.1 What the reference files confirm

| Item | Finding | Class |
|---|---|---|
| Ordered files | In the zudo-blanks repo: `jlcpcb-order-snapshots/2026-04-16--alumi-blanks/alumi-blanks-v1-3U-8hp.zip`, identical to the panel's `gerber/` folder: Edge_Cuts, F_Mask, B_Mask, NPTH and PTH drill files, job file. **No copper and no silkscreen Gerber** | Confirmed (repo) |
| Masks | F_Mask and B_Mask differ only in their FileFunction line (Top / Bot). Their only features are 4.0 × 11.08 mm rounded-rectangle openings at the two slots; everything else is masked. The files therefore call for mask on **both** faces, while the product page says the back is bare | Files confirmed (repo); which face was actually masked **UNAV** |
| Holes | Two NPTH **oval slots 3.2 × 10.28 mm** (`8hp.kicad_pcb` `drill oval 3.2 10.28`; NPTH.drl routes X6.62→13.7 and X26.6→33.68); PTH file empty. The mask openings leave an unmasked ring about 0.4 mm wide around each slot on both faces | Confirmed (repo) |
| Thickness | 1.6 mm declared nominal: the job file `BoardThickness` is the same KiCad default as the rejected stack below, and the product page size table has no 8hp row | **PA** (declared nominal); ordered value UNAV |
| As delivered | Product page: aluminum, "one side painted black", the back is bare aluminum | Owner's published description |
| Stack layers in the job file | Generic KiCad FR4 two-layer stack (35 µm copper, 1.51 mm FR4) | **Not the aluminum order**; KiCad default, not evidence |
| Aluminum alloy, dielectric thickness and conductivity, mask thickness, which face JLCPCB masked, order options | Not in the repo files | **UNAV** (needs the JLCPCB order detail page; owner action) |

So the delivered panel appears to be a single-sided aluminum board: one black (masked) face over the board's dielectric, and one bare aluminum face. On a single-sided aluminum PCB the copper and the insulating dielectric sit on the masked face; with no copper Gerber, that face is mask over dielectric over aluminum (PA, consistent with the product page; the dielectric's presence and thickness are not confirmed for this order).

### B.2 Stack facing the components (owner's orientation)

Component tab or body → thermal pad → (silkscreen, if added; **the panels in hand have none**, since no silkscreen Gerber was ordered, so full-silkscreen coverage needs a new order) → soldermask → aluminum-PCB dielectric (if present) → aluminum core → bare face to air.

- **Insulation verdict: not qualified.** The intended layers (pad, silk, mask, dielectric) can each insulate, but none is qualified here for **compressed contact**: the pad's dielectric strength and puncture resistance are an unverified sales claim; mask and silk are not rated insulation and can be scratched or punctured by tab edges, burrs or debris under clamp load; the dielectric's rating for this order is UNAV. The stack is a reasonable design intent for a low-voltage (≈14 V) functional barrier, provided it is tested (H1b below), and it does not replace one-potential-per-plate (§4.1).
- **Edges and holes expose bare aluminum** (and the dielectric edge). A routed outline or a drilled hole is conductive at its wall, and the reference slots also carry an **unmasked ring about 0.4 mm wide** around each slot on both faces; any hole in a cut plate made the same way has that ring too. Keep every plate edge and hole wall clear of tabs, switch nodes, pads and exposed copper by a margin not yet set (PA proposal: at least the pad overhang plus 1 mm), and break or deburr edges.
- **Core potential:** the aluminum core is tied to nothing unless a fastener or a pad failure connects it. A plate over one potential can be left floating or tied to that potential deliberately; a plate over two potentials must float and depends wholly on the barrier.
- **Fasteners:** a metal screw through an aluminum plate connects the core to whatever the screw touches. On the board side, the holes are NPTH and unconnected, but a screw head or nut can still touch copper or a part. Use insulating washers or nylon hardware, or keep screw heads in copper-free keep-outs, until the plate's potential is decided.
- **Thermal resistance of the plate itself:** the 1.6 mm aluminum core spreads well; the dielectric adds a small resistance (UNAV; typical aluminum-PCB dielectrics are thin, but no value is used). The plate-to-air resistance in §4.2 still dominates.

### B.3 Pad thickness per plate (method; embraces different thicknesses)

For each part under a plate: gap_i = plate underside height − part top height; choose an uncompressed pad t_i = gap_i / (1 − c), with compression c in the vendor-tip range of 10–20 % (PA; force versus deflection UNAV). Thermal resistance is then R_i = t_compressed / (k · A_i) per §4.2. Pads of different thickness under one plate are expected; the plate height is set by the tallest part that must touch it, and taller parts that must not touch (cans, headers) get cutouts.

| Plate | Parts in contact | Part heights | Pad thickness | Notes |
|---|---|---|---|---|
| V1 / A-type (GND regulators) | TO-263 bodies (U2/U3 on the combined board; U6/U7 on renewal Board B) | UNAV (exact drawings not in evidence) | Per formula; thinner pads on taller bodies | Cutouts for cans and MLCCs |
| V2 / V3 (combined board LDOs) | TO-263-2 L7812 / L7805 | UNAV | Per formula | One potential (GND) |
| V4 / B-type (negative chain) | TO-263 U4 + TO-252 U8 (combined) or DD-PAK U8 (renewal) | UNAV; TO-252 is lower than TO-263, so its pad is thicker | Per formula | −13.5 V / −14.145 V; isolated from GND plates |
| C (inverting stage, renewal) | U4 TO-263, L3 top | UNAV; inductor height differs from the TO-263 | Per formula; L3 switch-node pin side cut out | Mixed potentials: split or cut |

Each row needs the exact part heights (from drawings or 3D models) and a measured gap (H2) before thicknesses can be listed. Thicker pads raise R linearly, so where the height step is large, a stepped plate or a spacer block is an alternative to a very thick pad.

## 1. Hot parts, potentials and neighbors (renewal Board B, the existing hardware)

Coordinates are Board B mm (origin top-left, F.Cu view). All parts are on F.Cu, which faces **down** when installed.

| Part | Position | Package | Tab / hot-copper potential | Thermal vias | Near keep-outs |
|---|---|---|---|---|---|
| U6 LT1963A (+12 V LDO) | (74, 16) | TO-263-5 | **GND** | 12 | C40 47 µF polymer (86, 16); C21 470 µF 35 V (99, 18); C3/C36/C37 1210 MLCCs at x 57–62 |
| U7 LT1963A (+5 V LDO) | (77, 34) | TO-263-5 | **GND** | 12 | C41 (89, 34); C4 470 µF 10 V (62, 34) |
| U8 LT3015 (−12 V LDO) | (77, 60) | DD-PAK-5 | **−14.145 V PRE** (tab = IN) | 12 | C42 (89, 60); C11 470 µF 25 V (62, 55); J11 shrouded 16-pin header (81.5, 72.8) |
| U4 LM2596 inverting (−14.145 V) | (23, 60) | TO-263-5 | **−14.145 V PRE** | 12 | C7 470 µF 35 V (24, 48); C9 100 µF (21.7, 73); J7 terminal (7, 61); J10 header (41.4, 72.8) |
| L3 100 µH + D3 SDT5A60SA-13 (inverting stage) | (47, 60), (35, 61) | 13.8 × 12.8 mm land; SMA | L3 pin 1 / D3 K = **switch node** (Net-(D3-K)); L3 pin 2 GND; D3 A −14.145 V | — | C24 470 µF (61.5, 67.8); C12 470 µF (48, 47); J10 |
| U3 LM2596 (+6.519 V) | (23, 36) | TO-263-5 | **GND** | none listed | **Under Board P** (see §2); D2 (33.75, 35) |
| L2 100 µH + D2 SS34 (+6.519 V stage) | (47, 34), (33.75, 35) | as L3; SMA | L2 pin 1 / D2 K = switch node; L2 pin 2 +6.519 V | — | C12 (48, 47); C4 (62, 34); J5 (37.2, 24.9) |
| U2 AP63201 + L1 (+13.44 V) | (43, 15), (51, 15) | TSOT-23-6; 7.5 × 6.85 mm (L1 ≤ 3.0 mm tall, owner bundle) | U2_SW switch node on L1 pin 1 | — | C6, C38, C39 0805/1210 nearby; tiny package: no useful top contact |

Body heights of TO-263 / DD-PAK packages, the 100 µH inductors and the electrolytics are **not recorded** in the owner bundles reviewed here (UNAV). The old page's 4.5 mm (TO-263) and 10.5 mm (10 mm can) values are not reused. A plate stack-up cannot be dimensioned until those heights come from the exact drawings or 3D models.

## 2. Installed orientation and Board P interference

- Board B hangs **component face down** on its legs. A plate on the component side sits **below** the parts, between them and the floor or enclosure base. Warm air rises away from it, so a component-side plate mainly spreads heat; it adds little convection.
- The **back side (B.Cu) faces up** and carries no SMD parts, only through-hole tails (J5, J6, J7, J10, J11) and back silk. It is the flat, upward-facing surface.
- **Board P occupies Board B x ≈ −0.5…39.5, y ≈ 12…39** on the component side (27 × 40 mm, transformed), with its own components facing down toward Board B. U3 (23, 36), D2 (33.75, 35) and J5 (37.2, 24.9) sit inside that extent; C39 (43, 21.5) and C8 (34, 41) are outside it. **No component-side plate can reach U3 on the existing stack**: the space between U3's top and Board P's hanging components is not measured and is already the tightest region of the stack.
- Leg seating height is 18 mm (adhesive-leg prototype); the terminal drawing maximum reaches 14.2 mm and Board P substrate 12.7 mm (CLAUDE.md). A component-side plate plus pad must stay inside that floor clearance; the margin is not established.

## 3. Proposed plates (concept; dimensions indicative, not designed)

### Renewal Board B as built (no PCB change)

| Plate | Side | Covers | Potential under it | Mounting idea (not designed) |
|---|---|---|---|---|
| **A. Right LDO strip** | Component side | U6 + U7 body tops, cutouts around C40 / C41 / C21 / C4 / 1210s; about 16 × 30 mm | GND tabs only | No free hole nearby. The corner holes H4/H6 are taken by the leg screws (see plate D) and are about 30 mm away. Pad adhesion is not a retention method. Needs new holes (next revision) or an enclosure-side clamp |
| **B. Negative LDO** | Component side | U8 body top, cutouts for C42, C11 and the J11 shroud; about 16 × 14 mm | **−14.145 V** | As A; must not touch plate A or anything at GND unless the pad insulates it |
| **C. Inverting stage** | Component side | U4 + L3 tops (pads of different thickness bridge the height step), cutouts for C7, C9, C24, C12, J10, J7; about 40 × 20 mm | **−14.145 V** (U4 tab), **switch node** (L3 pin 1 / D3), GND (L3 pin 2) | No free hole; the corner holes carry the leg screws, and a bar from them would be long and cross Board P |
| **D. Back-side spreader (alternative to A/B)** | **Back (up-facing)** | Over the U6, U7 and U8 thermal-via fields (and optionally U4), through an insulating pad on solder mask | GND (U6/U7 pours) **and −14.145 V** (U4/U8 pours) under one plate | **No usable mount on the current board.** All holes are NPTH and unconnected, but the corner holes H4/H6 cannot carry a plate: the leg's M3 × 5 screw inserts only 3.4 mm through the 1.6 mm PCB into the leg's 4.5 mm blind bore, so any plate plus pad under the head cuts engagement further; the holes are 3.0 mm with zero diametral clearance for M3; and H4/H6 at x = 106 are about 30 mm from the via fields at x 74–77. A longer screw changes the adhesive-leg fit candidate and is not proposed. Without new holes, plate D needs a non-screw retention (e.g. an enclosure lid pressing it), which is unproven. Avoid J10/J11/J5/J6/J7 tails |

Plate D is the one with a useful heat path: tab → pour → 12 vias → back pour → pad → plate, with the plate facing up. Component-side plates A–C touch plastic package tops, whose junction-to-top resistance is UNAV and usually much larger than the tab path; their benefit is uncertain.

### Next-revision options (would change the PCB; not proposed for adoption)

- Move U3 (and D2) out from under Board P, or give U3 thermal vias like U4/U6/U7/U8 (it has none listed).
- Group the GND-tab parts (U3, U6, U7) and the −14.145 V parts (U4, U8) into two regions so each region can have one plate at one potential.
- Add **plated or NPTH mounting holes reserved for plates** next to each group, with keep-outs for screw heads and washers on both sides.
- Open solder mask (exposed copper) only where an insulating pad is guaranteed to sit, or keep mask and rely on the pad; decide one way, per potential.
- Keep electrolytics out of the plate footprint and away from the hot parts (see §4.4), and route switch nodes away from plate edges.

## 4. Analysis

### 4.1 Tab potentials and insulation

- Two potentials carry the heat: **GND** (U3, U6, U7) and **−14.145 V PRE** (U4, U8). Switch nodes (L2/L3 pin 1, D2/D3 cathodes, U2_SW, L1 pin 1) swing between rails at the switching frequency.
- A metal plate that touches parts of both potentials, or a GND part and a switch node, through anything but an intact insulator **shorts a rail**. The 14 V difference is low-voltage, so the concern is functional shorts and burr punch-through, not safety creepage. No creepage requirement is derived here.
- For the owner's aluminum-PCB plate stack (mask and silk facing the parts), see §B.2; its verdict is **not qualified** until tested.
- **Solder mask is not a rated insulator** (dielectric strength and pinhole rate UNAV for this fab). Do not count it.
- The pad's dielectric strength is **UNAV** (sales claim only). Until an insulation test exists, keep one potential per plate: A at GND, B and the U4 part of C at −14.145 V, and **no plate over a switch node** (cut L3's pin-1 side and D3 out of plate C, or split C).
- A floating plate (no connection to any net) avoids a hard short but couples capacitively to every node beneath it (see 4.5).

### 4.2 Pad thickness versus thermal resistance (calc; k is UNAV)

R_pad = t / (k · A). Conductivity k is swept over 1 / 3 / 6 W/m·K as a PA range; the listing's 24 W/m·K is not used.

| Contact | k (W/m·K) | t = 0.5 mm | 1.0 mm | 1.5 mm | 2.0 mm |
|---|---|---|---|---|---|
| TO-263 body top, about 10 × 9 mm (90 mm²) | 1 | 5.6 K/W | 11.1 | 16.7 | 22.2 |
| | 3 | 1.9 | 3.7 | 5.6 | 7.4 |
| | 6 | 0.9 | 1.9 | 2.8 | 3.7 |
| Back via field, about 15 × 15 mm (225 mm²) | 1 | 2.2 | 4.4 | 6.7 | 8.9 |
| | 3 | 0.7 | 1.5 | 2.2 | 3.0 |
| | 6 | 0.4 | 0.7 | 1.1 | 1.5 |

Using a thicker pad to bridge a height step costs resistance linearly. The mask, the interface contact resistance and the package junction-to-top resistance add to these and are UNAV.

**The plate's own path to air dominates.** Natural convection at h = 5–10 W/m²K (PA) on both faces, no radiation credit:

| Plate | Plate-to-air resistance |
|---|---|
| 16 × 30 mm (A) | 104–208 K/W |
| 30 × 40 mm | 42–83 K/W |
| 40 × 75 mm (D-sized) | 17–33 K/W |
| 60 × 80 mm | 10–21 K/W |

Against the screened θJA limits (about 20 K/W for U6, 24 K/W for U8), a small cutout plate in free air adds a weak parallel path; it mostly evens out temperatures between parts. Only a large plate (D-sized or bigger), or a plate pressed against an enclosure wall, approaches the scale of the existing PCB path. None of this is a thermal rating.

### 4.3 Clamping load and compression

- Gap pads need compression to make contact (the old page's "10–20 %" is a vendor tip, not evidence). Force versus deflection for this pad is UNAV.
- On the component side the load lands on SMD package bodies and, through them, on solder joints. TO-263 / DD-PAK tabs tolerate some load; **inductor tops and 0805/1210 MLCCs do not have a published compression rating** (UNAV). MLCC cracking under board flex is a known failure mode; keep plates off MLCCs and away from the board areas between support points.
- A clamp bar between distant holes would span tens of mm, so screw torque bends the bar and the board and the load per part is uncontrolled; on renewal Board B the corner holes are also not available (leg screws). A back-side plate (D) loads the flat back surface instead, which spreads the force over the board rather than individual joints.
- Pads relax over time (compression set UNAV), so a pad-only retention is not a mechanical fixing.

### 4.4 Capacitor vents and heat keep-outs

- Electrolytics C5, C7, C12, C21, C24, C25 (470 µF, 10 mm cans), C9, C11 (8 mm), C4, C22, C23 (6.3 mm) and the 47 µF polymer cans C40 / C41 / C42 (6.3 mm) beside the LDOs, inside plates A and B, carry pressure vents or can tops on their tops. Plates must leave the vent area free (a vent clearance value is UNAV for these exact parts) and must not press on a can.
- A plate that spreads heat sideways can raise the temperature of nearby electrolytics; their life is temperature-driven. Plates should cut out around cans, not just above them.
- With the board face down, a can's top faces down toward the plate side; any plate below it blocks vent release.

### 4.5 PCB thermal paths and EMI

- Existing paths: 12 thermal vias each at U4, U6, U7, U8; U3 has none listed. U6 and U7 share connected system-ground copper, which cannot be credited to each one separately (power-budget.md).
- A conductive plate near a **switch node** (L1/L2/L3 pin 1, D2/D3, U2_SW) forms a capacitor to it and can radiate or couple switching noise into the plate and anything it touches. A plate over the GND pour, grounded at one point, shields; a floating plate near switch nodes can make EMI worse. Grounding a plate through a screw needs a plated GND hole, which the current board does not have.
- A plate shared by GND and −14.145 V regions must float or sit on one potential with insulation over the other.

## 5. Comparison and recommendation (marked, not adopted)

| Approach | Thermal benefit (calc) | Main risks | Board change |
|---|---|---|---|
| A + B + C component-side cutout plates | Small: plastic-top contact, 40–200 K/W to air for small plates | Shorts across potentials; switch-node coupling; MLCC and can loading; no mounting holes; U3 unreachable under Board P | None, but retention is unsolved |
| D back-side spreader over via fields | Largest available: via path, up-facing plate, large area | Two potentials under one plate (insulation UNAV); burr punch-through; THT tails; floating-plate coupling | Needs new holes or an enclosure clamp; corner holes unusable |
| Next-revision regrouping + plate holes | Can combine the via path with one potential per plate | Layout work; re-verification | PCB change (gated) |

**Recommendation (marked).** The arrived board is the renewal Board B (owner-stated; §A's plates V1–V4 apply only to the historical combined board). For it, and for the next revision, prefer the back-side spreader D over the via fields, split into a GND plate (U6/U7) and a −14.145 V plate (U8, optionally U4), each on an insulating pad, rather than component-side cutout plates. Build plates from the owner's aluminum blank-panel construction with the masked face toward the parts (§B), but count none of the stack as insulation until H1b passes. Treat any plate as unproven until measured. Fold plate holes, potential grouping and U3's position into the next revision instead of working around them now.

## 6. Proposed measurements (not executed; each needs owner approval)

| ID | What | Method (proposal) |
|---|---|---|
| H1 | Pad properties | Measure thickness before and after compression, and insulation (DC withstand at a modest voltage) on pad samples; no reliance on the listing |
| H1b | Plate stack insulation | DC withstand and insulation resistance from tab to aluminum core through pad + silk + mask + dielectric, under the intended clamp load, on cut samples; include edge and hole walls |
| H2 | Fit | Dry-fit plates and pads on an unpowered board; record the gap stack, contact and floor clearance face-down |
| H3 | Thermal | Board under defined load with thermocouples on U6, U7, U8, U4 tabs and nearby cans, with and without each plate, face-down at a stated ambient |
| H4n | EMI / noise | Output ripple and noise on each rail with and without plates (grounded and floating) |
| H5 | Mechanical | Board flex and joint inspection after clamping |

H3 and H4n involve energizing the board, which is not authorized by this request.
