---
sidebar_position: 7
---

# v3 Test Point Planning

Adding deliberate test points to v3, driven by the v2 debug experience where QFN-24 chip pins were physically impossible to probe with a multimeter and we had to remove U1 with hot-air to confirm the chip-side fault. Pogo pads and labeled test pads cost essentially nothing on the BOM, and turn 30-minute scope hunts into 30-second multimeter checks.

## The lesson from v2

During PCBA v2 debug:

- We suspected the STUSB4500 CC1DB pin was internally shorted to GND, but couldn't measure it directly — the QFN-24 pin pitch is 0.5 mm and the pin sits under the IC body
- We had to **hot-air remove U1** from one of the boards to confirm the PCB pad was open to GND with the chip off → proving the chip itself was the short
- Cost: one PCBA sacrificed, several hours of work, no margin for repeat testing
- If CC1DB had been brought out to a 1 mm pogo pad, the entire diagnosis would have taken 5 seconds with a multimeter

This page lists which nets are worth bringing out to test points on v3, why, and how to implement them.

## Existing test points (already in v2)

| Ref | Net | Location | Type |
| --- | --- | --- | --- |
| TP1 | +15V USB-PD | usb-pd-input | TestPoint |
| TP2 | GND | usb-pd-input | TestPoint |
| TP3 | +13.5V (DC-DC out, before +12V LDO) | dc-dc-conversion | TestPoint |
| TP4 | +7.5V (DC-DC out, before +5V LDO) | dc-dc-conversion | TestPoint |
| TP5 | -13.5V (DC-DC out, before -12V LDO) | dc-dc-conversion | TestPoint |
| J2 | VBUS / SCL / SDA / GND (NVM programming) | usb-pd-input | PogoPad_1x04 |

Reasonable coverage of the power rails. **Gaps**: the entire STUSB4500 chip-side signal set, and the -15V SEPIC inverter output node.

## New test points — STUSB4500 chip area

### Tier 1 — Essential (the ones we needed during v2 debug)

| Signal | Source | Why it's needed |
| --- | --- | --- |
| **CC1** (USB-C side, after USBLC6 D4) | USB-C connector net | Verify Rd voltage, watch source negotiation handshake |
| **CC2** (USB-C side, after USBLC6 D4) | USB-C connector net | Same |
| **CC1DB** (chip pin 1, chip-side) | STUSB4500 pin 1 | Detect chip-internal short (the v2 fault) — single most useful TP |
| **CC2DB** (chip pin 5, chip-side) | STUSB4500 pin 5 | Same |

> **Note on CC1DB / CC2DB pads on a built v3 board**: v3 ties both CC1DB and CC2DB to GND through a **0 Ω 0603 jumper** (R19 / R20, LCSC C21189) rather than a hard short. Electrically identical (0 Ω), but the resistor preserves the names `CC1DB` / `CC2DB` as distinct nets between the chip pin and the resistor. That gives the J3 pogo pads a unique trace to probe — touching pad 1 actually verifies continuity to U1 pin 1, not just "somewhere on the GND pour." On every healthy board the pads still read **0 V**, so they function as *GND-tie verifiers* (does U1 pin → R19/R20 → GND still measure 0 Ω end-to-end?). For deeper debug, R19/R20 can be lifted to isolate U1's CC1DB / CC2DB pins from GND without touching the IC. If a future chip batch turns out to have working internal Rd, replacing R19/R20 with a populated/DNP scheme that routes back to CC1/CC2 restores dead-battery wiring with no further board respin.
| **VREG_2V7** | STUSB4500 VREG_2V7 pin | Chip's internal 2.7 V regulator. Present only when chip is alive and configured — the canonical "is the chip awake?" indicator |
| **VDD / VSYS** (chip supply) | Chip supply pin (post-MOSFET load switch) | Confirms VBUS path reached the chip after Q1; catches blown fuse, dead MOSFET, broken trace |

These six are the minimum useful set. If only one pogo block fits, this is it.

### Tier 2 — Strongly recommended (chip state outputs)

| Signal | Source | Why it's useful |
| --- | --- | --- |
| **ATTACH** | STUSB4500 ATTACH pin | Chip asserts when USB-C device is detected — proves the CC handshake completed |
| **PD_OK** | STUSB4500 PD_OK pin | Chip asserts when PD negotiation succeeded — proves 15V was negotiated |
| **VBUS_EN_SNK** | STUSB4500 VBUS_EN_SNK pin | Drives Q1 (AO3401A) gate. If this is wrong, the load switch never opens even when negotiation succeeds |
| **RESET** | STUSB4500 RESET pin | The pin-6 reset state question we raised during v2 debug — answer it in 1 second with a multimeter, not by re-tracing the schematic |

These would have shortcut several v2 hypotheses: "is the chip booting?", "did negotiation finish?", "is the load switch being commanded on?". Each can fail independently.

### Tier 3 — Nice to have

| Signal | Why |
| --- | --- |
| **ALERT#** | Chip interrupt output; useful when paired with I2C session debugging |
| **A_B_SIDE** | Chip's cable-orientation detection result |
| **GPIO** | If used in NVM configuration |

Add these only if the pogo block has spare positions.

## New test points — Power chain (other areas)

### DC-DC / linear regulator chain

Current TPs cover the DC-DC outputs but not every intermediate. Gaps worth adding:

| Signal | Reason |
| --- | --- |
| **-15V** (SEPIC inverter output, before -13.5V buck) | Currently no TP — if -12V output is wrong, you need to know whether -15V or -13.5V or -12V is the failing stage |
| **VBUS_DISCH** (post-470Ω discharge node) | Verifies discharge path works on disconnect |

The final output rails (+12V / +5V / -12V) appear on the output connectors and are easy to probe there — no separate TP needed.

## Already covered, skip

- **SCL, SDA** — on J2 (programming pogo block)
- **VBUS at USB-C connector** — accessible at the connector pins
- **+15V, GND** — TP1 / TP2

## Implementation

### Recommended layout: hybrid pogo block + scattered TPs

**A) Second pogo pad block near U1** — for the chip-side signals that physically cluster around the QFN:

Suggested 1×8 block (Tier 1 chip-side + most of Tier 2):

```
Pad 1: CC1DB
Pad 2: CC2DB
Pad 3: VREG_2V7
Pad 4: VDD
Pad 5: RESET
Pad 6: ATTACH
Pad 7: PD_OK
Pad 8: VBUS_EN_SNK
```

Reuses the J2 style (2.54 mm pitch pogo pads) so the same probe clip works. Needs a new footprint variant — call it `PogoPad_1x08_P2.54mm` modeled on the existing `PogoPad_1x04_P2.54mm` in `footprints/kicad/zudo-power.pretty/`.

**B) Individual TP pads** for signals that are far from U1 or sensitive to long traces:

| TP | Signal | Reason for individual pad (not in block) |
| --- | --- | --- |
| TP6 | CC1 (USB-C side) | Long trace to U1 pogo block would add stub capacitance on the CC line |
| TP7 | CC2 (USB-C side) | Same |
| TP8 | -15V | Lives in dc-dc-conversion sheet, far from U1 |
| TP9 | VBUS_DISCH | Lives near the discharge resistor R13 |

Use the existing `Connector:TestPoint` symbol (same style as TP1–TP5).

### Why a pogo block for the chip-side signals?

- One clip captures all 8 signals at once — useful for scope captures correlating ATTACH ↔ PD_OK ↔ VBUS_EN_SNK timing during negotiation
- Pogo pads are PCB-only (no SMT component), so zero JLCPCB assembly cost
- Same probe tooling as J2 — no new fixture to build

### Why individual TPs for the CC lines?

- CC1 / CC2 are the most signal-integrity-sensitive nets on the board (USB-PD BMC at ~600 kHz, 50 Ω target characteristic impedance)
- A trace stub to a centrally-located pogo block would add ~10–30 mm of unused trace = parasitic capacitance that could affect detection at the source
- Better to put a small TP pad right where the CC trace already runs, near the USB-C connector

## Pad geometry and labeling rules

### Pogo pad geometry

Reuse the existing `PogoPad_1x04_P2.54mm` style:

- Round or rectangular pads, ~1.5–2.0 mm diameter
- 2.54 mm pitch (standard pogo clip spacing)
- No soldermask over the pad
- Pad-only (no plated through-hole) — pogo pin is spring-loaded and pressed against the surface

### Individual TP pads

The existing `Connector:TestPoint` footprint is fine. Round pad, ~1 mm with sufficient annular ring.

### Silkscreen labels — mandatory

Every test pad must have a **short signal-name label** on silkscreen, directly adjacent:

- `CC1DB`, `CC2DB`, `VREG2V7`, `VDD`, `RESET`, `ATTACH`, `PDOK`, `VBUSENSNK` (drop punctuation that's not silkscreen-friendly)
- For the pogo block, label each pad position (or label the block ends with pin 1 indicator + a printed legend)
- Don't rely on schematic reference designators alone — `TP6` doesn't tell the operator what they're probing

### Visual identification on the board

Add a small filled silkscreen marker (triangle, dot, or pin-1 arrow) next to each pogo block pin 1, matching the convention used on J2.

## v3 implementation checklist

- [ ] Create new footprint `PogoPad_1x08_P2.54mm` (copy `PogoPad_1x04_P2.54mm`, extend to 8 positions)
- [ ] Add Tier 1 + Tier 2 pogo block (J3) to `usb-pd-input.kicad_sch` using `Conn_01x08`
- [ ] Add individual TPs to `usb-pd-input.kicad_sch`: CC1 (TP6), CC2 (TP7), VBUS_DISCH (TP9)
- [ ] Add individual TP to `dc-dc-conversion.kicad_sch`: -15V (TP8)
- [ ] Confirm silkscreen labels are readable at silkscreen min line width (typically 0.15 mm)
- [ ] Place pogo block near U1 with clear single-side access (not blocked by tall components)
- [ ] Re-run ERC + DRC
- [ ] Update BOM with new connector (Conn_01x08 with custom pogo footprint — no LCSC part needed, it's a PCB pattern)
- [ ] Update `pcba-v2-debug.md` to note that v3 includes test pads for future diagnosis

## Future-proofing note

The "if a future chip batch behaves differently" scenario is already much easier to validate with these test points:

- Plug a fresh PCBA into a USB-C source with NO PD negotiation expected
- Multimeter on CC1DB pogo pad → should read GND (not floating, not a short to CC1) for our broken-chip wiring
- Multimeter on VREG_2V7 → should read 2.7 V if chip wakes up
- Multimeter on PD_OK → should toggle high when negotiation succeeds

This is a 30-second pre-shipment QA check that catches the v2 failure mode without sacrificing any boards.
