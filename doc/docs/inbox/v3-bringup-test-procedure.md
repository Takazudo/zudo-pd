---
sidebar_position: 8
---

# v3 Bring-Up & Test Procedure

Staged bench procedure for a freshly assembled **PCBA v3** board. Every stage gates the
next: if a stage fails its pass criteria, **stop and debug before powering further** — the
downstream rails have never run on real hardware (v1 and v2 both died at the USB-PD front
end), so v3 is the first board where the DC-DC + LDO chain is exercised at all.

:::danger The two independent gambles
1. **Does the v3 CC-termination fix work?** (external Rd + CC1DB/CC2DB isolation — the v2 killer)
2. **Does the never-before-tested power chain behave?** (DC-DC + LDO + protection)

These are separable, and you should test them separately. The cleanest way to de-risk
gamble #2 without depending on #1 is to **inject 15 V from a bench supply at TP1 (VBUS_OUT)**,
bypassing USB-PD entirely — see Stage 4.
:::

:::warning Before anything: the 20 V hazard
A **fresh, un-programmed** STUSB4500 advertises **20 V at highest priority**. On a
20 V-capable PD charger it will negotiate 20 V within ~tens of ms of plug-in and push 20 V
into a 15 V-rated DC-DC stage. **Never plug an un-programmed board into a full PD charger.**
Use a current-limited bench supply, a 5 V-only charger, or a no-20V (max 9/15 V) source until
the NVM is written. (USB-C always starts at 5 V vSafe5V, so the instant of plug-in is safe;
the danger is the negotiation a few ms later.)
:::

## Tools & materials

| Item | Purpose |
| --- | --- |
| Bench DMM | Continuity (ohms) + DC voltage. The workhorse. |
| Bench PSU with **adjustable current limit** | First power-up + injecting 15 V at TP1. Set the limit low to catch shorts. |
| USB-C **5 V-only or no-20V** charger | Safe source for NVM programming session. |
| Real USB-C **PD charger that supports 15 V** | Final PD-negotiation test (only after NVM programmed). |
| NUCLEO-F072RB + 4P pogo clip + STSW-STUSB002 GUI | STUSB4500 NVM programming (see [NVM Programming Setup](nvm-programming.md)). |
| Oscilloscope (optional) | Ripple measurement (Stage 7). |
| Dummy loads: power resistors or electronic load | Load test (Stage 6). |

**Rated-load reference** (note: docs disagree — `CLAUDE.md` says 1.2/0.8/0.5 A, `quick-reference`
says 1.5/1.0/1.5 A). Test at the **lower** figure first, then push up:

| Rail | Conservative | Stretch |
| --- | --- | --- |
| +12 V | 1.2 A | 1.5 A |
| −12 V | 0.8 A | 1.0 A |
| +5 V | 0.5 A | 1.5 A |

---

## Stage 0 — Visual + unpowered inspection (no power)

1. **Solder bridges**: inspect U1 (QFN-24) corners especially — CC1DB is at one corner,
   RESET at the opposite. Inspect the TO-263 regulator/converter tabs.
2. **Polarity**: confirm electrolytic cap orientation (470 µF bulk caps) and diode bands.
3. **Fuses present**: confirm the SMD fuses and PTCs are populated.
4. **EPAD ground**: the STUSB4500 exposed pad (pin 25) must be soldered to GND, or the chip
   misbehaves. (Hard to inspect visually on a QFN; the continuity checks below catch a dead chip.)
5. **No rail-to-GND dead short**: ohmmeter from +12 V, +5 V, −12 V output points to GND.
   Expect hundreds of ohms to kΩ (bulk caps), **not** 0 Ω. A hard 0 Ω = stop, find the short.

**Pass**: no bridges, correct polarity, no rail-to-GND short. → Stage 1 (or Stage 0.5).

---

## Stage 0.5 — Verify the v1/v2 fixes (unpowered ohm checks) ⭐

These confirm the historical bugs are actually fixed on *this* board. **All verified present
in the v3 netlist** — these checks confirm the physical assembly matches. Probe at the J3
pogo block (chip-side signals) and the USB-C / D4 area.

| # | Check | Expected | If wrong |
| --- | --- | --- | --- |
| 1 | U1 pin 18 → R14 → GND | **~470 Ω** to GND (not open) | v1 "pin 18 NC" bug — pin 18 unconnected |
| 2 | U1 pin 22 (VSYS) → GND | **&lt;1 Ω** (hard tie) | VSYS floating (v1 bug) |
| 3 | U1 pin 22 ↔ pin 23 | **OPEN** (no continuity) | v1 VSYS–VREG_2V7 short returned |
| 4 | **CC1 → GND** and **CC2 → GND** | **~5.1 kΩ each, SYMMETRIC** | The v2 fault signature was CC1 = 0 Ω vs CC2 = 5.1 kΩ. **Asymmetry = the chip-short failure.** |
| 5 | J3 pad 1 (CC1DB) ↔ CC1 net | **OPEN** (isolated) | CC1DB not isolated — v2 vulnerability persists |
| 6 | J3 pad 1 (CC1DB) → GND (via R19) | **~0 Ω** | 0 Ω jumper R19 missing/open |
| 7 | D4 across each CC line (pin1↔6, pin3↔4) | **~0 Ω** (diode passes) | Dead ESD diode |

:::note R14 destination discrepancy (flag for your eyeball)
The netlist shows R14 ties pin 18 → 470 Ω → **GND**, while the older debug docs say "→ VBUS_IN."
Tying the VBUS-discharge sense pin to GND through a resistor is a datasheet-sane discharge
config, so this is probably fine — but cross-check against the STUSB4500 reference design if
PD behaves oddly. The fix being verified here (pin 18 is *not* NC) holds either way.
:::

**Pass**: checks 1–7 as expected, CC lines symmetric. → Stage 1.

---

## Stage 1 — Program STUSB4500 NVM (prerequisite)

The board will not negotiate 15 V until the NVM is reprogrammed. Full procedure:
[NVM Programming Setup](nvm-programming.md). The essentials:

- **Power the board from a 5 V-only / no-20V USB-C charger** during programming (the chip's
  VDD only needs 5 V for I2C; the Nucleo supplies only SCL/SDA/GND).
- Connect pogo clip to **J2**: pad 1 = SCL, pad 2 = SDA, pad 3 = GND, pad 4 = NC. I2C addr **0x28**.
- Write: **`SNK_PDO_NUMB = 2`** (drops the 20 V PDO entirely), **PDO2 = 15 V / 3 A**,
  **`POWER_ONLY_ABOVE_5V` = enabled**.
- **Read back to verify** — `POWER_ONLY_ABOVE_5V` sometimes fails the first write.
- GUI Dashboard must show **"Sink attached"**, not "No device attached." (The latter = a
  CC-termination hardware fault — go back to Stage 0.5 check #4.)

:::caution NVM is rated ~1000 write cycles
Program once. Don't loop writes.
:::

**Pass**: NVM read-back confirms the 3 settings, Dashboard shows "Sink attached." → Stage 2.

---

## Stage 2 — First safe power-up (current-limited)

Two valid sources; use whichever you have. **Watch the current draw** — a spike that doesn't
settle = a short; kill power immediately.

- **Option A — bench supply into VBUS_IN**: set **5.0 V**, limit **~100–150 mA**. Good for a
  gentle smoke test of the chip front-end.
- **Option B — 5 V-only / no-20V USB-C charger**.

**Measure:**

| Point | Expected | Meaning |
| --- | --- | --- |
| VREG_2V7 (J3 pad 3) | **2.6–2.8 V** | Chip is alive and configured ("is the chip awake?") |
| Idle current | settles to a low steady value | No short |

:::warning Bench supply at VBUS_IN does **not** power the downstream rails
VBUS_OUT is gated by Q1 (AO3401A load switch), and Q1 only turns on when the chip asserts
**VBUS_EN_SNK** after a valid PD contract. Injecting at VBUS_IN with no CC handshake leaves
Q1 **off**, so the DC-DC chain stays dark. That's expected. To test the power chain
independently, inject at **VBUS_OUT / TP1** instead — see Stage 4.
:::

**Pass**: VREG_2V7 ≈ 2.7 V, current settles. → Stage 3.

---

## Stage 3 — USB-PD negotiation + v3 fix validation (the v2 killer)

Now the moment v2 failed at. **First, the acceptance test that proves the v3 Rd fix:**

1. With **un-programmed-acceptable** logic aside (NVM is already done), plug a USB-C source and
   confirm **VBUS appears (~5 V) at the connector and at TP1**.
  - **v2's headline failure was 0 V here.** Any voltage appearing proves the external-Rd
     bootstrap works even with a defective chip. ✅ This single test is the v3 vindication.
2. Now connect the **real 15 V PD charger** (safe — the 20 V PDO is no longer advertised):

| Point | Expected | Notes |
| --- | --- | --- |
| TP1 / VBUS_OUT | **14.7–15.3 V** (≈15.0, **not 20**) | PD negotiated |
| ATTACH (J3 pad 6) | asserted | CC handshake completed |
| PD_OK (J3 pad 7) | asserted (toggles high) | 15 V contract succeeded |
| VBUS_EN_SNK (J3 pad 8) | asserted → Q1 on | Load switch enabled |

**Diagnostic**: if VBUS_IN = 15 V but VBUS_OUT/TP1 = 0 V → VBUS_EN_SNK / Q1 gate path issue.

:::tip If PD still fails on v3
Lift **R19** (or R20) to isolate the chip's CC1DB/CC2DB pin from GND — this is exactly why
0 Ω jumpers (not hard ties) were used. Last resort: hot-air U1 and meter the empty pad
(OPEN = the short is inside the chip, as in v2).
:::

**Pass**: TP1 = 15.0 V (not 20), PD_OK asserted. → Stage 4.

---

## Stage 4 — DC-DC intermediate rails

:::tip Decouple from USB-PD — inject 15 V at TP1 (with one pre-check)
To test the power chain **without depending on PD**, you can feed a bench supply into
**TP1 (+) / TP2 (GND)** at **15.0 V, limit ~200–300 mA**. TP1's net is the **`VBUS_OUT`**
global label (downstream of the Q1 load switch), so this bypasses the USB-PD front end and
drives the DC-DC + LDO chain directly. `VBUS_OUT` enters the DC-DC sheet as the
`USB-PD-power IN` hierarchical pin and fans out to U2/U3/U4 VIN (local labels
`+15V -> +13.5V gen`, `+15V -> +7.5V gen`, `+15V -> -13.5V gen`).

**⚠️ Mandatory pre-check before injecting (unpowered, ohmmeter):** measure between **TP1** and
**U1's VDD pin (J3 pad 4)**.
- **Open / high resistance** → TP1 is isolated from the chip supply. **Safe to inject 15 V.**
- **Continuous (~0 Ω)** → `VBUS_OUT` back-feeds the STUSB4500 supply. **Do NOT inject 15 V at
  TP1** — you'd put 15 V onto the chip. (The docs conflict: `test-points-v3.md` calls VDD
  "post-MOSFET load switch," which would mean exactly this back-feed; the netlist trace
  suggested VDD = VBUS_IN. Resolve it with this meter check before trusting TP1 injection.)
  In that case, drive the chain through the normal PD path (Stage 3) instead.

Note: there is **no input fuse** on the VBUS path (the SMD fuses are all on the output rails).
If you inject and a converter stays dark, confirm 15 V actually reaches *that* converter's VIN
before suspecting the converter itself.
:::

Probe each intermediate at its test point:

| TP | Rail | Source | Expected | Pass band |
| --- | --- | --- | --- | --- |
| **TP3** | +13.5 V | U2 LM2596 (R1=10k/R2=1k → 13.53 V) | +13.5 V | 13.2–13.8 V |
| **TP4** | +7.5 V | U3 LM2596 (R3=5.1k/R4=1k → 7.50 V) | +7.5 V | 7.3–7.7 V |
| **TP5** | −13.5 V | U4 LM2596 **inverting buck-boost** (+15 V → −13.5 V *directly*) | −13.5 V | −13.2 to −13.8 V |

:::danger TP5 MUST read negative — the #1 module-killer risk
The **negative rail is the single most dangerous thing on this board to get wrong.** Older
docs disagree on its topology (there is **no separate −15 V rail** on this build — the old
LM2586 SEPIC two-step was replaced by U4's direct inversion; ignore "−15 V → −13.5 V"
wording), and the U4 feedback-divider orientation could **not** be resolved from the file.
Before you trust the −12 V chain or connect *any* module:

1. Meter TP5 and **confirm the reading is NEGATIVE**, ≈ −13.5 V (band −13.2 to −13.8 V).
2. If TP5 reads **positive, near 0 V, or +15 V** → the inversion is not working. **Stop.**
   Do not proceed to the −12 V LDO or the output connectors. A positive voltage on what
   should be the −12 V rail destroys modules instantly.
:::

**Pass**: all three TPs in band, TP5 negative. → Stage 5.

---

## Stage 5 — LDO final rails + output connectors

Measure each regulator output, then verify it survives the protection devices to the connector.

| Rail | Regulator | In → Out | Expected | Pass band |
| --- | --- | --- | --- | --- |
| +12 V | U6 L7812CD2T-TR | +13.5 → +12 | +12.0 V | 11.75–12.25 V |
| +5 V | U7 L7805ABD2T-TR | +7.5 → +5 | +5.0 V | 4.9–5.1 V |
| −12 V | U8 CJ7912 | −13.5 → −12 | −12.0 V | −11.75 to −12.25 V |

:::note Headroom flag (watch under load in Stage 6)
+12 V and −12 V each have only **1.5 V dropout headroom** — marginal for a 78xx/79xx, which
can want ~2 V at full load and high temperature. At light load they'll read fine; the risk
shows up under load (Stage 6). +5 V has a comfortable 2.5 V headroom.
:::

**Protection-device note**: PTC/TVS numbering does **not** follow rail order — **PTC1 = +12 V,
PTC2 = +5 V, PTC3 = −12 V**. The indicator LED only proves the *regulator output*, not the
*post-PTC delivered rail* — always meter the post-PTC node. (PTCs as placed are
BSMD1206-150-16V, ≈1.5 A hold.)

### Output connectors — polarity is destruction-critical

:::danger Do NOT trust pin numbers — identify −12 V by meter, every time
A reversed ribbon swaps +12 V/−12 V and **instantly destroys** modules. The exact pin→net
mapping on J10/J11 could not be resolved to a number I'd stake a module on (it depends on the
header's physical orientation, which the board may mount face-down), so **treat pin numbers as
unverified** and use the procedure below instead. The board's **silkscreen is the authority** —
it was a hard design requirement — and the meter is the final check.
:::

**−12 V identification procedure (do this on this first board):**

1. Put the black meter lead on a known **GND** (any FASTON GND tab / TP2). Red lead on each
   header pin in turn while the board is powered at low load.
2. The pin that reads **negative (≈ −12 V)** is the −12 V rail. **Mark it.**
3. Confirm that marked pin matches the **silkscreen** label and the Eurorack **red-stripe edge**
   of the connector. If silkscreen and meter disagree, **trust the meter** and stop to
   investigate before connecting anything.

**Reference — standard Eurorack 16-pin convention** (verify against *your* board, don't assume):
the red-stripe edge carries **−12 V**, the opposite edge **+12 V**, with **+5 V** and **GND**
rows between. This board's headers also carry the Eurorack **CV and Gate bus rows** — present
in the schematic as `CV rail` and `GATE rail`, alongside `-12V rail`, `+12V rail`, `+5V rail`,
`GND rail`. Match those net names to the silkscreen.

- **J10 / J11** = 2541WR-2X08P, 16-pin Eurorack box headers (two, for daisy-chaining the rails).
- **J6–J9** = FASTON tabs, per netlist: **J6 = −12 V, J7 = +12 V, J8 = +5 V, J9 = GND**
  (verify against silkscreen). These are live rail taps — handy as the **known-good reference
  points** for the meter procedure above, and as the GND lead anchor.

**Pass**: all three rails in band at the connector, polarity confirmed by meter. → Stage 6.

---

## Stage 6 — Load test

Apply load **one rail at a time**, starting at the conservative current, ramping to stretch.

1. Apply rated load (resistor or e-load) to +12 V. **Go/no-go: if +12 V drops below 11.75 V at
   rated load, the LDO is dropping out** (the 1.5 V headroom flag) — note the current at which
   it sags. A rail that holds at 1.2 A but sags at 1.5 A tells you the safe load ceiling.
2. Repeat for −12 V (**no-go below −11.75 V magnitude** = dropout) and +5 V (comfortable
   headroom, should hold easily to its rated current).
3. **Thermals**: after a few minutes at load, the LM2596 tabs and the 78xx/79xx should be
   warm, not untouchable. Expected rise is modest (~+15 °C on the converters). If anything is
   too hot to touch briefly, stop.
4. Optionally load all rails simultaneously to confirm the shared 15 V input holds up.

**Pass**: rails hold regulation at rated load, thermals reasonable. → Stage 7/8.

---

## Stage 7 — Ripple / noise (optional, scope)

Target: **&lt;1 mVp-p** on the LDO outputs. Measure with a scope, **20 MHz bandwidth limit on**,
short ground spring (not the long clip lead), AC coupling, on the output rail at the connector
under load. The DC-DC intermediates (TP3/4/5) will show ~tens of mVp-p switching ripple — that's
expected; the LDO is what cleans it up.

**Pass**: LDO outputs near or below 1 mVp-p.

---

## Stage 8 — Protection test (do last, deliberately)

:::caution Do this knowingly — it stresses the board
:::

- **Overcurrent → PTC**: gradually increase load past the rail's PTC hold current (≈1.5 A).
  The PTC should trip → rail drops → indicator LED off. Remove load; PTC **auto-resets in
  ~30 s** as it cools. (A tripped PTC mimics a dead rail — don't mistake it for a fault.)
- **Short → fuse**: the SMD fuses are the final defense for a hard short and are **one-shot**
  (blown = replace). Only test deliberately if you have spares and a reason to.

---

## Troubleshooting quick table

| Symptom | Likely cause | Check |
| --- | --- | --- |
| 0 V at USB-C VBUS on plug-in | CC termination fault (the v2 failure) | Stage 0.5 #4: CC1/CC2 symmetric ~5.1 kΩ? Lift R19/R20 to isolate chip |
| VBUS = 20 V (!) | NVM not programmed / wrong charger | Reprogram `SNK_PDO_NUMB=2`; unplug from 20 V source |
| Dashboard "No device attached" | Hardware CC fault, not NVM | Stage 0.5 #4–7 |
| VBUS_IN = 15 V but TP1 = 0 V | VBUS_EN_SNK / Q1 load-switch path | J3 pad 8 asserted? Q1 gate |
| VREG_2V7 ≠ 2.7 V | Chip not awake / EPAD not grounded / no VDD | Stage 0 EPAD; Stage 2 |
| A DC-DC TP wrong/0 V | That converter's FB divider or the IC | Recheck TP3/4/5; TP5 must be negative |
| +12 V or −12 V sags under load | LDO dropout (1.5 V headroom) | Stage 5 headroom flag; consider raising the intermediate rail |
| A rail dead but LED was on | PTC tripped (post-PTC node) | Meter post-PTC; wait 30 s for auto-reset |
| Rail present at regulator, absent at connector | PTC/fuse open | Meter across PTC/fuse |

---

## Appendix — verified facts & open flags

**Verified present in the v3 netlist (7/7 historical fixes):** R14 on pin 18; VSYS→GND;
no pin22–23 short; VREG_2V7 decoupled by C30 (1 µF); VREG_1V2 by C34 (1 µF); external Rd
R17/R18 = 5.1 k (C23186) on CC1/CC2; CC1DB/CC2DB isolated and GND-tied via 0 Ω jumpers
R19/R20 (C21189). Chip-side signals broken out on **J3** 1×8 pogo block
(1:CC1DB 2:CC2DB 3:VREG_2V7 4:VDD 5:RESET 6:ATTACH 7:PD_OK 8:VBUS_EN_SNK).

**Open flags to keep in mind:**
- R14 far end is **GND**, not VBUS_IN as older docs state (probably fine; cross-check ref design).
- +12 V / −12 V LDO headroom is **1.5 V** — marginal; watch under load.
- U4 negative-feedback exact value/sign unresolved from the file — **confirm at TP5 on the bench.**
- TP6–TP9 (CC1/CC2/−15V/VBUS_DISCH individual pads) were **planned but not placed** — only
  TP1–TP5 + J2 + J3 exist on this build.
- Rated-current spec disagrees across docs (1.2/0.8/0.5 A vs 1.5/1.0/1.5 A) — reconcile vs BOM.
