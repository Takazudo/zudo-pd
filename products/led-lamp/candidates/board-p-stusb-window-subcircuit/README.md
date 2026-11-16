# LED Board P r-next voltage window: standalone sub-circuit (UNADOPTED)

**State:** UNADOPTED desk source. **Integrated in [`../board-p-rnext-stusb-unadopted/`](../board-p-rnext-stusb-unadopted/README.md) without QINH/RG/RB/RBE and without the SMAJ20A** (see that README: Q1 is the contract gate there, an RG pull-up on the VBEN node would bias Q1's gate, and input surge belongs to the common front end). No schematic sheet, PCB, simulation or measurement exists.
It is not validated and must not feed any fabrication output.
It waits for the PD worker's common STUSB4500 block (`/mnt/project-files/manager/common-controller-block.md`, not yet published). Once that exists, it becomes one sheet of the LED Board P r-next candidate.

- Source: [`window_spec.py`](window_spec.py) (parts, pin tables, nets).
- Check: [`check_window.py`](check_window.py) runs a structural net check and reuses the V196 tolerance model unchanged ([`../board-p-v196-unadopted/analysis/failoff_window.py`](../board-p-v196-unadopted/analysis/failoff_window.py)).
- Output: [`window_check.json`](window_check.json).

## What the window does: OFF unless RAW is in 14.0-16.49 V and the STUSB4500 enables the sink

Starting point: the V196 window (TPS3701 undervoltage monitor + TPS25947 eFuse UV/OV + QINH inhibit). Three changes:

1. **Inhibit source.** QINH is driven by the STUSB4500 VBUS_EN_SNK (pin 16, active-low HV open drain, owner pin map) instead of the HUSB238 GATE. The polarity is the same:
   - VBUS_EN_SNK released: RG/RB pull the QINH base high, so EN/UVLO is held low (OFF).
   - VBUS_EN_SNK sinking: QINH is off and the UV divider plus the TPS3701 decide.
2. **RMH2 is 187 k** (V196 option O3).
3. **SMAJ20A input TVS on RAW_VBUS.** V196 had no input TVS.

| Event | Cutting path | Result at L2 (0.1 % + TCR + soldering + endurance) |
| --- | --- | --- |
| No contract, startup, STUSB unpowered or unprogrammed with VBEN released | QINH holds EN low | OFF |
| 15 V-only NVM, source without 15 V (5 V mismatch contract, VBEN Hi-Z) | QINH | OFF |
| Factory or lost NVM: VBEN asserted on a 5 V contract | U2 UV + TPS3701 | OFF (5 V << 12.755 V) |
| Factory or lost NVM: 20 V contract | U2 OVLO, rising 16.485-17.948 V | OFF; U2 IN 20 V stays inside the 2.7-23 V operating range |
| Renegotiation or fallback to 12 V (<= 12.6 V) while VBEN is still asserted | TPS3701 INA, OFF guaranteed <= 12.755 V | OFF, margin +0.155 V |
| 15 V contract, RAW >= 14.0 V | all released | ON (rising band 12.851-13.999 V) |
| OV trip, then back to 15.0 V | U2 OV falling minimum 14.992 V | Recovery at nominal 15.0 V is not guaranteed (carried from V196) |
| Contract lost while VBUS stays at 15 V | VBEN release only | **Unbounded**: STUSB4500 release timing is not specified. Residual |

## Evidence: TI pin numbers and limits re-checked against the hashed V196 sources

| Source | SHA-256 | Used |
| --- | --- | --- |
| TI TPS3701 SBVS240C | `27c94a6c…7d9560` (same bytes as V196 SOURCES.json) | Pin Functions table: 1 OUTA, 2 GND, 3 INA, 4 INB, 5 VDD, 6 OUTB; thresholds in failoff_window.py |
| TI TPS25947 SLVSFC9C (May 2026) | `8f96de38…8a65b4` (same bytes) | Table 5-1 pins 1-10 as in `PINS`; TPS259474LRPW = latch-off; ILIM table at exact RILM values: 3.32 k gives 0.850/1.007/1.150 A, 1.65 k gives 1.800/2.028/2.200 A; RILM range 549-6650 Ohm; abs max VIN 28 V |
| onsemi MMBT3904LT1/D Rev 15 (Sep 2026) | `5bae32c4…b579a4d7` | SOT-23 style 6: 1 B, 2 E, 3 C; ICEX 50 nA max at TA 25 °C only |
| STUSB4500 owner bundle `pin-map.json` | in repo | pin 16 VBUS_EN_SNK active-low HV open drain; 9 DISCH; 11 ATTACH; 20 POWER_OK2 |
| SMAJ20A owner bundle `component-high-diode-smaj20a-c571370` | in repo | VRWM 20 V, VC 32.4 V max at 12.3 A |

Structural check: every IC pin is either connected or listed as NC, no node sits on two nets, and every node names a known part and pin. A mutation test (dropping UMON.4, and wiring NC pin U2.3) was caught.

## Interface to the common block and Board L

| Net | Connects to |
| --- | --- |
| RAW_VBUS | VBUS after the common-block input protection, on the STUSB4500 VDD side |
| VBUS_EN_SNK_N | STUSB4500 pin 16 |
| SWITCHED_OUTPUT | JOUT1.1/.2; also to STUSB4500 DISCH (pin 9) through the common block's discharge resistor. That resistor must follow requirement R1.1: no RESET copper under or near it |
| GND | JOUT1.5/.6 |

- **ATT/PDOK** (STUSB4500 pins 11/20) pass straight to JOUT1.3/.4 and are not part of this sheet. JOUT1 is the existing PZ254V-11-06P with the existing pin map, so the 2 assembled Board Ls are reused unchanged.
- **Q1 (AO3401A) and its R11/R12/C35 gate network are replaced by U2.**

## Open items

| Item | Class |
| --- | --- |
| RILM: LED option 3.32 k (TI tabulated point, 0.85-1.15 A, above the Board L F1 0.75 A hold) versus V196's 1.27 k for a 3 A contract (an interpolated value, not a tabulated point). The tabulated band does not include resistor tolerance | user decision (tied to R2.2, PDO2 3 A) |
| LCSC codes for RMH2 RT0603BRD07187KL and RILM 0603WAF3321T5E not verified (LCSC returned 403 earlier; not bypassed) | access/evidence gap |
| QINH leakage: datasheet bound is 25 °C only; the 1 µA hot value stays an assumption | technical uncertainty |
| SMAJ20A VC 32.4 V exceeds the U2 abs max of 28 V and the STUSB4500 VDD abs max of 28 V at rated surge. Hot-plug ringing is not modelled | technical uncertainty; owned by the common block (R1.4) |
| DVDT 22 nF gives ~165 ms ramp (V196); Board L AP63203 slow-ramp startup is not guaranteed in retained evidence | evidence gap (V196 R9) |
| Placement relative to the STUSB4500 RESET keep-out, thermal design and a land review: none started | technical uncertainty |
