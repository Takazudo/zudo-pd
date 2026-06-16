# PD Schematic Review Report

**Skill:** `pd-schematic-review` (Approach C, sub-issue #76 of epic #68)
**Board:** zudo-pd USB-PD modular-synth power supply, version 0.4.0 (4th JLCPCB order)
**Date:** 2026-06-17
**Method:** read-only KiCad netlist export → pin→net map → datasheet-checklist review.
**Inputs:**

- `zudo-pd.kicad_sch` (root) → exported with KiCad CLI 10.0.0:
  `kicad-cli sch export netlist --format kicadxml -o __inbox/zudo-pd-netlist.xml zudo-pd.kicad_sch`
  (also `--format kicadsexpr -o __inbox/zudo-pd-netlist.net`). Exports kept in `__inbox/`
  (gitignored), not committed.
- 87 components parsed; pin→net topology read from the **actual nets**, not symbol positions.

> **READ THIS FIRST — findings are leads, not verdicts.** Every item below is a *lead to
> verify against the datasheet*, never ground truth. This is a static net-topology pass: it
> can confirm what connects to what and recompute divider math, but it cannot measure
> voltages, simulate loops, judge thermals, or check the PCB. Sources are cited per finding so
> you can confirm each one. See "What this pass can and cannot catch" at the end.

---

## Part map (from the export — confirm each run, the BOM can change)

| Ref | Part | Role | Source for review |
| --- | --- | --- | --- |
| U1 | STUSB4500QTR | USB-PD sink controller, negotiates 15 V | repo docs + ST DS12499 (web) |
| Q1 | AO3401A | P-ch VBUS load switch | `components/ao3401a.md` |
| U2 | LM2596S-ADJ | DC-DC +15 V → +13.5 V (for +12 V rail) | `datasheets/LM2596S-datasheet.pdf` + `components/lm2596s-adj.mdx` |
| U3 | LM2596S-ADJ | DC-DC +15 V → +7.5 V (for +5 V rail) | same |
| U4 | LM2596S-ADJ | DC-DC **inverting** → −13.5 V (for −12 V rail) | same |
| U6 | L7812CD2T | LDO +13.5 V → +12 V | `datasheets/L7812CD2T-datasheet.pdf` + `components/l7812cv.md` |
| U7 | L7805ABD2T | LDO +7.5 V → +5 V | `datasheets/L7805ABD2T-datasheet.pdf` + `components/l7805abd2t.md` |
| U8 | CJ7912 | LDO −13.5 V → −12 V | `datasheets/CJ7912-datasheet.pdf` + `components/cj7912.md` |

> **Designator note:** the issue text calls the STUSB4500 "U0"; the actual netlist uses **U1**.
> Reviewed as U1.

---

## USB-PD stage — STUSB4500 (U1)

**Datasheet source for this stage:** primary = repo docs
`doc/src/content/docs/inbox/stusb4500-pinout.md`, `doc/src/content/docs/inbox/v3-pd-failure-diagnosis.md`,
`doc/src/content/docs/components/stusb4500.md` (these distill the ST datasheet and the v3 root
cause). External = **ST DS12499** — the direct PDF fetch timed out, but a web search returned
ST's authoritative pin-18 description (below). **There is no local STUSB4500 PDF**, so every
electrical *value* below is flagged "verify against ST DS12499."

### F-1 — VBUS sense path (the v3 fix) — CONFIRMED PRESENT ✅ (blocker-class check)

**Net evidence (from export):**

```
VBUS_VS_DISCH net = { U1.18 (VBUS_VS_DISCH), R14.2, TP6.1 }
VBUS_IN net       = { U1.24 (VDD), Q1.2 (S), R14.1, R11.2, C1.2, C2.2, D4.5, J1.A9/B9, J3.4 }
  ⇒ U1.18 ── R14 (470 Ω) ── VBUS_IN     (NO GND on the pin-18 net)
```

The pin-18 net reaches **VBUS_IN through R14 (470 Ω)** and touches a test point (TP6); it does
**not** touch GND anywhere. This is exactly the 0.4.0 fix for the v3 blocker (v3 had
`pin 18 → R14 → GND`, so the chip never saw VBUS and never asserted the sink path).

- **Lead to verify:** ST DS12499 confirms VBUS_VS_DISCH is the VBUS-monitoring input that
  checks VBUS is in a valid window before enabling the power path via VBUS_EN_SNK, and requires
  a **current-limiting series resistor** (max discharge current 50 mA). 470 Ω is the value the
  repo's v1-debug intent and `stusb4500-pinout.md` specify. **Verify against ST DS12499 Fig. 10
  whether a bare series R or a divider is the recommended topology**, and that 470 Ω keeps
  discharge ≤ 50 mA (15 V / 470 Ω ≈ 32 mA — within spec, OK).
- **Source:** net export (ground truth for topology) + `stusb4500-pinout.md` (pin 18 row) +
  `v3-pd-failure-diagnosis.md` (root-cause + fix) + ST DS12499 via WebSearch
  ("STUSB4500 ... VBUS monitoring block supervises VBUS ... from VBUS_VS_DISCH input pin ...
  current limiting serial resistor recommended, max discharge 50 mA").
- **Severity:** OK-confirmed. This was the whole v3 story; it is now correct in the schematic.

### F-2 — VBUS_EN_SNK → Q1 load switch — CONFIRMED ✅

**Net evidence:** `U1.16 (VBUS_EN_SNK) → VBEN → R12.1`; `R12.2 → Q1.1 (G)`; `R11 (100 k) from
VBUS_IN to Q1 gate`; `Q1.2 (S) → VBUS_IN`, `Q1.3 (D) → "+15V -> +13.5V gen"` (the VBUS_OUT
rail, oddly net-named). AO3401A is a P-channel MOSFET: source at VBUS_IN, gate pulled up to
VBUS_IN by R11 (off by default), pulled low by the chip via VBEN/R12 to turn on. Correct
high-side load-switch topology.

- **Lead to verify:** R12 gate series + R11 pull-up values vs AO3401A gate charge / turn-on
  time — fine for a slow enable. **Source:** export + `components/ao3401a.md`. **Severity:** OK.

### F-3 — VDD supply + decoupling — CONFIRMED ✅

`U1.24 (VDD) → VBUS_IN`, decoupled by **C1 (10 µF) + C2 (100 nF)** on that net.

- **Lead to verify:** VBUS can be 15 V; STUSB4500 VDD operating range is ~4.1–22 V per repo
  doc (`components/stusb4500.md`: "VDD 4.1–22 V"). 15 V is comfortably inside. **Verify the
  22 V abs-max against ST DS12499** (repo doc value, not from a local PDF). C1/C2 voltage
  ratings (25 V) exceed 15 V. **Source:** export + `components/stusb4500.md`. **Severity:** OK.

### F-4 — VREG_2V7 / VREG_1V2 / VSYS / EP — CONFIRMED ✅

`U1.23 (VREG_2V7) → C30 (1 µF) decap`; `U1.21 (VREG_1V2) → C34 (1 µF) decap`;
`U1.22 (VSYS) → GND`; `U1.25 (EP) → GND`; `U1.10 (GND) → GND`.

- **Lead to verify:** the two internal-regulator outputs each have a 1 µF decap (repo doc
  recommends this). VSYS-to-GND is correct for a VBUS-only (non-battery) board. EP grounded.
  **Verify the 1 µF VREG decap values against ST DS12499.** **Source:** export +
  `stusb4500-pinout.md` + `components/stusb4500.md`. **Severity:** OK.

### F-5 — CC pins, ADDR straps, RESET — CONFIRMED ✅

`U1.2 (CC1)` and `U1.4 (CC2)` each have a 5.1 kΩ Rd to GND (R17, R18) — correct sink Rd.
`U1.1 (CC1DB)`/`U1.5 (CC2DB)` to GND via 0 Ω (R19/R20). `U1.12 (ADDR0)`+`U1.13 (ADDR1)` → GND
⇒ I²C addr 0x28. `U1.6 (RESET) → GND` (held low = run). `U1.7/8 (SCL/SDA)` to pull-ups.

- **Lead to verify:** 5.1 kΩ Rd is the USB-C spec value for a sink advertising default current;
  the actual current is set by the NVM PDO (15 V). **Source:** export + `stusb4500-pinout.md`
  (CC rows) + `v3-pd-failure-diagnosis.md` (addr 0x28 matches programmer). **Severity:** OK.

### F-6 — DISCH (pin 9) — VERIFY ⚠️ (minor)

`U1.9 (DISCH) → Net-(U1-DISCH) → R13 (470 Ω) → "+15V -> +13.5V gen"` (VBUS_OUT side).

- **Lead to verify:** DISCH is a discharge-path pin distinct from VBUS_VS_DISCH. `components/
  stusb4500.md` documents `DISCH → R13 (470 Ω) → VBUS_OUT` as intended. `v3-pd-failure-diagnosis.md`
  marks pin 9 "check (minor, not a blocker)." **Confirm against ST DS12499 whether DISCH should
  tie to the VBUS rail via R or be left to internal handling.** **Source:** export +
  `components/stusb4500.md`. **Severity:** verify (minor).

---

## DC-DC stage — LM2596S-ADJ (U2 / U3 / U4)

**Datasheet source:** `doc/public/datasheets/LM2596S-datasheet.pdf` +
`doc/src/content/docs/components/lm2596s-adj.mdx`. Vref = **1.23 V**; ON/OFF (pin 5):
**Low/Float = ON, High = shutdown**; Vin range 4.5–40 V (abs-max 45 V).

### F-7 — Feedback dividers recomputed — CONFIRMED ✅

`Vout = 1.23 V × (1 + Rtop/Rbottom)`, recomputed from the **actual** divider resistors in the
export:

| Rail | Top R (to Vout) | Bottom R (to GND ref) | Computed Vout | Target | Verdict |
| --- | --- | --- | --- | --- | --- |
| +13.5 V (U2) | R1 = 10 k | R2 = 1 k | 1.23·(1+10) = **13.53 V** | 13.5 V | ✅ |
| +7.5 V (U3) | R3 = 5.1 k | R4 = 1 k | 1.23·(1+5.1) = **7.50 V** | 7.5 V | ✅ |
| −13.5 V (U4) | R6 = 1 k (to −13.5 OUT) | R5 = 10 k (to GND) | inverting: see F-9 | −13.5 V | ✅ topology |

Net evidence: `U2.4 (FB) = {R1.1, R2.2}`, `R1.2 → +13.5 OUT`, `R2.1 → GND`. Same shape for U3.
C31/C32/C33 (22 nF) are FB-compensation caps in parallel with the top resistor.

- **Lead to verify:** the divider math matches the `lm2596s-adj.mdx` worked examples exactly
  (13.53 V, 7.50 V). **Source:** export + `lm2596s-adj.mdx`. **Severity:** OK-confirmed.

### F-8 — ON/OFF (enable) pins — CONFIRMED ✅

`U2.5 → GND`, `U3.5 → GND` (Low = ON, correct). `U4.5 → −13.5 V OUT` (U4's local "GND",
i.e. its enable is tied to its own reference = ON; see F-9).

- **Lead to verify:** LM2596 ON/OFF Low/Float = ON per `lm2596s-adj.mdx`. **Source:** export +
  `lm2596s-adj.mdx`. **Severity:** OK.

### F-9 — U4 is an INVERTING LM2596 (not a SEPIC / not a LM2586) — DOC DISCREPANCY ⚠️

**Net evidence:** `U4.3 (Gnd)`, `U4.5 (ON/OFF)`, `U4.6 (TAB)` **all tie to `−13.5 V OUT`**, and
`U4.1 (Vin) → +15 V gen`, `U4.2 (Output) → D3.K + L3.1`, `D3.2 (A) → −13.5 V OUT`,
`L3.2 → GND`. This is the **classic LM2596 inverting buck-boost** configuration: the
regulator's ground reference sits at the negative output, the catch diode points to the
negative rail, and the inductor returns to system GND.

- **Discrepancy to resolve:** the repo `CLAUDE.md` / architecture text describes the negative
  rail as "−15 V (LM2586SX-ADJ **inverted SEPIC**) → −13.5 V". The **actual schematic uses a
  third LM2596S-ADJ (U4) in an inverting topology**, not an LM2586 SEPIC. The
  `lm2596s-adj.mdx` doc's U4 section ("−15 V → −13.5 V, same as U2") also doesn't describe the
  inverting wiring explicitly. **Lead to verify:** confirm the input-voltage stress on an
  inverting LM2596 — in this topology the switch sees roughly `|Vin| + |Vout|` ≈ 15 + 13.5 ≈
  **28.5 V** across the part, well under the 40 V/45 V max but worth confirming against the
  LM2596 datasheet's inverting-application note and the inductor/diode current ratings for
  buck-boost (peak current is higher than a simple buck).
- **Source:** export (topology) + `LM2596S-datasheet.pdf` (inverting app note) vs repo
  `CLAUDE.md` text. **Severity:** verify — likely a stale doc, but the abs-max stress on an
  inverting converter is a real lead to check.

### F-10 — Catch diodes / inductors / input caps — CONFIRMED ✅ (values to verify under load)

D1/D2/D3 = SS34 (3 A/40 V Schottky); L1/L2/L3 = 100 µH; bulk input/output electrolytics
(C3/C4/C5/C7/C9/C11/C14/C20/C21/C24/C25, 100–470 µF) present on each rail.

- **Lead to verify:** SS34 3 A and L = 100 µH ratings vs the **peak** inductor current at each
  rail's load — buck-boost (U4) peak current is notably higher than buck. Recompute peak
  current and ripple against the LM2596 datasheet design equations. Confirm electrolytic
  voltage ratings exceed each rail (25 V parts on 13.5 V rails = OK; check the 16 V parts).
  **Source:** export + `LM2596S-datasheet.pdf` + `lm2596s-adj.mdx`. **Severity:** verify (this
  static pass cannot compute currents under load).

---

## Linear-regulator stage — LDOs (U6 / U7 / U8)

**Datasheet source:** local PDFs `L7812CD2T-`, `L7805ABD2T-`, `CJ7912-datasheet.pdf` + the
matching `components/*.md`. All three: ~2 V typical dropout, 1.5 A max, ±4 % output.

### F-11 — +12 V LDO (U6 L7812): DROPOUT MARGIN THIN — VERIFY ⚠️ (the flagged thin-rail case)

**Net evidence:** `U6.1 (IN) → +13.5 V OUT`, `U6.3 (OUT) → Net-(U6-OUT)`, `U6.4 → GND`.
Input bulk: C3/C20 (470 µF) + C14 (470 nF) + C17 on output side; output → PTC1 → +12 V rail.

- **Headroom:** `13.5 − 12 = 1.5 V` against a **~2 V typical dropout**. The local doc
  `components/l7812cv.md` itself flags this: **"⚠️ Marginal — operates near minimum dropout
  voltage,"** and recommends raising the DC-DC to 14.0 V for production.
- **Lead to verify:** dropout is current- and temperature-dependent; at 1.2 A and worst-case
  hot/low-line, 1.5 V may be insufficient → +12 V could droop / lose regulation. **Verify the
  dropout-vs-current curve in `L7812CD2T-datasheet.pdf`** at 1.2 A. Also note the DC-DC actually
  regulates to ~13.53 V (F-7), giving a hair more, but still under 2 V. **Source:**
  `components/l7812cv.md` (explicit ⚠️) + `L7812CD2T-datasheet.pdf`. **Severity:** marginal —
  the strongest "thin intermediate-rail margin" lead on the board.

### F-12 — +5 V LDO (U7 L7805): dropout OK ✅

**Net evidence:** `U7.1 (IN) → +7.5 V OUT`, `U7.2 → GND`, `U7.3 (OUT) → Net-(U7-OUT) → PTC2 →
+5 V rail`. Headroom `7.5 − 5 = 2.5 V` ≥ ~2 V dropout.

- **Lead to verify:** 2.5 V margin is comfortable at 0.5 A; `components/l7805abd2t.md` marks it
  "✅ Excellent." Confirm thermals: `P = (7.5−5)·0.5 = 1.25 W` (doc: Tj ≈ 69 °C). **Source:**
  `components/l7805abd2t.md` + `L7805ABD2T-datasheet.pdf`. **Severity:** OK.

### F-13 — −12 V LDO (U8 CJ7912): polarity + thin margin — VERIFY ⚠️

**Net evidence:** `U8.1 (GND) → GND`, `U8.2 (VIN) → −13.5 V OUT`, `U8.3 (OUT) → Net-(U8-OUT) →
PTC3 → −12 V rail`. Note the negative-regulator pinout (GND/IN/OUT = pins 1/2/3) differs from
the positive parts — the export confirms IN is on pin 2, OUT on pin 3, GND on pin 1, matching
`components/cj7912.md`.

- **Headroom:** `|−13.5| − |−12| = 1.5 V` against ~2 V dropout — **same marginal case as the
  +12 V rail (F-11)**, at 0.8 A.
- **Lead to verify:** (a) dropout-vs-current for CJ7912 at 0.8 A in `CJ7912-datasheet.pdf`;
  (b) **electrolytic polarity** on the negative rail — `components/cj7912.md` is explicit that
  C21 (input) and C22 (output) have their **negative terminal toward the −13.5 V / −12 V node
  and positive terminal to GND**. Verify the symbol polarity in the schematic matches (a flipped
  electrolytic on a negative rail is a classic failure). **Source:** export +
  `components/cj7912.md` + `CJ7912-datasheet.pdf`. **Severity:** marginal (dropout) + verify
  (polarity).

### F-14 — Output protection (PTC fuses + TVS) — CONFIRMED present ✅

Each LDO output passes through a PTC resettable fuse (PTC1/PTC2/PTC3) before the rail, and each
rail has a TVS (TVS1 SMAJ15A on +12, TVS2 SD05 on +5, TVS3 SMAJ15A on −12) and a status LED via
1 k series (R7/R8/R9).

- **Lead to verify:** PTC hold/trip currents vs each rail's rated load (1.2 / 0.5 / 0.8 A); TVS
  standoff voltage vs rail (SMAJ15A standoff 15 V is fine for a 12 V rail; SD05 for 5 V).
  **Source:** export + `components/ptc-12v.md`, `ptc-5v.md`, `ptc-12v-neg.md`, `smaj15a.md`,
  `sd05.md`. **Severity:** verify (ratings under fault).

---

## Summary of leads (by severity)

| # | Finding | Severity | Source |
| --- | --- | --- | --- |
| F-1 | VBUS_VS_DISCH (U1.18) ← R14 ← VBUS_IN — v3 fix present, no GND | OK ✅ | export + repo docs + ST DS12499 (web) |
| F-11 | +12 V LDO dropout only 1.5 V (< ~2 V typ) | **MARGINAL ⚠️** | `l7812cv.md` (explicit) + L7812 PDF |
| F-13 | −12 V LDO dropout 1.5 V + check electrolytic polarity | **MARGINAL/VERIFY ⚠️** | `cj7912.md` + CJ7912 PDF |
| F-9 | U4 is an inverting LM2596 (docs say LM2586 SEPIC) — abs-max stress ~28.5 V | VERIFY ⚠️ | export + LM2596 PDF vs CLAUDE.md |
| F-10 | Inductor/diode peak current under load (esp. buck-boost U4) | VERIFY ⚠️ | export + LM2596 PDF |
| F-6 | DISCH (U1.9) → R13 → VBUS_OUT — confirm intended | VERIFY (minor) | `stusb4500.md` + ST DS12499 |
| F-14 | PTC trip / TVS standoff vs rated load & fault | VERIFY | export + protection docs |
| F-2..F-5, F-7, F-8, F-12 | load switch, VDD decap, VREG decaps, CC/ADDR/RESET, FB math, EN pins, +5 V dropout | OK ✅ | export + cited docs |

**Top takeaways:**

1. **The v3 blocker is fixed (F-1).** A datasheet-aware net review of v3 would have caught the
   pin-18→GND bug — that is the standing safety net this skill provides.
2. **Two LDOs run at ~1.5 V dropout (F-11, F-13)** — the thin intermediate-rail margins the
   checklist targets. The repo doc already flags +12 V; raising the +13.5 V / −13.5 V DC-DC
   setpoints toward 14 V (per the doc's own recommendation) is the obvious mitigation. Verify
   the dropout-vs-current curves at the rated 1.2 A / 0.8 A.
3. **Doc-vs-schematic drift (F-9):** the negative rail is a third inverting LM2596, not an
   LM2586 SEPIC. Update the architecture docs and verify the inverting-mode abs-max stress.

---

## What this pass CAN and CANNOT catch

**Datasheet source for STUSB4500 — disclosure:** there is **no local STUSB4500 PDF**. STUSB4500
findings rest on repo docs (`stusb4500-pinout.md`, `components/stusb4500.md`,
`v3-pd-failure-diagnosis.md`) cross-checked against **ST DS12499** obtained via WebSearch (the
direct `st.com/.../stusb4500.pdf` fetch timed out). Treat every STUSB4500 *value* as
"verify against ST DS12499." Regulator/LM2596 findings rest on local PDFs in
`doc/public/datasheets/` + their `components/*.md`.

**CAN catch (static net topology):**

- Wrong-net / missing-connection errors — e.g. the v3 pin-18→GND bug (a pure topology fault).
- Missing components on a net (decap absent, divider half-missing, EN floating).
- Feedback-divider math from the *actual* resistors (recomputed, not trusted).
- Pin-function vs net mismatches (the export carries `pinfunction`, so IN/OUT/GND/FB/EN are
  checked by function, not by symbol position — which is what produced false v3 findings).
- Polarity *by pin assignment* (which net is IN vs OUT vs GND on a negative regulator).
- Nominal dropout headroom (Vin − Vout vs datasheet typ) as a flag.

**CANNOT catch (out of scope for this pass — require bench / sim / PCB review):**

- Actual voltages/currents **under load** — dropout-vs-current, regulation droop, ripple,
  inductor peak/saturation, PTC trip behavior. (F-10, F-11, F-13, F-14 are flags, not proof.)
- **Thermals** — junction temperature, copper-area heatsinking, derating.
- **Loop stability / transient response** — compensation, ESR-dependent stability of the LDOs
  and DC-DC loops.
- **Layout / parasitics** — `*.kicad_pcb` is not reviewed here (read-only, untouched); trace
  width, current loops, ground bounce, decap placement.
- **Footprint ↔ symbol pin-number mismatch** — the netlist uses symbol pins; a wrong footprint
  pinout (the kind of error that bit a prior order) is invisible to a schematic-netlist pass.
- **Electrolytic polarity in the physical part** — flagged by net (F-13) but the actual symbol
  +/- orientation and the footprint polarity mark must be eyeballed in KiCad.
- **NVM / firmware** — the STUSB4500 PDO programming (15 V/3 A) is data, not schematic.

---

*Generated by the `pd-schematic-review` skill. Re-run after any schematic change. Raw exports:
`__inbox/zudo-pd-netlist.xml` / `.net` (gitignored).*
