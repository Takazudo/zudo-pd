# Product comparison: current model vs a 60 W-input-class model (screen)

**Status: exploration only. Nothing here is adopted.** No model, name, rating, contract relaxation, part or circuit is selected. Every schematic and PCB stays an unvalidated draft, and **nothing on this page is measured**. No hardware change, fabrication, NVM programming or energizing is implied. "zudo-PD-60W" is a tentative working name only.

Owner direction (zudo-pd#218, 2026-10-20): evaluate the **current model** as its own lightweight-use product, separately from a redesigned higher-power model. Do not make a common-PCB two-SKU lineup the default recommendation for manufacturing convenience alone. Do not assume the current model is already safe or cheaper. The current-model cost baseline belongs to this comparison.

Sources reused unchanged: [`supply-capability.md`](supply-capability.md) (and `scripts/pcb/calculate-supply-capability.py --load`), [`supply-alternatives.md`](supply-alternatives.md), [`input-clamp-fix.md`](input-clamp-fix.md), [`design-gaps-20v.md`](design-gaps-20v.md), [`power-limit-60w.md`](power-limit-60w.md) and [`product-lineup.md`](product-lineup.md). Evidence classes: **G** guaranteed, **G-U** guaranteed but mirror-only or unsourced, **TYP** typical, **PA** project assumption, **CP** catalog price (non-binding), **UNAV** unavailable. "calc" means calculated and unverified.

## Part 1. Current model as a lightweight-use product

Current model: 15 V / 3 A PD contract on Board P (STUSB4500, SMAJ16A D5, AO3401A Q1); Board B AP63201 + two LM2596 pre-regulators, LT1963A (+12 V, +5 V) and LT3015 (−12 V) linear regulators, PTC1–PTC3.

### 1.1 What the screen says today (calc, unverified)

| Load point (+12 / −12 / +5 A) | Screen status | Blocking rows | Required weighted converter efficiency (14 V / 15 V input) |
|---|---|---|---|
| PD targets 1.2 / 0.8 / 0.5 | **FAIL** | PTC3 hold 0.77 A at 85 °C < 0.8 A (G); PTC1 ≈ 0.74 A at 85 °C (estimate) | 85.1 % / 79.4 %; efficiency data UNAV, so NOT RUN |
| 1.0 / 0.7 / 0.4 | ESTIMATE_FAIL | PTC1 85 °C estimate | 73.4 % / 68.5 % |
| **0.7 / 0.7 / 0.4 (candidate)** | PASS_SCREEN, efficiency open | None failing; +5 V PTC2 hold at 85 °C NOT RUN; AP63201 low-line headroom typical only | 63.6 % / 59.4 % |

The PD-target row is in `supply-capability.md`. The other two rows are not in any committed report; they come from `python3 scripts/pcb/calculate-supply-capability.py --load cand=1.0,0.7,0.4` and `--load cand=0.7,0.7,0.4` run at this commit (the `--load` option evaluates a point without changing the committed JSON).

The current model is **not** shown to support the published PD targets. A conservative candidate rating is below; it is a screen result, not a rating.

**Candidate lightweight rating (calc, unverified, not adopted): +12 V 0.7 A, −12 V 0.7 A, +5 V 0.4 A** (about 18.8 W at 12 / 12 / 5 V), on a 15 V / 3 A charger with a 3 A cable. Known: the PTC hold at 85 °C passes on the G value (−12 V, PTC3) or the family estimate (+12 V, PTC1); the U2 peak current limit passes on a guaranteed minimum. The U3 and U4 switch-limit checks also pass, but the script classes them PROJECT_ASSUMPTION (they rest on an assumed inductance), so they are not guaranteed. Unknown: converter efficiency (needs ≥ 63.6 % at a 14 V board input), LDO thermal (dissipation 3.16 / 3.23 / 1.73 W needs effective θJA ≤ 26.9 / 26.3 / 49.0 °C/W at 40 °C ambient; NOT RUN), +5 V PTC2 derating, ripple, startup and surge. Raising the rating toward 1.2 / 0.8 / 0.5 A needs fixes F1 and F2 below plus efficiency and thermal evidence.

### 1.2 Fixes needed for the current model to be viable

| ID | Gap | Applies at the candidate rating? | Fix direction (candidate, not chosen) | Evidence state |
|---|---|---|---|---|
| F1 | PTC3 (−12 V) hold 0.77 A at 85 °C | Only above 0.77 A | Higher-hold PTC or lower ambient rating | G (fail at 0.8 A) |
| F2 | PTC1 (+12 V, SMD1210P150TF/16) hold ≈ 0.74 A at 85 °C | Above ≈ 0.74 A | Higher-hold PTC or lower ambient rating | Estimate |
| F2b | PTC2 (+5 V, mSMD110-33V) derating above 25 °C UNAV; 1.1 A hold at 25 °C | Unknown at 0.4 A | Retrieve derating | UNAV |
| F3 | U4 (−12 V inverting LM2596) switch limit caps −12 V at 1.217 A (G 3.4 A switch minimum with an assumed 80 µH, so the check is PA) | No | None needed for a light rating | PA |
| F4 | LM2596 inverting startup ≈ 4.5 A for ≥ 2 ms against the 3 A contract | **Yes, at any load** | Soft start or enable sequencing on U4 | Integration rule `inverting-startup-vs-pd-source`; NOT RUN |
| F5 | LDO thermal (4.2 / 3.5 / 2.0 W at PD targets; 3.2 / 3.2 / 1.7 W at the candidate) | **Yes** | Copper and θJA screen, then thermal test | NOT RUN |
| F6 | Converter efficiencies U2–U4 | **Yes** | Retrieve curves or measure | UNAV |
| F7 | AP63201 low-line headroom 0.080 V on typical RDS(on) only; AP63201 out of stock at LCSC on 2026-10-20 | **Yes** | Guaranteed-limit screen; sourcing alternative | TYP; CP stock observation |
| F8 | Input clamp vs STUSB4500 28 V: SMAJ16A +2.00 V at 25 °C (G), hot unproven | **Yes** | PD-CLAMP-1 (b) per-pin R + BZX84-C20, or (a) TVS1800; gaps and plan V1-15–V6-15 in [`input-clamp-fix.md`](input-clamp-fix.md) | G at 25 °C; hot TYP estimate |
| F9 | VREG_2V7 loaded by R15/R16 pull-ups; DS12499 says "used only for external decoupling" | **Yes** | Move pull-ups to another supply, or confirm by test (V2) | G-U |
| F10 | CC pins vs 22 V: +6.25 V margin at 15 V (PA VBUS max) | Yes (low risk) | Short test V6-15 | PA |
| F11 | Coordinated all-rail on/off, insufficient-source indication, reverse blocking (GAP-6, -7, -9) | Product decision | Same requirement set as any option; overload ends in source OCP or hard reset, not a coordinated off | Requirements only |
| F12 | Source voltage bands, ripple and noise for synth loads | Load-dependent | LDO chain helps ripple; bands and Zout unscreened for a general load | NOT RUN |

Ratings that need validation (tests proposed elsewhere, **not executed**, each needing hardware-test approval): efficiency and thermal at the rating, startup inrush with U4 (F4), PTC behavior at ambient, surge and clamp (V1-15–V6-15), and all-rail behavior on detach.

### 1.3 Current-model cost baseline

Known (CP, LCSC, qty 1, retrieved 2026-10-20; from `supply-alternatives.md` and `product-lineup.md`):
- Board B regulators: LT3015 $16.57, LT1963A $4.6427 ×2, LM2596S $0.6299 ×2, AP63201 $0.7228, **total $27.84**.
- STUSB4500QTR $2.8412.
- Retrieved IC subset for the current design (PD sink, Board P TVS/MOSFET, Board B regulators): **$30.86**. For comparison, the 20 V switcher-direct subset is $7.18.

Unpriced (UNAV): PTCs, inductors, capacitors and other passives; connectors and terminals; PCB fabrication; assembly (setup, extended-part fees, through-hole); stencils; test fixtures and time; NVM programming; F1–F12 fix parts; chargers and cables; enclosure and labels.

**The current model is not shown to be cheaper.** Its retrieved regulator ICs cost about $24.5 more than a switcher-direct chain at qty 1. Whether that survives passives, heat sinking and assembly is UNAV. Because most items are unpriced, the current model has no priced baseline. Part 2 therefore places both models on the existing **C2 = 1.0** scale used in `product-lineup.md` and `power-limit-60w.md`, and marks every ratio as an unverified project guess.

## Part 2. zudo-PD-60W (tentative name; not adopted)

"60 W" is the **input class**: a 20 V / 3 A PD contract (60 W source PDP). It is **not** 60 W of rail output. At that contract the board input is about 55 W and the rail output about 42–48 W, or 41.6–46.6 W with a safe trip (`power-limit-60w.md`, calc).

### 2.1 Changes vs the current model

| Area | Change (candidate) | Source |
|---|---|---|
| Board P | 20 V set: TVS2200 + AOD4185L replace SMAJ16A + AO3401A; 20 V NVM image and refuse policy; clamp decision **PD-CLAMP-2** (TVS2200 + per-pin R + BZX84-C24, 0.2–1.4 V hot margin, PA) — separate from PD-CLAMP-1 | `supply-alternatives.md`, `input-clamp-fix.md` |
| Board P | CC 22 V at 20 V: +1.00 V (PA); no fix found except a TCPP-class part with an unsolved supply | `input-clamp-fix.md` |
| Board B | Switcher-direct chain (3× TPS54560 class), LC post-filters, higher-rated PTCs | `b1-gates.md` |
| Board B | Terminal sense and precision servo for the source bands (GAP-3/4); post-LDO candidate for load-step Zout | `design-gaps-20v.md` |
| Protection | Input current trip with latching all-rail off, common start hold-off, 4-state indicator, re-plug reset (M-a, M-c, M-d, M-e) | `power-limit-60w.md` |
| Rating | Candidate range R60: +12 V ≤ 1.60 A, −12 V ≤ 1.50 A, +5 V ≤ 0.28 A (≈ 38.6 W), LTC4282-class trip + 5 % guard (calc) | `power-limit-60w.md` |

### 2.2 Coarse cost on the C2 = 1.0 scale (unverified project guesses; two separate ratios)

C2 is the fixed full-OSC 20 V ≥ 3.5 A design used as the reference in `product-lineup.md` and `power-limit-60w.md`. Neither ratio below is calculated; each is a judgment from the count of cost drivers, and the drivers set the range.

| Model | Per-unit manufacturing cost (1 unit) | One-off design and test effort | Drivers that set the range | Unpriced |
|---|---|---|---|---|
| C2 (reference) | 1.0× | 1.0× | Switcher-direct Board B, servo, shutdown, reverse blocking, 20 V Board P set | Passives, PCB, assembly, test, protection network |
| **zudo-PD-60W** (= C1-L in `power-limit-60w.md`) | about 1.05–1.15× | about 1.3–1.6× | C2 plus the input trip chain and calibration, latch, common start, 4-state indicator; charger-OCP matrix; startup control work with OSC | Trip chain, indicator, CC protection, as for C2 |
| **Current model with F4–F9** | about 1.0–1.3× (guess) | about 0.5–1.0× (guess) | Per unit: its retrieved IC subset is $23.68 above C2's ($30.86 vs $7.18, CP), against C2's unpriced servo, shutdown and protection; LDO heat sinking UNAV. Effort: no Board B redesign, but F4, F8 and F9 still change the schematic and PCB, and F5/F6 need thermal and efficiency evidence | Fix parts, heat sinking, passives, PCB, assembly |

On this scale zudo-PD-60W and the current model are within the guessed ranges of each other per unit; the current model is not shown to be cheaper. zudo-PD-60W carries more one-off effort.

### 2.3 OSC compatibility

Full OSC compatibility is **unverified** for zudo-PD-60W:
- Full OSC as recorded needs a 20 V contract of at least about 3.38 A (≥ 70 W charger, 5 A e-marked cable; `product-lineup.md`). A 60 W input class does not meet it.
- Under R60, OSC fits only if OSC changes its reserve and rounding rule (PWR-D5): the +5 V cap of 0.28 A is below OSC's 0.3 A ×1.1-rule candidate, and ±12 V leaves only about 4 % above the heavy realistic patch.
- OSC's fitted-capacitance startup row is EDGE against R60: +12 V is about 10 mA over at the 10 ms soft start. It fits only with a supply-side slow ramp of at least about 11.5 ms, accepted by OSC, and only after the OSC slow-ramp campaign (OSC #288 PWR-INT-08) passes.
- The 20 ms transient requirement is not removed by any of these.

## Part 3. Common-platform tradeoffs (secondary; not the default)

A common PCB serving both models (`product-lineup.md` B-common, `power-limit-60w.md` B-common-L) remains possible but is **not the default recommendation**. The owner questions deliberately limiting an expensive high-power board to create a low SKU. On this screen:
- A common 20 V board used as a light SKU carries the 60 W model's servo, trip and indicator cost in every unit.
- Its benefit is one layout and one parts set. At IC level (CP, qty 1) the retrieved difference between lineup options is $0.84–1.24 per set, and the Board P 20 V parts delta that a population variant would save is $0.44–0.85 per set over qty 1–100 (`product-lineup.md`).
- Misprogramming a high image onto low trip hardware, or the reverse, is a new failure mode.

## PD controller choice (consolidated from as-built-and-controller.md)

The current RESET / I2C failures are on the **zudo-led-lamp** Board P, not on any zudo-PD board, and they trace to board-level conditions (RESET outside its guaranteed low, VREG_2V7 used for I2C pull-ups, wrong silkscreen labels) rather than to an STUSB4500 incompatibility. The renewal zudo-PD Board P shares that circuit except its TVS. Which zudo-PD revision is on the bench is undetermined until the JLCPCB order record is retrieved. Intrinsic STUSB4500 costs remain per-unit NVM programming, stateful POWER_OK and the 28 V clamp margin. Among simpler fixed-profile sinks, the resistor-strapped Infineon CYPD3177 (VBUS 30 V, CC still 22 V, FAULT pin, pre-programmed with no per-unit programming) is the leading candidate for zudo-PD-60W evaluation; nothing is adopted. For manufacturing repeatability (per-unit programming, pass/fail test, rework; the owner's 20-of-60 example is hypothetical, not a rate), a pre-programmed, resistor-strapped controller removes the per-unit NVM step at a small BOM increase (PA); its strap-tolerance risk is not yet calculated, and all setup times are PA estimates, not measurements. Details, evidence classes and the as-built identity gaps are in [`as-built-and-controller.md`](as-built-and-controller.md).

## Owner choices (minimal; recommendation marked; nothing adopted)

1. **PC-1, current model as a lightweight product (no recommendation):** pursue it at a candidate rating near 0.7 / 0.7 / 0.4 A, raise its rating with F1/F2 plus efficiency and thermal evidence, or retire it. Pursuing it is not a small change: F4 (U4 startup), F8 (input clamp) and F9 (VREG_2V7 pull-ups) change the schematic and PCB; F7 is a sourcing problem (AP63201 out of stock at LCSC on 2026-10-20); F5 and F6 are evidence gaps that need thermal and efficiency data. Its per-unit cost is not shown to be lower than a redesigned board.
2. **PC-2, zudo-PD-60W:** continue as a candidate new model (**recommended to keep as a candidate**, with full OSC still requiring ≥ 70 W or the PWR-D5 path), or drop it.
3. **PC-3, common platform:** keep as a secondary option only (**recommended**), or reconsider later when both models are defined.

These choices do not authorize parts, schematic, PCB, NVM, fabrication or hardware tests.
