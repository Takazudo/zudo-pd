# Design gaps for any 20 V input option

**Status: analysis and documentation only. Nothing here is adopted.** No schematic, PCB, BOM, NVM or part selection changes. Every schematic and PCB stays an unvalidated draft. Each "candidate" below is a direction to study, not a selection.

This list collects the gates that block adoption under **every** 20 V option (C1 20 V / 3 A, C2 20 V / 5 A, and the two-SKU high model). The input-contract decision does not close any of them. Sources:
- [`b1-gates.md`](b1-gates.md), rows R3, R4a–R4c, R6/TVS and R7;
- [`product-lineup.md`](product-lineup.md), "Behavior gates common to every option";
- the OSC integration reviews PWR-INT-03 and PWR-INT-05 (zudo-osc-hole-field#288, record in PR #289), which own demand and acceptance limits.

Status words: **OPEN** means no candidate has been screened to a result. **UNRESOLVED** means a candidate exists but its screen is incomplete. **NOT RUN** means the check needs simulation or measurement that does not exist.

## Gap register

| ID | Gate | Requirement (not relaxed) | Current state | Status |
|---|---|---|---|---|
| GAP-1 | Input clamp vs STUSB4500 28 V absolute maximum | Every VBUS-side pin stays ≤ 28 V over the surge envelope and temperature | TVS2200 clamp 28.0 V (40 A, 27 °C) / 28.35 V (35 A, 125 °C), G: margin 0.00 / −0.35 V. Per-pin 470 Ω + BZX84-C24 candidate gives about 0.6–1.4 V hot at the table points | **UNRESOLVED** |
| GAP-2 | CC pins vs 22 V absolute maximum | A CC-to-VBUS short at 20 V must not exceed 22 V on CC1/CC2 | 2 V nominal margin; no protection screened | **OPEN** |
| GAP-3 | Source voltage bands | 12.00–12.30 / 12.00–12.20 / 5.05–5.10 V at the source terminals, including setpoint, temperature, load step and ripple | Internal TPS54560 reference FAILS on every rail. Terminal sense plus a precision DC servo is the candidate; its load-step, drift and −12 V level-shift terms are UNAV | **UNRESOLVED** |
| GAP-4 | Rail plus return loss | Board B adds no drop outside regulation (OSC already uses 0.162–0.194 V of 0.2 V) | PTC outside the loop costs 0.04–0.20 V and is inadmissible. Feedback after the PTC is the candidate; stability and trip behavior not screened | **UNRESOLVED** |
| GAP-5 | Output current limiting | Interface maximum 2.1 / 2.0 / 0.5 A enforced, tripping all rails | PTC trip about 5 A. No retrieved limiter holds a 0.1 A window; no −12 V high-side eFuse retrieved | **OPEN** |
| GAP-6 | Simultaneous all-rail shutdown | Detach, hard reset, charger swap, 5 A→3 A downgrade or any rail fault turns all rails off together, never a sag; restart only on a fresh full-class contract | Candidate: Board B input UVLO plus a common enable for all three stages. VBUS_EN_SNK timing on hard reset and re-contract is not stated by ST | **OPEN** (bench check needed) |
| GAP-7 | Reverse blocking | No reverse current from OSC rails or bulk into Board B or the source | Not addressed by any screened candidate | **OPEN** |
| GAP-8 | Ripple and noise | < 1 mVpp at load on every rail, plus the OSC 2 mV / 1 mV noise gates | Arithmetic fundamental 0.02–0.05 mVpp (CCM). Edges, ESL, +5 V DCM and pulse skipping not screened | **NOT RUN** |
| GAP-9 | Insufficient-source indication | All rails off with a visible "insufficient source" state | Indicator must sit on Board P, fed from VBUS_IN; ATT asserted and PDOK not asserted. POWER_OK latches after detach | **OPEN** |
| GAP-10 | NVM programming in production | Every unit carries the intended PDO set and refuse policy | Per-unit NVM write plus readback is required; no retained NVM image | **OPEN** |

GAP-1 to GAP-8 are the blocking items listed by the integration review. GAP-9 and GAP-10 come from the product-lineup screen.

## How each gap could close

| ID | Next analysis (no design change) | Needs a decision | Needs simulation or bench |
|---|---|---|---|
| GAP-1 | Define a surge envelope (waveform, energy, cable inductance); screen an input OVP or surge-stopper and the alternative controllers (CYPD3177 30 V, AP33772S 34 V) | PD-003-D3 controller choice | Surge test |
| GAP-2 | Retrieve CC protection parts rated above 22 V and confirm PD signaling compatibility | — | Short test |
| GAP-3 | Close the UNAV servo terms with retrieved limits; define the step amplitude and edge rate with OSC | PD-003-D5 | Loop stability, load step |
| GAP-4 | Screen terminal-sense stability with the OSC load capacitance (120–180 µF / 80–120 µF) | PD-003-D5 | Loop stability |
| GAP-5 | Search per-rail limiters, including −12 V, with a guaranteed window inside 2.0–2.1 A; otherwise ask OSC whether a wider interface maximum is acceptable (OSC decides) | OSC interface limit | Trip test |
| GAP-6 | Draft the enable chain and its timing against ST's documented behavior | PD-003-D4 | Detach, hard reset and downgrade tests |
| GAP-7 | Screen ideal-diode or series-switch candidates per rail, including their drop against GAP-4 | PD-003-D4 | Back-feed test |
| GAP-8 | Add ESL, DCM and pulse-skip screens; agree the measurement bandwidth with OSC | — | Ripple and noise measurement |
| GAP-9 | Draft the indicator logic from ATT, PDOK and VBUS_IN | PD-003-D4 | Bench check |
| GAP-10 | Define the NVM image and readback procedure | PD-003-D1 | Programming bench check |

None of these steps changes a schematic, PCB or part selection until the owner approves it.
