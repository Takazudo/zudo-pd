# Isolated hardware candidates — NOT ADOPTED

Directories here hold isolated design candidates imported from outside Git history
for review. They are not canonical hardware: `boards/` and
`manufacturing/` remain the source of truth for what was ordered. Nothing here is
validated, qualified, released, or order-ready, and no fabrication output may be
generated from it without a separate explicit approval.

## Current path: P15 r1 + the two existing Board Ls

**Decision 2026-11-03 (owner):** the LED lamp's current Board P is the zudo-pd
**P15 r1**, shared with the 15 V zudo-pd product, mated with the **two existing Board Ls**
from the 2026-09-19 order. LED-first. The Board Ls already exist; P15 is not ordered, programmed or
measured yet.

| Item | Current value | Where it lives |
| --- | --- | --- |
| Board P | zudo-pd `boards/board-p15/` r1, 27 × 40 mm, same outline, holes and JOUT1 as the ordered LED Board P | Adopted at zudo-pd commit `4a0741fabf8d2332848a3740708aab26b8504133` (now on zudo-pd `main`). Consumer reference: [`boards/p15-r1-reference.json`](../boards/p15-r1-reference.json), checked by `python3 scripts/checks/verify-p15-reference.py --pd-repo <zudo-pd checkout>` (byte identity only) |
| NVM image | `boards/board-p15/nvm/stusb4500-15v.bin`: 2 PDOs, PDO1 5 V / 1.5 A, PDO2 15 V / **3 A**, POWER_ONLY_ABOVE_5V = 1. Same image for LED and zudo-pd | SHA256 `76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb` at that commit. Desk image: never written or read back |
| Board L | The two existing boards, unchanged: RS1 = 200 mΩ as built, MCU believed blank | `boards/board-l/`, `manufacturing/jlcpcb/2026-09-19/` |
| Firmware | `firmware/board-l/target/` with `CTRL_FULL_CCR` = 2407 (the 200 mΩ ceiling) | Not flashed. See [`firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md`](../firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md) |
| Bench sheets | Boot, NTC, knob, CTRL, option bytes, temperature | [`firmware/board-l/BENCH-TEST-SHEETS.md`](../firmware/board-l/BENCH-TEST-SHEETS.md), all NOT EXECUTED |

Accepted residuals and mandatory steps (they are not passes):

- P15 has no NVM-independent voltage window or eFuse. Requirement rows R2.3, R2.4 and
  R2.6 are **FAIL** and R2.5 is **UNKNOWN**; the owner accepted this as a prototype-stage
  residual. The adoption does not turn them into passes.
- Every P15 unit must have its NVM written and accepted (P15-NVM-4/5 on a 5 V-only source,
  then P15-NVM-6 on a PD test source with no load) before it ever mates with a Board L.
  The procedure is owned by zudo-pd (`doc/src/content/docs/architecture/board-p15-programming.md`).
- Keep `CTRL_FULL_CCR` = 2407 while RS1 = 200 mΩ. The [#52 analysis](board-l-led-margin-52/ANALYSIS.md)
  hot-branch numbers (88.6 / 96.9 mA at full CTRL) and the 250 mΩ rework numbers
  (72.5 / 79.1 mA) are sensitivity cases, not measured values or guaranteed limits. Do not
  rework RS1 or move to 3200 as an assumed next step.

Enclosure fit in CAD (2026-11-03, P15P): `enclosure/generate.py` at `cfc8cb4`, run in an isolated
copy with `boards/board-p/board-p.kicad_pcb` replaced by the zudo-pd P15 r1 PCB (sha256 `97acc5f4…`)
and its 3D models, KiCad 10.0.6 pinned image, exit 0. All generator assertions and `check_stack` pass,
every printed part clears every P15 and Board L STEP body (0.0 mm³), and the USB corridor is open.
Tracked enclosure outputs were not regenerated. Nominal datums only; print and seating fit are unmeasured.
Use the [LED prototype-order handoff](../manufacturing/README.md) for the pinned owner decision packet,
exact three upload files, supporting exclusions and remaining checkout checks. For LED, 2 P15 are new,
the 2 Board Ls are reused, and no new Board B is ordered.

These are **not** blockers for the current path: the PDO2 1.5 A vs 3 A question (settled:
3 A), the 27 × 44 / 27 × 50 outline question, and the old Board P #144 diagnosis. They
belong to the future candidates below.

## Future candidates (not on the current path)

| Directory | Candidate | State |
| --- | --- | --- |
| [`board-p-v196-unadopted/`](board-p-v196-unadopted/PROVENANCE.md) | HUSB238_006DD 15 V-only shared Board P, V196 routed PCB | FUTURE CANDIDATE. UNADOPTED; native DRC exit 5 (22 known findings), not DRC PASS |
| [`board-p-v198-unadopted/`](board-p-v198-unadopted/PROVENANCE.md) | V196 + PCB/schematic field sync, J1 bound to USB4105-GF-A / C3020560 | FUTURE CANDIDATE. UNADOPTED; same 22 DRC findings (exit 5), not DRC PASS |
| [`board-p-v199-pending-user-decision/`](board-p-v199-pending-user-decision/PROVENANCE.md) | V198 + recommended options as separable changes: RMH2 187k, COUT Datasheet sync, J1 GND 0.025 mm trim, SMAJ20A input TVS | FUTURE CANDIDATE (its options are no longer pending for the current path). UNADOPTED scratch; same 22 DRC findings with default rules (exit 5); 0 with the unapplied base rules in a scratch copy only |
| [`board-p-rnext-stusb-unadopted/`](board-p-rnext-stusb-unadopted/README.md) | LED Board P r-next schematic: zudo-pd common STUSB4500 block @3ac13d46 + LED voltage window after Q1 + JOUT1; option pair PDO2 1.5 A / RILM 3.32 k or 3 A / 1.27 k (candidate-only question) | **FUTURE CANDIDATE** (deferred 2026-11-03; its PDO2 and outline options are not current blockers). UNADOPTED schematic draft; native netlist matches spec, ERC 0 errors / 13 pin-type warnings; 9 candidate owner bundles; land check; 27 × 40 mm placement study (no routing); area options (C3 / J3 / back side / outline) compared, J3 test-pad array adopted in candidate; no PCB |
| [`board-p-stusb-window-subcircuit/`](board-p-stusb-window-subcircuit/README.md) | LED Board P r-next voltage window (TPS3701 + TPS25947 + QINH driven by STUSB4500 VBUS_EN_SNK, RMH2 187 k, SMAJ20A input TVS) as a standalone sub-circuit | FUTURE CANDIDATE. UNADOPTED desk source; structural check + V196 arithmetic only; awaits the common STUSB4500 block |
| [`board-p-stusb4500-144-root-cause/`](board-p-stusb4500-144-root-cause/ANALYSIS.md) | Issue #144 desk root-cause ranking for the ordered STUSB4500 Board P and rules for the common controller block | Desk analysis only; nothing measured or changed. Not a prerequisite for the current path |
| [`board-l-led-margin-52/`](board-l-led-margin-52/ANALYSIS.md) | Issue #52 LED peak-current desk analysis: RS1 options vs firmware CTRL ceiling | UNADOPTED proposal; recommends RS1 = 250 mΩ (RLP25FEER250, LCSC unverified); no hardware changed. The current path keeps 200 mΩ with `CTRL_FULL_CCR` 2407 |
| [`FIRMWARE-V72-INVENTORY.md`](FIRMWARE-V72-INVENTORY.md) | Board L V72 portable C firmware, imported to [`firmware/board-l/`](../firmware/board-l/README.md) | Imported; the target skeleton in `firmware/board-l/target/` links it. Not flashed |

The KiCad project directories sit two levels below the repository root on purpose:
their library footprints resolve 3D models via
`${KIPRJMOD}/../../footprints/kicad/zudo-led-lamp.3dshapes/`.
