# PD20 evidence research, 2026-11-08

**Unvalidated desk research. Nothing here is validated, qualified, released or ordered, and no 20 V NVM binary
exists.** Base: `main` at `6b08236`. Tracking: Takazudo/zudo-pd#231 (parent #228). Every source below was fetched in
the research container on 2026-11-08 and is identified by URL and SHA-256; none is stored in this repository.

## TDISPAR0V is located: NVM 0xCA bits 7:4

| Item | Finding |
|---|---|
| Position | NVM byte 0xCA = sector 1, byte 2. Bits [7:4] are `DISCHARGE_TIME_TO_0V` (the datasheet's TDISPAR0V); bits [3:0] are `VBUS_DISCH_TIME_TO_PDO` (TDISPARPDO). Default 0x9C |
| Source | ST technical note "TNxxx, STUSB4500 NVM registers, description and generic access", 39 pages, ST template, PDF created 2019-05-10, no revision number. Pages 4–5 (bank map and defaults) and 22 (`DISCHARGE_TIME_CTRL`). SHA-256 `a1f35ffea672cef0a32bbd818dd7f5795cfe4bd641960bbf70a5b2374a3927e4` |
| Provenance | Attached by an ST technical moderator to ST Community thread 157984 on 2025-10-13 ([thread](https://community.st.com/others-hardware-and-software-57/stusb4500-clarification-on-vbus-discharge-default-configuration-and-nvm-address-details-157984); attachment `community.st.com/topic/trackAttachment?file_uuid=42542a85-96dd-517f-8a98-5fdc9af66b5a`). The same moderator post places `VBUS_DISCH_DISABLE` at 0xC9 bit 5, which matches the note |
| Corroboration | The note's default table equals the repository's base bytes for all 40 bytes (`scripts/pcb/board-p15/nvm-image.py` BASE). The 0x9C nibbles equal the datasheet defaults TDISPAR0V = 9 and TDISPARPDO = 12 (DS12499 section 5 table: 84 ms and 24 ms typical units; electrical table 70 / 84 / 100 ms × TDISPAR0V) |
| Authority | Manufacturer-authored but an unnumbered draft (`TNxxx`) distributed through a forum. Treat it as MANUFACTURER_DRAFT, stronger than the third-party map and weaker than a released document |

Required discharge (existing calculation, `scripts/pcb/calculate-input-ovp-20v.py`): 0.906 s. Candidates, using the
70 ms minimum unit:

| TDISPAR0V | Byte 0xCA | TDISUSB0V min / max | Margin over 0.906 s |
|---|---|---|---|
| 13 | 0xDC | 0.910 / 1.300 s | 0.4 % |
| 14 | 0xEC | 0.980 / 1.400 s | 8 % |
| 15 | 0xFC | 1.050 / 1.500 s | 16 % |

The value is an **owner decision** and is not written into the partial bytes. 13 has almost no margin. Whether a
longer discharge interacts with source re-application after a hard reset is not stated in any retained document
(bench T8).

## Lower-current 20 V source: the sink does not enable VBUS_OUT (DS12499 Rev 8)

DS12499 section 3.3.2 (decision algorithm): a sink PDO matches a source PDO only when `V(SNK_PDOi) = V(SRC_PDOj)` **and**
`I(SNK_PDOi) ≤ I(SRC_PDOj)`. With PDO2 = 20 V / 5 A and SNK_PDO_NUMB = 2, a 20 V offer below 5 A (a 3 A cable, for
example) does not match PDO2. The comparison falls to PDO1, giving an explicit 5 V contract (or, with no match at all,
a 5 V RDO with capability mismatch set). Table 6 and section 6.1.2: with POWER_ONLY_ABOVE_5V = 1, VBUS_EN_SNK stays
Hi-Z unless a PDO2 or PDO3 explicit contract exists, and "in case of mismatch, the VBUS power path remains open while
the source provides 5 V". So Q1 stays off, which satisfies "no degraded mode" **if** the POWER_ONLY_ABOVE_5V bit is in
the position the image writes (next section).

- Source: DS12499 **Rev 8** (November 2022), sections 2.2.10 (Table 6), 3.3.2 and 6.1.2. The owner supplied the copy
  on 2026-11-08 (SHA-256 `82d6080e6d3e994f0969f4f018039d1f0871db9f6793c80c09e63e80325029e8`), byte-identical to the
  retained `src-stusb-ds12499` mirror. The Rev 2 Farnell mirror (SHA-256 `650afb8f…`) carries the same text.
- Residual: if a source re-advertises 20 V below 5 A during an established 20 V contract, the behaviour of
  VBUS_EN_SNK through the transition is not stated (bench T8).

## POWER_ONLY_ABOVE_5V position conflicts with the ST note (affects P15 too)

The 20 V intent and the shared P15 image (`boards/board-p15/nvm/stusb4500-15v.bin`, SHA-256 `76622e14…`) both set
0xE6 bit 3 (0x40 → 0x48) for POWER_ONLY_ABOVE_5V, from the SparkFun field map (THIRD_PARTY). The ST note lists 0xE6 as
`VBUS_CTRL`: [7:5] reserved 0b010, [4] REQ_SRC_CURRENT, **[3:0] reserved 0x0**. The only other location statement is a
non-ST user who diffed GUI exports (ST Community thread 32193, 2023-11-02: "bit 3 of NVM Address 0xE6 … In TNxxx … the
bit is undefined"). ST's own example image (`usb-c/STUSB4500` `STUSB_NVM.h`, SHA-256 `7505a772…`) has 0xE6 = 0x50, bit
3 clear, so it neither confirms nor refutes the position.

Consequence: P15 acceptance must not rely on the NVM alone to keep Q1 off at 5 V. The existing per-unit acceptance
sequence (no-load PD acceptance on a source also offering 20 V, before downstream connection) is where this shows. Add
an explicit check that VBUS_OUT stays off during the 5 V phase of attach. This is reported to the manager; the P15 image
and its records are not changed here.

## Board P Q1 inrush SOA: desk margin about 2× at 25 °C

Q1 DMP3036SFG-7 closes only on a 20 V contract (POWER_ONLY_ABOVE_5V). The C36/Q5 Miller network slews VBUS_OUT at
3.1–10 V/ms (`board_p_spec.py`). B20 holds its converters off until RDY (≥ 0.21 s), so the inrush is capacitive.

| Input | Value |
|---|---|
| B20 VIN capacitance, upper bound | 186 µF: C1 RVT1H101M0810 100 µF +20 %, six GRM32ER71H106KA12L 10 µF +10 % with no DC-bias reduction, two 100 nF |
| VBUS_OUT | 21 V (20 V + 5 %) |
| Energy in Q1 | ½CV² = 41 mJ, independent of slew |
| 10 V/ms | 1.86 A, 39 W peak, 2.1 ms |
| 3.1 V/ms | 0.58 A, 12 W peak, 6.8 ms |
| Fig. 12 SOA (DS37038 Rev 6-2, retained hash `7d68df47…`), read from the graph at 20 V | 1 ms ≈ 8 A (≈ 160 W); 10 ms ≈ 1.2 A (≈ 24 W); single pulse, TA 25 °C, VGS −10 V, minimum-pad board |
| Allowed rectangular pulse (log interpolation) | 2.1 ms ≈ 87 W; 6.8 ms ≈ 33 W |
| Margin, treating the triangular pulse as rectangular | 2.2× (10 V/ms), 2.7× (3.1 V/ms); 1.6× and 2.0× after linear derating to TA 60 °C |

Status: **desk PASS (graph read)**. The SOA is read from a printed curve, not a manufacturer statement for this
waveform. Linear-mode stability at the actual VGS is not characterised. If C36 or Q5 fails open the slew falls back to
the 0.46 ms gate constant, which is a single fault outside this screen. Bench T3 still owns the measurement.

## 1206 discharge resistors: one event sits inside the short-time-overload test

UNI-ROYAL "Thick Film Chip Resistors" V.7 (2022-10-13, SHA-256 `9e71ced0…`, already retained for the project passives)
gives for 1206: 1/4 W, RCWV = √(P·R), short-time overload at 2.5 × RCWV (or 400 V, whichever is lower) for 5 s with
ΔR ≤ ±(1.0 % + 0.05 Ω) for ±1 % parts. No pulse-energy or repetitive-pulse curve is published.

| Rail (part) | Peak V (load-band maximum) | 2.5 × RCWV | Ratio | One-shot window at peak (externally held inlet) |
|---|---|---|---|---|
| +12 V, RX12 100 Ω (1206W4F1000T5E) | 12.48 V | 12.50 V | 99.8 % | 1.56 W for ≤ 1.33 s |
| −12 V, R76 150 Ω (1206W4F1500T5E) | 12.37 V | 15.31 V | 81 % | 1.02 W for ≤ 1.33 s |
| +5 V, RX5 33 Ω (1206W4F330JT5E) | 5.20 V | 7.18 V | 72 % | 0.82 W for ≤ 1.33 s |

The zero-load discharge (τ 18 / 27 / 4 ms) and the worst single event with the inlet held for the whole 0.48–1.33 s
window both stay inside the 5 s test condition. Status changes from OPEN to **single event inside the manufacturer
test envelope; repetition UNSOURCED**. +12 V has no voltage margin, and T5's 100 cycles and field repetition are not
covered by a one-time qualification test. A pulse-rated part remains a component change that needs owner approval.

## Capacitor DC-bias curves are still not retained

Murata (`GRM32ER71H106KA12-01.pdf`) and YAGEO MLCC datasheet URLs returned HTML instead of PDFs from the research
container, and SimSurfing is interactive. C43 (CC0603KRX7R9BB104 at about 33 V) and the six B20 VIN 10 µF parts at
20 V remain without retained DC-bias data. On 2026-11-08 the owner supplied YAGEO "Surface-Mount Ceramic Multilayer Capacitors, General Purpose & High Cap.
X7R 6.3 V to 250 V" Version 27 (2026-03-06, SHA-256 `3aa10c5d01fbea28f638f1e4bca56a14b9b3342f593d68641830b1cbdb3720e6`).
It publishes no capacitance-versus-DC-bias curve for C43's line; it gives only the ±15 % X7R temperature characteristic.
The owner also supplied a text extract of Murata's general catalog (C02E, 2021-01-18), which does not list
GRM32ER71H106KA12. The gap therefore stays open for both parts. The SOA screen above uses nominal +10 % capacitance, which bounds the inrush
from above.

## U6 decoupling (B20 PCB C35): measured, handed to the B20 layout owner

The pinned KiCad 10.0.6 image runs in this container. On `boards/board-b20-draft/board-b20-draft.kicad_pcb` at `6b08236`,
C35 (100 nF, P5_SUP/GND) sits at (102.5, 14.55) mm and U6 OPA2187 at (72.0, 60.0) mm: 52.3 mm from U6 pin 8 (P5_SUP)
and 57.2 mm from pin 4 (GND). `scripts/pcb/board-b20/` belongs to the PD20 load-case work, so no layout change is made
here. The fix is a placement constraint that keeps the decoupling capacitor next to its IC, then a full re-route and
native DRC.
