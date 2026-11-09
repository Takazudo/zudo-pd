---
title: Release Readiness
sidebar_position: 4
---

This page owns **acceptance criteria**, not a running status ledger. Read [current state](../project/current-state.md)
for dated results, artifacts, order plans and received hardware. Development exports, CAD checks and publication
checks do not establish a product release or measured rating.

## P15 acceptance before either load

| Gate | Required evidence |
| --- | --- |
| Identity and incoming inspection | P15 r1 source/population/NVM identity; D5/D9 orientation, U1/J1 seating, no bridges |
| Provisioning | [P15-NVM-1–5 and P15-NVM-7](./board-p15-programming.md), current-limited 5 V-only source and both Board L and B disconnected; factory dump, write, immediate readback, full power cycle and configuration verification |
| Jig | External pull-ups, no VREG_2V7 loading, grounded RESET, no RESET pulse; canonical power sequencing and measured I/O levels/rise time |
| First PD attach | NVM-6 on a current-limited test source also offering 20 V, still no downstream boards; 15 V contract and output off at 5 V |
| Handover | Only an accepted module proceeds to LED first, then PD15; retain unit-specific results |

The absence of a hardware voltage window/eFuse is a recorded prototype residual, not proof of fault protection.

## PD15 qualification

| Gate | Required evidence |
| --- | --- |
| Received Board B identity | S3 factory BOM plus D1 inspection, copper/mask/paste/silk boundary, LED2 orientation and usable quantity; distinguish later development substitutions |
| Electrical rules and PCB | Exact part/pin-map parity, reviewed ERC/DRC/connectivity, converter loops, returns, copper/vias and conditioned stress limits |
| Power behavior | [Staged bring-up](../verification/renewal-bring-up.md): startup, low-line, load, ripple, thermal, surge and coupled operation at the target rail budgets |
| Mechanics | Front-down stack, unkeyed J5 alignment, wire/terminal/shroud clearance; printed-leg fit, M3 passage through Ø3.0 mm holes, retention and 116 × 91 mm footprint |
| Model evidence | Source-specific datum/clearance reports; sampled geometry does not establish physical fit |

## The selected power stage requires qualification

PD15's +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A are targets. Its
[power-stage material](./power-stage-options.md) describes the AP63201/LM2596/LT1963A/LT3015 design only.
Headroom calculations retain source/path voltage, temperature, ripple and ceramic-bank assumptions.

## PD20 qualification

| Gate | Required evidence |
| --- | --- |
| Input design | Disposition and independent verification of the completed P r3 review findings, exact component evidence, inrush/SOA and transient bounds |
| Configuration | TDISPAR0V value/reset timing decision, resolved POWER_ONLY_ABOVE_5V mapping conflict and established-contract downgrade behavior; reviewed program-ready binary before any T4 execution. Position 0xCA[7:4] and initial lower-current source matching are already documented |
| B20 review | Disposition of original review, retained SMC hot-loop/EMI and limiter-maximum D3/U3 thermal limits; component/pulse/DC-bias gaps |
| OSC pre-order interface | Complete actual startup/re-entry waveforms and model scope; 1.5 V analog threshold for the +5 V hold condition; adopted no-load exception ceilings; loaded asymmetric discharge and output disconnection before discharge; maximum delivered current including overshoot. A limiter trip threshold or windowed slew average is insufficient |
| Model and design decisions | Disposition unresolved numerical/model excursions without inventing a tolerance or excess-current budget; any ramp-down before disconnection, component substitution, lower current ceiling or acceptance of unresolved thermal margins needs an explicit decision |
| Other OSC behavior | Reverse leakage, all-rail fault latch and the remaining interface obligations retain their documented acceptance criteria and evidence limits |
| Physical evidence | All [T1–T8](../verification/pd20-verification.md), actual 5 A e-marked source/cable, assembled thermal and mechanical checks |

## Order gates

Each export needs one exact valid pair, final-revision Gerbers/drills/BOM/CPL, reviewed DNP/side/rotation/THT scope,
source locks, reports and named blockers. Use [package preparation](../project/jlcpcb-package.md).
An export is neither an executed order nor a release. Prototype residual acceptance does not waive product qualification.

The two-P15 local packet and the PD20 development pair have separate dispositions
in the [execution ledger](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/prototype-order-readiness.md).
P15 supplier placement preview and a current quotation remain owner steps;
incoming inspection and provisioning follow arrival. Unperformed first-prototype
arrival tests are not a circular prerequisite for ordering that settled P15
candidate. Conversely, PD20's explicitly pre-order interface obligations cannot
be reassigned to T1–T8 merely to make an order appear ready.

The P15 `corner-support-review` package is fixed at manifest base `3b9821b`; retain its historical full-verifier
and 151/151 checksum PASS with the original STEP. Current HEAD does not inherit that result. A historical replay
needs a tree matching its source hashes and the original required local-only STEP. Do not refresh the frozen locks.
