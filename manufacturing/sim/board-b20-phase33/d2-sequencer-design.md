# D2 −12 V discharge sequencer: discrete design draft with a 3.9 V zener reference (adopted into the schematic 2026-11-14)

**Adopted 2026-11-14 JST** (`dec-b20-d2-sequenced-fast-discharge` in `scripts/schgen/decisions.json`): drawn in
`board_b20_spec.py` as Q7 / Q8 / Q9 / Q13 (QR / QP / QH / QN), D5 (DZS), RSQ1–RSQ4 and R81 / R82. **Correction:** the
supply node is `DIS_P`, not `DIS_C` as the table below says. `DIS_C` stays charged while the board is enabled; the
simulated deck feeds RSQ1 and QP from the disable-gated `dis` node, which is `DIS_P`. The table is kept as drafted.

The owner chose a 3.9 V zener reference on 2026-11-14 JST. This draft turns the behavioural sequencer that passed in
simulation ([record](d2-sequenced-20261114.md)) into parts. Nothing in the schematic, PCB, BOM or inventory changes
yet. D2 stays a PRE-ORDER HOLD.

## Function to realise
Clamp the −12 V discharge switch gate (`M12_DGN`) to its source (`M12_OUT`) while |−12 V| ≤ H and +12 V > R.
The calculation passes every case for H between 4 V and 6 V together with R between 0.5 V and 1.7 V
([`d2_sequenced.py`](d2_sequenced.py), ideal switches).

## Topology (proposed refs are placeholders)

| Part | Connection | Role |
| --- | --- | --- |
| QR, BSS138-7-F | G ← `P12_OUT` (10k series, 1M to GND); S GND; D `SEQ_EN_N` | On while +12 V > VGS(th): R = 0.5–1.5 V |
| RSQ1 100k | `DIS_C` → `SEQ_EN_N` | Pull-up; QP is off once +12 V is gone |
| QP, DMP3036SFG-7 | S `DIS_C`; G `SEQ_EN_N`; D → RSQ2 100k → `SEQ_G` | Supplies the clamp gate only during discharge and only while +12 V is present |
| RSQ3 100k | `SEQ_G` → `M12_OUT` | Clamp gate return |
| QH, BSS138-7-F | G `SEQ_G`; S `M12_OUT`; D `M12_DGN` | The clamp: holds the −12 V switch off |
| DZS, BZT52C3V9-7-F | cathode GND; anode `SEQ_Z` | Reference: QN turns on once \|−12 V\| > VZ + VGS(th) |
| RSQ4 4.7k | `SEQ_Z` → `M12_OUT` | Zener bias |
| QN, BSS138-7-F | G `SEQ_Z`; S `M12_OUT`; D `SEQ_G` | Releases the clamp while −12 V is still above H |

So H = VZ + VGS(th, QN). In normal operation DIS_C is low and QP has no supply, so QH stays off whatever QN does.

## The windows this gives, and what is not sourced
- **R:** BSS138-7-F VGS(th) 1.5 V max is sourced. The 0.5 V minimum is the project's PA, as in the phase-12
  interlock. That gives R = 0.5–1.5 V, inside 0.5–1.7 V.
- **H:** DS18004 guarantees BZT52C3V9 VZ only at IZT 5 mA, at 3.7–4.1 V. At the switching point the zener carries
  VGS(th)/4.7k = 0.1–0.3 mA, where only a typical curve exists. Taking VZ = 3.0–4.1 V there (PA) gives
  H = 3.5–5.6 V.
- **Corner check:** H 4.2–5.6 V with R 0.5–1.5 V passes every case in the calculation. The lowest corner, H 3.5 V with
  R 1.5 V, fails 18 of 10,935 cases. Closing it needs either a sourced low-current VZ or a lower release threshold.
- **Standing load:** with −12 V at 12.37 V, the bias draws (12.37 − VZ) / 4.7k ≈ 1.8 mA through the −12 V shunt.
  The −12 V trip minimum clears the start-into-full-load floor by about 13 mA, so this uses about 14 % of that margin.

## Open before adoption
- Candidate identity: the LCSC number for BZT52C3V9-7-F is not yet retrieved, so no candidate record exists.
- A sourced low-current VZ bound, or a design change that closes the H 3.5 V / R 1.5 V corner.
- Its own pre-registered simulation with FET and zener corner models, then the component audit, schematic and layout.
