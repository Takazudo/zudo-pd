# D2 bounded sensitivity (PR #307 independent review, 2026-11-20)

CALCULATED (`sensitivity.py` → `sensitivity.json`) plus an exploratory, NOT pre-registered SIM bound
(`resim.py` → `resim.json`; vendor CSD18543Q3A model, ngspice-44.2 in the pinned KiCad image, generic small-part
corner models as in `d2-sequencer-circuit-criteria.md`). Neither is measured. Electrical acceptance stays NOT ESTABLISHED.

Inputs (sha256): PCB `7a8270f5…` (`boards/board-b20-draft/board-b20-draft.kicad_pcb`), spec `4084d845…`
(`scripts/schgen/board_b20_spec.py`), `loop-resistance.txt` `25eecc6b…`, `d2_sequenced.py` `ba6f97d2…`,
`d2-sequenced-20261114.json` `94784f1f…`, `d2-sequencer-circuit-20261114.json` `3903bb2d…` (full list in `sensitivity.json`).

## Layout parasitics and part tolerances preserve every pre-registered row at the simulated firing timing

| Rail | Nominal | Worst series total (hot, J11 bank) | Fast corner |
| --- | --- | --- | --- |
| +12 V | 0.5 Ω | 0.600 Ω (+20.1 %) | 0.494 Ω (−1.2 %) |
| +5 V | 0.5 Ω | 0.621 Ω (+24.2 %) | 0.494 Ω |
| −12 V | 1.5 Ω | 1.664 Ω (+11.0 %) | 1.482 Ω |

Terms: WSL ±1 % and 75 ppm/K (C511023 owner), RDS(on) 15.6 mΩ max at 4.5 V × 2.0 hot (PA: SLPS633 hot data is a
typical curve only), routed rail copper (`loop-resistance.txt`), pulse-net copper (one 1.2 mm B.Cu segment per net, no
vias, ≤0.6 mΩ), GND vias at 18 µm plating (Q51 has **2** source vias, not the three the README states; Q52 4, R76 4),
In1 (17.5 µm from the stackup) spreading `3 × (Rs/π)·ln(d/√(ab))` ≤ 5.3 mΩ (factor 3 is PA: half-plane × antipads),
all copper at 85 °C (0.393 %/K). The worst total is ~2× the README's "≤12 %" because RDS(on) and the GND return are
included.

- Calc (two-node model: bank-side copper between the OSC bank and the board node the sequencer senses), the
  pre-registered fire grid, 8 independent per-rail fast/slow corners × 5 threshold sets: behavioural, `hlrl`, `hhrl`,
  `hhrh` 0 failing in every corner. `hlrh` (ideal-threshold artefact the SIM already cleared) 18 → up to 162.
- SIM, same timing, parasitics applied: `hhrl` `plnhfh-mzm` and `ceil-mzp` PASS, |−12 V| once +12 V absent 5.648 / 5.653 V
  (control 5.645 V; ≤ 6 V). `hlrh`/`hlrl` `phnlfl-zmz` PASS, |−12 V| while +12 V present 0.906 V at the bank, 0.93 V at the
  board (control 0.98–0.99 V; > 0.6 V).
- Disconnect before discharge: every deck disconnects before the EN_N crossing; the earliest onset in any deck here is
  16.6 µs after it.
- Level time ≤ 1.29 ms (calc) / 1.25 ms (SIM) against 100 ms, the 19 ms minimum-off interlock and the ≥ 0.1 s hold-up.

## R62 47.5k and 47 nF + 22 nF move the −12 V firing by +0.58 µs

They set the Q55 turn-on delay: Thevenin of R61 4.7k / R62 from DIS_C to M12_OUT into CDGN. τ 294.3 → 298.9 µs,
V∞ 15.700 → 15.715 V, t(VGS(th) typ 2.0 V) 40.11 → 40.69 µs (simulated onset 40.5–48.2 µs). Negligible on its own.

## The firing-network tolerance band is not covered by the pre-registered sweep and fails R-VEE (pre-existing, not layout)

Guaranteed VGS(th) 1.5–2.7 V (25 °C only), CDG/CDGN tolerances and Ciss max give Q51/Q52 firing at −48…+85 µs and Q55 at
−13…+20 µs about nominal. With PA hot-threshold (−0.3 V) and X7R DC-bias (−25 %) terms: −80…+123 µs and −22…+22 µs.
`FIRE_S` swept only ±35 µs on +12 V.

| Deck (exploratory SIM) | Timing | Resistors | Result |
| --- | --- | --- | --- |
| `hlrh phnlfl zmz` | guaranteed only: +12 V onset 262 µs, −12 V 28 µs | nominal | **R-VEE fail**: |−12 V| 0.39 V while +12 V present |
| same, `hhrh` | guaranteed only | +12 slow / −12 fast | **fail**, 0.53 V |
| `hhrl plnhfh mzm` | guaranteed only: +12 V 99 µs, −12 V 68 µs | +12 fast / −12 slow | PASS, 5.65 V |
| `hhrl plnhfh mzm` | with PA terms: +12 V 57 µs | nominal | **fail**, 6.09 V |

Mechanism: the sequencer holds the −12 V switch off but cannot stop OSC's −12 V maximum load from draining a small bank
below 0.6 V while a late +12 V switch has not yet fired. Parasitics change these margins by ≤ 0.03 V. This is not a
formal reading (it is not pre-registered), but it shows D2's margin depends on switch-threshold spread that no record
bounds.

## Model limits that remain

Resistive loads, ideal-threshold calc, generic small-part models, timing applied by rescaling CDG12/CDGN, no cable
resistance on the OSC side, and an RDS(on) hot factor and In1 factor that are project assumptions.
