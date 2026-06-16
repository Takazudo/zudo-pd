# SPICE value-sizing loop — LM2596-ADJ feedback divider

**Approach D** of the AI-circuit-design experiment (epic #68, sub-issue #77).
Goal: demonstrate a **repeatable SPICE-in-the-loop value-sizing workflow** on a
real part of the `zudo-pd` design and produce a worked result.

## Scope (read this first)

This is a **value-sizing demo**: a DC operating-point / resistor-divider
calculation that verifies the **feedback divider selects the intended rail
voltage**.

It is **NOT** a full buck-converter simulation. There is **no** modelling of:

- switching transient / start-up behaviour,
- control-loop stability (phase/gain margin, compensation),
- output ripple or noise,
- inductor / catch-diode / Cout dynamics.

Those belong to a separate transient/AC study (see "How this extends" below).
The value-sizing question — _"do R3/R4 set the rail I want?"_ — is exactly the
kind of parameter tuning the research flagged as the 14% -> 90% lever, and it is
what this deck answers.

## The part under study

From the real schematic (`dc-dc-conversion.kicad_sch`, read-only):

- **U = LM2596S-ADJ** adjustable buck regulator.
- Feedback divider: **R3 = 5.1 kOhm** (top, Vout->FB), **R4 = 1.0 kOhm**
  (bottom, FB->GND).
- The LM2596-ADJ servos its output until **FB = Vref ~= 1.23 V** (datasheet typ).
- Governing equation: **Vout = Vref * (1 + R3/R4)**.

With the as-designed values this is the **+7.5 V intermediate rail** that feeds
the LM7805 -> +5 V output (4-stage architecture in the project README).

## The loop (generate -> simulate -> read-back -> adjust -> re-check)

This is the repeatable procedure. It is deliberately mechanical so an agent (or
a human) can run it without re-deriving algebra each time.

1. **Target.** State the rail you want, e.g. `Vout_target = 7.5 V`.
2. **Generate (compute the divider).** Hold one resistor (here R4 = 1 kOhm, a
   convenient round value) and solve for the other:
   `R3 = R4 * (Vout_target / Vref - 1)`.
   For 7.5 V -> R3 = 1k * (7.5/1.23 - 1) = **5.28 k** -> nearest E24 = **5.1 k**.
3. **Encode in the deck.** Put the chosen R3/R4/Vref into `lm2596-divider.cir`
   as `.param`s. The deck has two cross-checks:
   - **(A) forward** — apply `Vout_target`, confirm the FB node lands on Vref
     (proves the divider ratio is right);
   - **(B) loop-closed** — pin FB to Vref with an ideal source (this is what the
     regulator does in steady state) and **read back the Vout the divider
     demands** (proves which rail the part will actually servo to).
4. **Simulate.** `ngspice -b lm2596-divider.cir` runs the `.op` and prints
   `v(vout_*)`, `v(fb_*)`, and the ratio.
5. **Read back.** Compare the printed `v(vout_b)` to the target.
6. **Adjust & re-check.** If it's off, bump R3 to the next E24 value and re-run
   — or use `lm2596-divider-sweep.cir`, which sweeps R3 and prints the resulting
   rail for a range of E24 values in one shot, so you pick the closest fit
   directly from the table.

The deck _is_ the artifact of the loop: changing the target means editing two
`.param` lines and re-running, not rewriting equations.

## Worked result

Simulator status: **no command-line SPICE was available** on this host (details
below), so the read-back values are **hand-computed** and the deck is left
**ready to run**. The algebra is the same arithmetic the `.op` performs, so the
numbers below are exactly what the deck would print.

### As-designed +7.5 V rail (the loop's "verify" pass)

| Quantity                      | Value                             |
| ----------------------------- | --------------------------------- |
| R3 (top), R4 (bottom)         | 5.1 kOhm, 1.0 kOhm                |
| **Vout = 1.23 * (1 + 5.1/1)** | **7.503 V** (target 7.5 V)        |
| FB node at Vout = 7.5 V        | 7.5 * 1/(5.1+1) = 1.2295 V ~= Vref |
| ratio v(vout)/Vref            | 6.1 = (1 + 5.1/1)                 |

Error vs target: **+0.04 %** — the as-designed divider is correct.

### Loop "adjust & re-check" pass — retarget to +13.5 V

To show the loop doing real work, retarget the same topology to **+13.5 V** (the
voltage the +12 V rail's pre-regulator would need), holding R4 = 1 kOhm:

- Solve: R3 = 1k * (13.5/1.23 - 1) = **9.976 k**.
- Candidates read back from the sweep deck:

| R3 (E24)  | Vout = 1.23 * (1 + R3/1) | error vs 13.5 V |
| --------- | ------------------------ | --------------- |
| 9.1 kOhm  | 12.423 V                 | -7.98 %         |
| **10 kOhm** | **13.530 V**           | **+0.22 %**     |
| 11 kOhm   | 14.760 V                 | +9.33 %         |

-> pick **R3 = 10 kOhm**. That is the full loop: target -> compute -> read back
-> the first E24 guess (9.976k ~= 10k) is confirmed within 0.22 %.

## Simulator availability (honest notes)

- `ngspice` is **not on PATH**.
- KiCad is installed, but its bundle ships ngspice **only as a shared library**
  (`libngspice.0.dylib`) plus code-model `.cm` files — usable from KiCad's GUI
  simulator, but there is **no command-line `ngspice` executable** and
  `kicad-cli` has **no batch sim subcommand**.
- One non-interactive, timeout-limited install was attempted
  (`gtimeout 180 brew install ngspice`); it was **killed by the 180 s timeout
  mid-download** and, per the run guardrails, was **not retried**.

To run the decks for real:

```sh
brew install ngspice            # one-time, ~1-2 min
ngspice -b lm2596-divider.cir         # .op: prints vout/fb/ratio
ngspice -b lm2596-divider-sweep.cir   # R3 sweep -> rail-vs-R3 table
```

The expected output is documented in `command-log.txt` and matches the
hand-computed table above (a documented blocker with the concrete deck + worked
result intact, as the issue permits).

## How this extends (beyond value-sizing)

The same generate -> simulate -> read-back -> adjust loop scales up once a real
simulator is in place, by swapping the analysis (not the methodology):

- **Ripple / regulation on the rails** — replace the ideal FB pin with a buck
  behavioural model (or the actual LM2596 SPICE subckt + L, catch diode, Cout),
  run a `.tran`, and read back peak-to-peak output ripple; adjust **Cout / L**
  and re-check against the `<1 mVp-p` target. Value-sizing the **output cap**
  instead of the divider, same loop.
- **Line/load regulation** — `.dc` sweep of Vin (or a load step in `.tran`) and
  read back delta-Vout; size the feedforward / compensation.
- **Linear post-regulator headroom** — `.op` across the LM7805/LM7812/LM7912
  with worst-case Vin to confirm dropout margin; size the pre-reg rail.

In every case the loop is identical; only the measured node and the knob change.

## Files

- `lm2596-divider.cir` — `.op` deck: forward + loop-closed divider check.
- `lm2596-divider-sweep.cir` — R3 sweep deck (the "adjust & re-check" step).
- `command-log.txt` — exact discovery/install commands + expected sim output.
- `FINDINGS.md` — this document.
