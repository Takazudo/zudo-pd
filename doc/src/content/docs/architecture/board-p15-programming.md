---
title: Board P15 NVM Programming
sidebar_position: 6
description: Jig pull-ups, power-cycle reload and readback for shared P15 r1, with the desk 15 V NVM image.
---

This is the programming-jig procedure for shared P15 r1 (`boards/board-p15/`). That board is an
unvalidated draft. No step on this page has been run, and no NVM image has been written or read back.
Every result below is **NOT RUN**.

The board differs from the archived as-built procedure in [NVM Programming Setup](/docs/inbox/nvm-programming/)
in three ways:

- RESET is strapped to GND through the 0 Ω R21 (`dec-p15-reset-subset`). A RESET pulse cannot reload the NVM;
  only a full power cycle can.
- The I2C pull-ups are not on the board. R15/R16 to VREG_2V7 were removed, and the jig supplies the pull-ups.
- R22 and R23 (100 kΩ) pull SCL and SDA to GND, so both pins are defined in normal use
  (`dec-p15-i2c-pulldowns`). The jig pull-ups override them.

## One common Board P: the same P15 r1 serves the LED project first, then zudo-pd

On 2026-11-03 the user chose P15 r1 as the common Board P for the LED project and zudo-pd. Both use the same PCB, the same
population and the same 3 A image.

- LED bring-up with the existing Board L uses a P15 r1 unit first. The same board then goes to zudo-pd.
- Program and accept every P15 before it mates with anything. Board L and Board B stay disconnected through all of it:
  1. On a 5 V-only source, write, power-cycle, and pass P15-NVM-4 and P15-NVM-5 (steps 1–8 below).
  2. With no load connected, move to a PD test source that also offers 20 V and pass P15-NVM-6 (step 9). A 5 V-only
     source cannot exercise this test.
  3. Only then connect Board L or Board B.
- The output voltage window depends only on the NVM image. No hardware window follows the sink switch. This is an
  accepted residual at the prototype stage (LED requirement R2.3).
- The referenced manager report `led-p15-compatibility.md` is absent from this checkout. Its accessible summary is in
  `boards/board-p15/README.md`.

## Datasheet facts are from DS12499 Rev 7; the Rev 8 copy named by the owner bundle was not re-read

The owner bundle `component-stusb4500qtr` cites DS12499 **Rev 8** (sha256 `82d6080e…`). That copy is not in this
repository and was not re-read for this page. The facts below were read from **Rev 7** (sha256 `407ee676…`).
Those bytes are identical to `Doc/stusb4500_datasheet_v7.pdf` in ST's `usb-c/STUSB4500` GitHub repository
at commit `55d1109e`. Both copies are mirrors: no st.com primary retrieval is established.

| Fact | Value | Source |
| --- | --- | --- |
| SCL, SDA type | SCL DI, SDA DI/OD, external pull-up | Rev 7 p. 4 Table 1, p. 6 Table 3 |
| No-MCU minimum implementation | SCL and SDA tied to GND | Rev 7 p. 25 Fig. 9 |
| VIH min, VIL max (digital I/O, SCL and SDA included) | 1.2 V, 0.35 V | Rev 7 p. 30 Table 22 |
| VOL max | 0.4 V at 3 mA | Rev 7 p. 30 Table 22 |
| I/O operating range | 0 to 4.5 V | Rev 7 p. 28 Table 21 |
| I/O absolute maximum | −0.3 to 6 V | Rev 7 p. 27 Table 20 |
| I2C speed, rise time, bus capacitance | ≤ 400 kHz, tr ≤ 300 ns, Cb ≤ 400 pF | Rev 7 p. 18 Table 15 |
| NVM reload | after each NVM write, by power-off and power-up, or by reset | Rev 7 p. 19 §5 |
| Power-up load start | VREG_1V2 reaches 1.08 V; first I2C access after TLOAD | Rev 7 p. 24 |
| TLOAD max | 30 ms | Rev 7 p. 29 Table 22 (bundle `fact-stusb-load-time` cites Rev 8) |
| RESET | active-high input | Rev 7 p. 4 Table 1 |
| SCL and SDA pulled down with neither VDD nor VSYS | **not found in Rev 7**; Rev 8 only, per the bundle fact `fact-stusb-pin-states` | Rev 8, not re-read: UNVERIFIED |
| Input leakage on SCL, SDA; back-powering through I/O pins | not stated | UNKNOWN |

## Jig pull-up: 3.3 V through about 1–3.4 kΩ, never from VREG_2V7

The jig must supply its own pull-ups to a rail of at most 4.5 V, the I/O operating maximum. A 3.3 V
NUCLEO-F072RB rail is suitable. **Do not take the pull-ups from J3.3**: that pad is VREG_2V7, and loading it is
the R1.3 objection that removed R15/R16.

Each bound below holds with the 100 kΩ pull-down present, taking its 1 % low value of 99 kΩ:

- **Sink limit (lower bound):** at least (Vpu − 0.4 V) / 3 mA, so the STUSB4500 can pull SDA to VOL 0.4 V.
- **Rise time (upper bound):** from 30 % to 70 % of Vpu with the Thevenin source Rpu ∥ 99 kΩ, tr ≤ 300 ns.
- **High level:** Vpu × 99 kΩ / (Rpu + 99 kΩ) must reach VIH 1.2 V. This bound does not limit the range.

| Jig rail | Rpu min | Rpu max, Cb 50 pF | 100 pF | 200 pF | 400 pF |
| --- | --- | --- | --- | --- | --- |
| 3.3 V | 967 Ω | 6.49 kΩ | 3.39 kΩ | 1.73 kΩ | **none** (875 Ω < 967 Ω) |
| 4.5 V | 1.37 kΩ | 6.49 kΩ | 3.39 kΩ | 1.73 kΩ | **none** (875 Ω < 1.37 kΩ) |

- The pull-downs cut the rise-time bound by about 4 %: without them, the 100 pF bound is 3.54 kΩ.
- With the 99 kΩ pull-down, the high level is 3.19 V at 3.39 kΩ from 3.3 V. VIH is 1.2 V.
- **Recommended starting point:** 3.3 V through 2.2 kΩ. That sinks 1.32 mA and meets tr ≤ 300 ns up to about 160 pF.
- **Still OPEN:**
  - The pogo clip and wire capacitance is not measured.
  - The master's own low level must stay below the STUSB4500 VIL of 0.35 V at the chosen sink current. The
    Nucleo's VOL at 1.3 mA is not taken from its datasheet here. Measure it.
- In normal use, the pull-down keeps the pin below VIL for any pin leakage under 3.46 µA
  (0.35 V / 101 kΩ). The leakage itself is UNKNOWN.

## Procedure: write once, then accept only a power-cycle readback

Steps 1–8 run from a **current-limited 5 V-only source** with Board B and Board L disconnected. The archived page explains
why a factory 20 V request must never reach an unprogrammed board. Step 9 is the only step on a PD source, and it
follows a passing step 7 readback. Board B and Board L stay disconnected until step 9 passes.

1. **Power up.** Apply 5 V. Check J3.4 (VBUS_IN) at about 5 V and J3.3 (VREG_2V7) at about 2.7 V.
2. **Connect the jig.** Enable the jig pull-up rail only now, and clamp the pogo clip to J2:
   - J2.1 SCL, J2.2 SDA, J2.3 GND;
   - J2.4 is NC and unused.

   With the pull-ups on, SCL and SDA idle at the high level in the table above. With the clip off, they read
   about 0 V because of R22/R23.
3. **Dump.** Read and save the 40 NVM bytes (sectors 0–4) with their SHA-256. This is the pre-write record.
4. **Write.** Write `boards/board-p15/nvm/stusb4500-15v.bin`
   (sha256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`).
5. **Immediate readback.** It must equal the file. This alone does not prove the image will load.
6. **Full power cycle.**
   - Remove the jig pull-up rail first. Back-powering through SCL/SDA is UNKNOWN.
   - Then remove VBUS and wait until J3.3 reads below 0.1 V. The 0.1 V level is a project choice; ST gives the POR
     release level, 1.08 V on VREG_1V2, but no reset level.
   - Re-apply 5 V, wait at least TLOAD (30 ms), then re-enable the jig rail.
   - A RESET pulse is not available: R21 holds RESET low.
7. **Power-cycle readback.** Read the 40 bytes again. **Accept only an exact match with the file's SHA-256.** Then
   read the volatile PDO registers 0x85–0x90 (UM2650 Rev 3, mirror) and check PDO2 = 15 V / 3 A and two sink PDOs.
8. **Disconnect.** Remove the jig rail, then the clip. Remove the 5 V-only source.
9. **First PD attach (P15-NVM-6).** Move to a PD test source that also offers 20 V, through a current-limited path,
   with Board B and Board L still disconnected. VBUS_OUT (JOUT1.1/2) must stay off at 5 V, then follow 15 V after the
   15 V contract. Measure VBUS_OUT during the 5 V phase of attach, before the 15 V request, and fail the unit if it
   rises. This is the only evidence that POWER_ONLY_ABOVE_5V works: its bit position is third-party and an ST draft
   note marks that bit reserved (see below).
10. **Connect the load.** Only after step 9 passes, connect Board L or Board B.

## 15 V NVM image: desk-built from a third-party field map, checked against the Rev 7 defaults

`scripts/pcb/board-p15/nvm-image.py` writes `boards/board-p15/nvm/stusb4500-15v.bin` and its record
`stusb4500-15v.json`. `--check` rebuilds both and fails on any difference.

| Field | Value | Changed from the default |
| --- | --- | --- |
| SNK_PDO_NUMB | 2 (PDO1 5 V, PDO2 15 V; 20 V is never requested) | 3 → 2 |
| PDO2 | 15.00 V, I_SNK_PDO2 1011b = 3.00 A (Rev 7 Table 17) | 1.5 A → 3.0 A |
| POWER_ONLY_ABOVE_5V | 1 (VBUS_EN_SNK only after a PDO2/PDO3 contract), set as 0xE6 bit 3 from the SparkFun map; position CONFLICTED (2026-11-08) | 0 → 1 |
| Every other field | the Rev 7 default | no |

- **Base bytes and field positions:** both come from the SparkFun STUSB4500 Arduino library (MIT, commit
  `7f76188b`). That is a **third-party** source; no ST NVM map document is retained here.
- **Check:** decoding the base bytes with those positions gives every default in Rev 7 Tables 16–18 that the
  script checks. The other bits are not checked.
- **Conflict (2026-11-08):** an ST draft technical note lists 0xE6 as `VBUS_CTRL` with bits [3:0] reserved, so the
  POWER_ONLY_ABOVE_5V position used here rests on SparkFun and one non-ST GUI diff only. The image is unchanged.
  Step 9's VBUS_OUT-off-during-5 V measurement is the acceptance evidence; record and source:
  [PD20 evidence research](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/pd20-evidence-research.md).
- **ST example not used:** the example image in ST's `NVM_Flasher` (commit `55d1109e`) is a customised image,
  not the factory default.
- **Acceptance:** the image is accepted only by step 7 above. Until then its status is NOT RUN.

## Acceptance tests: all NOT RUN (no hardware)

| ID | Test | Pass |
| --- | --- | --- |
| P15-NVM-1 | SCL/SDA with the clip off, board powered | below 0.35 V |
| P15-NVM-2 | SCL/SDA high level and low level with the jig on; rise time on a scope | high ≥ 1.2 V; low ≤ 0.30 V; tr ≤ 300 ns |
| P15-NVM-3 | Pre-write dump saved with its hash | file and hash recorded |
| P15-NVM-4 | Power-cycle readback (step 7) | equal to sha256 `76622e14…` |
| P15-NVM-5 | PDO registers after the power cycle | 2 sink PDOs, PDO2 15 V / 3 A |
| P15-NVM-6 | First attach to a 20 V-capable PD test source (step 9), no load connected | 15 V contract; VBUS_OUT off at 5 V |
| P15-NVM-7 | VDD (U1.24, via C2.2) at a 4.75 V input during communication | ≥ 4.1 V (attach margin with the 1.47 kΩ feed) |
