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

## 2026-11-09 disposition: exact capacitor curves and ST primary access

The findings above remain the dated 2026-11-08 record. This follow-up inspected source bytes against adopted
revision `c32d4e636dc6f9a5e469ea95b5f3d7b57a85c199`; no circuit, NVM image, physical result or frozen package changed.

| Exact identity / source | Acquisition and inspected locator | Bounded finding |
|---|---|---|
| Yageo CC0603KRX7R9BB104 / C14663, C0603, B20 C43 | [Manufacturer specsheet](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104), generated 2026-11-08, retrieved 2026-11-09; valid PDF, 285417 bytes, SHA-256 `839100c3a478a2fb03e06f444e895bca6d40706c9f5682c080ed751cebdb8050`. Page 2 (physical index 1), lower-right DC voltage bias figure; page 4 disclaimer | Approximate visual read: −44% at 33 V (~56 nF) and −50% at 37.6 V (~50 nF), using nominal 100 nF. **Typical manufacturer simulation, not a guaranteed installed minimum.** Temperature, tolerance, aging and local-loop performance remain unqualified. Owner source `src-c14663-yageo-simulation-20261109`, fact `fact-c14663-b20-c43-dc-bias-curve`; older generated-sheet hash preserved |
| Murata GRM32ER71H106KA12L / C77102, C1210, B20 VIN bank | Existing [exact-part mirror](https://datasheets.b-cdn.net/files/GRM32ER71H106KA12L-Murata-datasheet-12553172.pdf), 2012-11-10; re-fetched valid PDF, 97579 bytes, SHA-256 `59b89eed344603cf4778bebb61ba60f887e3a33a8fd5f433c4651b25353f9100`, identical to `src-grm32er71h106ka12l-datasheet`. Page 1 explicitly lists L/K/B packaging; page 2 (index 1), left-middle DC-bias figure | Approximately −30% at 20 V (~7 µF nominal basis), **typical mirror evidence only**. The older 15 V fact is not a 20 V value. The sheet warns that figures can share another part's characteristics and calls specifications typical. Added `fact-grm32er71h106ka12l-dc-bias-20v`; primary approval and installed minimum stay open |
| STUSB4500QTR / C2678061 | [Canonical ST DS12499](https://www.st.com/resource/en/datasheet/stusb4500.pdf) now downloads directly: Rev 8, 2007449 bytes, SHA-256 `82d6080e6d3e994f0969f4f018039d1f0871db9f6793c80c09e63e80325029e8`, equal to the existing mirror. Section 3.4.2 page 13 (index 12), configuration page 20 (index 19), timing page 29 (index 28) | The dated primary-access failure is no longer current. Separate receipt `src-stusb-ds12499-primary-20261109` preserves old attempts/mirrors and does not bulk-promote their dependent facts. Initial matching was already answered; established-contract downgrade behavior remains open |

Thus the earlier “no retained curves” summary is superseded: the exact Yageo curve is now acquired and the Murata
owner already carried an exact-part historical mirror curve. Neither supplies a guaranteed installed-capacitance
bound. The nominal +10% inrush/SOA upper-bound screen remains unchanged. C43 and U6's C35/CU6D are separate
placements and separate implementation tasks despite sharing C14663.

The direct Murata URL `https://search.murata.co.jp/Ceramy/image/img/PDF/ENG/GRM32ER71H106KA12-01.pdf` returned HTTP 404
on 2026-11-09; it supplied no PDF. No unrelated-family curve was substituted.

### Official GUI acquired; paired mapping exports NOT RUN

The official [usb-c/STUSB4500 tooling repository](https://github.com/usb-c/STUSB4500) at
`55d1109e7ef0cffc2ffef2494095d23306594601` provides
[`GUI/App/STSW-STUSB002 v1.0.8.zip`](https://github.com/usb-c/STUSB4500/blob/55d1109e7ef0cffc2ffef2494095d23306594601/GUI/App/STSW-STUSB002%20v1.0.8.zip).
Downloaded ZIP SHA-256: `e391ce62bda04bd023780efc8c30ede9917b690ca2a827c004788720d8ee6bf0`.
Its `STUSB4500_GUI_1.08.exe` is 236032 bytes, SHA-256
`a15e40a163123c5f15585fd8de2a8696b14b01a786583926ac3380f296fe5fce`.
The same revision's `GUI/readme.md` (3999 bytes, SHA-256
`96413300ed14cef06c4490963973270dedd88aa77e5aa579d3b0227ff4a2be9c`) specifies Windows.
Wine and a virtual-display launcher were not installed in this Cloud run. The executable was not run and no exports
were produced. Acquisition alone does not resolve POWER_ONLY_ABOVE_5V.

The smallest software evidence step is a reviewed pair of offline exports from this pinned official GUI: keep every
setting identical except POWER_ONLY_ABOVE_5V, retain settings/screenshots and hashes, and compare all 40 bytes.
This would be official-tool evidence, not physical readback. The existing bit-position conflict remains open;
the frozen P15 image and the blocked PD20 intent are unchanged.

### TDISPAR0V recommendation remains an owner decision

Recommend **15 for owner review** when prioritizing discharge margin: the existing conditioned 0.906 s requirement
gets a 1.05 s minimum (~16% margin), versus 0.98 s (~8%) for 14. The tradeoff is 1.50 s maximum versus 1.40 s.
13's ~0.4% margin is too small to recommend. No value has been selected or applied.

DS12499 section 3.4.2 explicitly applies this discharge window during hard reset as well as disconnect/error recovery.
A longer window can therefore extend discharge/recovery interaction with source VBUS reapplication; the retained
sources do not establish that interaction or its compliance. Review source timing and measure T8 before treating the
choice as qualified. Do not infer that 15 is unconditionally safer, or produce a program-ready image before the
configuration decision and mapping evidence are resolved and reviewed.

### Repetitive resistor endurance remains UNSOURCED

The exact UNI-ROYAL SMD-SP-001 V.7 [manufacturer PDF](https://www.uni-royal.cn/en/images/userfile/file/1668661899c56505e6d9ab55c7.pdf)
was re-fetched on 2026-11-09: valid PDF, 815755 bytes, SHA-256
`9e71ced0af443ae5e320db644fade5b94d8a9d81bf74a421e5f98cd61e3efa74`, identical to the existing lock.
It covers 1206W4F1000T5E/C17901 (RX12), 1206W4F1500T5E/C17917 (R76) and 1206W4F330JT5E/C18005 (RX5).
Page 6 (physical index 5) distinguishes the 5 s short-time-overload test from load life: 1000 h at RCWV,
1.5 h ON/0.5 h OFF at 70±2°C. Rated-voltage cycling does not establish repetitive endurance for the installed
higher-voltage discharge pulse. No exact standard-series repetitive-pulse curve was found; AS/PS anti-surge
series evidence is for different orderables. Preserve the single-event screen, the repetitive-pulse gap and T5.
No supplier contact, substitution, programming or physical test occurred.

## Exact C12 and shunt primary documents — 2026-11-09 Mac follow-up

Holy Stone's manufacturer-hosted [HCN High Cap NP0 catalog](https://www.holystone.com.tw/downloads/series/10000/1000/60/20161108152237_file1.pdf)
(SHA-256 `cc8cdf6caa98e48459e1bb3f40b54c2489dfdd40d8e767ad45f2bb21726728bc`, no printed revision;
PDF creation date 2016-10-18) explicitly lists **C1206N473J050T/C5451690** on PDF page 6 (physical index 5):
47 nF, 1206, J tolerance, 50 V, thickness 1.6 ±0.2 mm. PDF page 2 defines J as ±5% and the NP0 temperature range
as −55 to +125 °C, coefficient ≤30 ppm/°C. The previous NCC catalog was the wrong series for establishing this
range; its historical omission is preserved, but the exact-part primary-specification gap is now closed. Installed
C12, its circuit behavior and mechanical acceptance remain unverified. No component was substituted.

RESI's manufacturer-hosted [E16009 V9 PCSR2512 sheet](https://s.resistor.today/shop/products/epdf/PCSR2512.pdf)
(SHA-256 `8305e9d8e0a9ff0b73aaa0772c2ecd9384482b9af488f032c6b8fac09d8f74ad`, revision V9 dated 2026-04-28)
explains the historical power-rating discrepancy. Printed page 15/16 (physical index 15) records the V5 upgrade
on 2024-07-30 from 1 W to 2 W for 5–10 mΩ. Printed page 1/16 specifies 2 W at +70 °C for that range;
page 2/16 decodes B/R010/M/6 as ±0.1%, 10 mΩ, ±15 ppm/°C, unmarked. The M9 table is not silently relabelled M6.
This supports the current family specification, but cannot identify the revision/date of supplier **C23067428**
stock. Keep the exact older M6 row's **1 W/10 A working bound**, and keep supplier-lot applicability and Kelvin-land
review open. At the contractual 2.1 A maximum, nominal 10 mΩ dissipation is 0.0441 W; neither this calculation nor
the document proves actual current let-through or assembled temperature.

The earlier UNI-ROYAL repetitive-pulse gap is unchanged. Rated-voltage load cycling and a single 5 s overload test
supply no guaranteed repetitive endurance for the higher-voltage discharge waveform. No supplier contact,
substitution, order, programming or physical result is implied by these acquisitions.

### Calculation applicability of the new exact-part evidence

C12 is the inverter's **CCCP compensation capacitor**, between C_CZ and M12_RAW, in series with RCCP 8.2 kΩ ±1%
from C_COMP (`board_b20_spec.py`). Its ±5% initial capacitance range is **44.65–49.35 nF**. The simple RC-zero
screen `1/(2πRC)` gives 412.960 Hz nominal and 389.402–439.086 Hz using both resistor and capacitor initial
extremes. This is an arithmetic sensitivity screen, not closed-loop stability or an installed capacitance minimum.
Temperature, the full compensation network and the converter/load operating point still matter.

The current phase33 tracking decks model converter outputs as stiff sources and do not contain CCCP/C12.
They therefore cannot qualify this compensation tolerance. Historical phase7 AC decks retain fixed 47 nF and
33 nF comparison runs; their recorded nominal-47 nF phase margins of 58.3–93.4° do not test the 44.65/49.35 nF
endpoints or qualify the final layout. A source-bound converter-loop tolerance sweep remains required before
using those historical numbers as final compensation evidence. No new AC simulation was performed here.

The current limiter desk calculation already uses the shunt's 10 mΩ, ±0.1% and 15 ppm/°C values. Its older
`G-U (distributor listing)` label predates the newly acquired primary specification. It applies a ±20 °C span
around a 25 °C reference, while the primary TCR table references 20 °C: for the same assumed 5–45 °C interval,
the maximum difference from the manufacturer reference is 25 °C. A conservative arithmetic check gives
`Rmax = 0.010 × (1 + 0.001 + 15e-6 × 25) = 0.01001375 Ω`; at the contractual +12 V maximum of 2.1 A,
`I²R = 0.0441606 W` (−12 V at 2.0 A: 0.040055 W). These values are below the retained 1 W working bound,
subject to actual temperature/derating and mounting. They do not establish the actual peak fault current,
let-through, pulse energy or shunt temperature. The calculator correction below reconciles the reference-temperature convention; wider operating conditions
and physical qualification remain open. No current ceiling is lowered or accepted here.


The owner calculator now uses the manufacturer's 20 °C reference while retaining the same 5–45 °C PA interval.
Fresh arithmetic gives +12 V trip 2.04159–2.08485 A (previously 2.04175–2.08470 A) and −12 V
1.94216–1.99544 A (previously 1.94231–1.99529 A). The existing start-floor comparisons remain numerically PASS;
+5 V is unchanged. Only `limiter` and dependent `limiter_startup` output sections changed. The illustrative
series-inductance screen at an assumed 2 µs switch-off becomes 1.624 mH / 5.351 mH (+12/−12 V), and stays OPEN:
the delay is not a guaranteed fault bound. No excess-current charge/time budget is adopted. These trip calculations
remain distinct from the required maximum delivered current and from physical acceptance.
