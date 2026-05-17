---
sidebar_position: 6
---

# PCBA v2 Debug Report — STUSB4500 CC1DB Failure

Debug analysis of the second PCBA prototype (v2) for the USB-PD modular synthesizer power supply. The STUSB4500 was successfully programmed via NVM, but the chip's **CC1DB pin is internally shorted to GND on every assembled board**, preventing USB-C source detection and blocking PD negotiation entirely. This page documents the failure mode, diagnostic sequence, root cause analysis, and the v3 design fix.

## Symptoms

After PCBA v2 was assembled by JLCPCB and the STUSB4500 NVM was successfully programmed:

| Observation | Detail |
| --- | --- |
| Charger plugged in | **0V on USB-C VBUS pin at the connector itself** |
| STUSB4500 detected on I2C | ✅ Yes — chip responds at address 0x28, NVM read/write works |
| NVM written with target PDOs | ✅ Yes — `SNK_PDO_NUMB = 2`, PDO2 = 15V/3A confirmed via read-back |
| GUI "Dashboard" tab | **"No device attached"** — chip sees nothing on its CC pins |
| Multimeter at D4 (ESD diode) | **CC1 net = 0 Ω to GND** (shorted), CC2 net = 5.1 kΩ to GND (correct) |
| Both PCBAs (2 boards from same JLCPCB order) | **Identical fault** |

## Root Cause

**The STUSB4500's CC1DB pin (pin 1) is internally shorted to GND.**

CC1DB provides "dead battery mode" termination — a passive 5.1 kΩ Rd pulldown that the USB-C source detects in order to apply VBUS. Since CC1DB is internally shorted to 0 Ω instead of presenting 5.1 kΩ Rd, the source sees an invalid CC termination and refuses to enable VBUS.

The v2 schematic correctly ties **CC1DB → CC1 net** (the standard ST-recommended dead-battery wiring). With the chip's internal short, this wiring drags the entire CC1 net to GND.

## Diagnostic Sequence That Isolated the Fault

### Step 1: GUI Dashboard ruled out NVM and software

The STSW-STUSB002 GUI's Dashboard tab showed **"No device attached"** even with a USB-C cable plugged into a working PD charger. NVM-level settings cannot influence the chip's hardware CC detection — this proved the issue was at the physical CC pin level, not software.

### Step 2: Multimeter measurements at D4 (USBLC6-2SC6)

D4 sits between the USB-C connector and the STUSB4500 on both CC lines. With board unpowered:

| Probe | Reading | Conclusion |
| --- | --- | --- |
| D4 pin 1 (J1-CC1 side) to GND | **0 Ω** | CC1 net shorted to GND |
| D4 pin 6 (U1-CC1 side) to GND | **0 Ω** | Confirms short propagates through diode (D4 passes signal correctly) |
| D4 pin 3 (J1-CC2 side) to GND | **5.1 kΩ** | CC2 net correctly terminated |
| D4 pin 4 (U1-CC2 side) to GND | **5.1 kΩ** | CC2 chip-internal Rd works |
| D4 pin 1 to D4 pin 6 (across diode) | **0 Ω** | Diode passes signal — D4 is healthy |

The asymmetry (CC1 shorted, CC2 fine) ruled out a generic short and pointed to a chip-side issue at pin 1 (CC1DB).

### Step 3: Hot-air removal of U1 isolated the source

To definitively localize the short to the chip or the PCB:

1. Applied flux + hot air to U1 (STUSB4500), removed the chip
2. With chip off, measured pad 1 (CC1DB position on the empty footprint) to GND: **OPEN circuit**
3. PCB pads were visually clean — no solder bridges remained under the chip area

**Conclusion**: the chip was the source of the short. The PCB itself has no design or assembly defect on the CC1 net.

### Step 4: Both PCBAs show identical fault

Two boards from the same JLCPCB order exhibited the exact same CC1DB short with the exact same chip placement orientation. This rules out:

- ❌ Random ESD damage (would affect chips randomly)
- ❌ Single-chip manufacturing defect
- ❌ Initial 20V overvoltage during testing (the second board was always programmed with a 5V-only charger first — confirmed by sequence of operations)

## What We Ruled Out Through Investigation

| Hypothesis | Status | How |
| --- | --- | --- |
| Wrong USB-C cable | Ruled out | Multiple cables tested |
| Wrong charger | Ruled out | Multiple chargers (all with 15V/3A support) tested |
| Chip damaged from initial 20V exposure | Ruled out | Second PCBA never saw 20V — same fault |
| Schematic error | Ruled out | Wiring matches SparkFun reference + ST datasheet typical app |
| USB-C connector footprint wrong | Ruled out | 6-pin SMD USB-C correctly maps B5 to CC2 internally |
| D4 (USBLC6) ESD diode dead | Ruled out | 0 Ω across pin 1↔6 confirms diode passes |
| CC1 trace touching GND on PCB | Ruled out | DRC clean on all layers; net visually clean in KiCad layout |
| STUSB4500 chip rotation wrong | Ruled out | I2C works on pins 7/8 → pin numbering is mapped correctly |
| NVM corruption | Ruled out | NVM read/write works; Dashboard says "No device attached" which is hardware-level |
| Footprint pad mapping wrong in PCB | Ruled out | PCB net assignments confirmed (pin 1 → Net-(U1-CC1), pin 6 → GND, etc.) |
| Counterfeit chip | Likely but unconfirmed | Both chips from same LCSC batch (C2678061) |

## Why v2 Design Is Vulnerable

The v2 schematic ties **CC1DB ↔ CC1** and **CC2DB ↔ CC2** — the standard ST-recommended dead-battery mode wiring used by:

- **SparkFun Power Delivery Board** ([schematic](https://cdn.sparkfun.com/assets/9/2/6/8/6/SparkFun_PowerDeliveryBoardSchematic.pdf))
- **ST STEVAL-ISC005V1** evaluation board
- **STUSB4500 datasheet "typical application" (Figure 10)**

This design relies **entirely on the chip's internal Rd** for CC termination. There's no external fallback. If any chip ships with internally-damaged CC1DB or CC2DB pins, **the entire board is bricked** with no rework option short of chip replacement.

## ST Datasheet Reference

Per the STUSB4500 datasheet (DS12499 Rev 5), pin description for CC1DB / CC2DB (page 4, Table 1):

> Pin 1 CC1DB: "Dead battery enable on CC1 pin" — Typical connection: **"To CC1 pin if used or ground"**
>
> Pin 5 CC2DB: "Dead battery enable on CC2 pin" — Typical connection: **"To CC2 pin if used or ground"**

And from §2.2.2 (page 5):

> "CC1DB and CC2DB are used for dead battery mode. This mode is enabled by connecting CC1DB and CC2DB respectively to CC1 and CC2. Thanks to this connection, the pull-down terminations on the CC pins are present by default even if the device is not supplied."
>
> ⚠️ **Warning: "CC1DB and CC2DB must be connected to ground when dead battery mode is not supported."**

**Both wiring options — "to CC1/CC2" (dead-battery) and "to ground" (no dead-battery) — are explicitly ST-supported.** The v3 fix uses the second option.

## v3 Design Fix

### Topology change

```
v2 (vulnerable):                          v3 (robust):

USB-C CC1 ─┬─ D4 ─ STUSB4500 pin 2 (CC1)  USB-C CC1 ─┬─ D4 ─ STUSB4500 pin 2 (CC1)
           │                                          │
           └─────── STUSB4500 pin 1 (CC1DB)           R_CC1 (10 kΩ)    ← NEW
                                                      │
                                                     GND

                                          STUSB4500 pin 1 (CC1DB) ─── GND   ← CHANGED

(symmetric for CC2)                       (symmetric for CC2)
```

### Schematic changes

| Change | Detail |
| --- | --- |
| **Add R_CC1 = 10 kΩ (0603, 1%)** | From CC1 net (USB-C connector side) to GND |
| **Add R_CC2 = 10 kΩ (0603, 1%)** | From CC2 net (USB-C connector side) to GND |
| **Disconnect U1 pin 1 (CC1DB) from CC1 net** | Tie pin 1 directly to GND |
| **Disconnect U1 pin 5 (CC2DB) from CC2 net** | Tie pin 5 directly to GND |

### Why 10 kΩ and not 5.1 kΩ?

Two CC termination scenarios coexist with external + internal Rd:

| Scenario | Effective Rd | USB-C spec window: 4.08–6.12 kΩ |
| --- | --- | --- |
| Chip's internal Rd healthy (5.1 kΩ) + ext 5.1 kΩ in parallel | **2.55 kΩ** | ❌ Below spec — risk of misdetection as Ra |
| Chip's internal Rd healthy (5.1 kΩ) + ext 10 kΩ in parallel | **3.4 kΩ** | ⚠️ Slightly below spec — most sources tolerate |
| Chip's internal Rd broken (0 Ω → isolated via CC1DB→GND) + ext 10 kΩ alone | **10 kΩ** | ⚠️ Slightly above spec — most sources tolerate |

**10 kΩ is the working compromise.** This value is also confirmed by an existing working JLCPCB-built design ([DIY Smart Hotplate on Instructables](https://www.instructables.com/DIY-Smart-Hotplate-Powered-by-STM32-USB-C-Power-De/)).

5.1 kΩ would be USB-PD-spec textbook value but produces 2.55 kΩ parallel — outside the spec window.

### Why disconnect CC1DB / CC2DB from CC1 / CC2?

**This is the critical change.** If CC1DB stays on the CC1 net (v2 wiring), then a chip with internally-shorted CC1DB still drags the entire CC1 net to 0 Ω, and the external 10 kΩ is overpowered. The fault persists.

By routing CC1DB and CC2DB to GND directly:
- The broken pin's internal short is isolated to the GND net (harmless)
- The CC1 / CC2 nets see only the external R_CC1 / R_CC2 and the chip's main CC pins (pin 2, pin 4) for termination

### What we give up: Dead-battery mode

In v3, the chip cannot present passive Rd before being powered. The chicken-and-egg is solved by the external R_CC1 / R_CC2 — these are always present and always provide valid Rd, so the source detects the sink, applies 5V VBUS, which powers the chip via VDD, which then takes over CC handling actively.

Dead-battery mode is only needed when the chip is being powered from a separate depleted battery and needs to advertise itself before that battery recovers. **For VBUS-only powered designs like zudo-pd, dead-battery mode provides no benefit and creates the single-point-of-failure we hit.**

## Additional v3 Improvements (Recommended)

### EPAD F.Paste aperture (footprint fix)

The current QFN-24 footprint defines pad 25 (the EPAD) with a single solid 2.8 × 2.8 mm F.Paste aperture. Standard QFN best practice is to **window the EPAD paste** into a grid of smaller apertures (e.g., 4×4 sub-squares of ~0.5 × 0.5 mm each, ~50-60% area coverage). This:

- Controls solder paste volume on the EPAD
- Prevents excess solder from squeezing out at the EPAD corners during reflow
- Reduces risk of solder bridging to corner pins (CC1DB is at one corner, RESET at the opposite corner)
- Is JLCPCB-recommended for thermal pad SMT assembly

### EPAD GND vias (footprint fix)

The current EPAD has 16 GND vias in a 4×4 grid. Standard QFN recommendation is **4–9 vias** for thermal/electrical GND connection. Excessive vias can wick solder away from the joint during reflow, contributing to solder migration and uneven joint quality.

**Recommendation**: Reduce to a 3×3 grid (9 vias) or 5 vias (4 corners + center). Use solder-mask plug on via-in-pad to prevent paste loss.

### External Rd resistor placement

Place R_CC1 and R_CC2 **physically close to the USB-C connector**, before D4. This ensures the source's first measurement (at first cable plug) sees the external Rd directly, even if D4 or downstream traces have issues.

## v3 Schematic Fix Checklist

- [ ] Add R_CC1 (10 kΩ, 0603, 1%) from USB-C CC1 to GND
- [ ] Add R_CC2 (10 kΩ, 0603, 1%) from USB-C CC2 to GND
- [ ] Disconnect U1 pin 1 (CC1DB) from CC1 net; tie to GND
- [ ] Disconnect U1 pin 5 (CC2DB) from CC2 net; tie to GND
- [ ] Update QFN-24 footprint: window the EPAD F.Paste into a 4×4 grid of 0.5 mm² apertures
- [ ] Update QFN-24 footprint: reduce EPAD GND vias from 16 to 9 (or 5)
- [ ] Add via tenting / mask-plug on EPAD via-in-pad
- [ ] Run DRC and ERC
- [ ] Bench test on first v3 board: cold-plug a USB-C source, confirm VBUS appears (proves external Rd bootstrap works)

## Reference Designs Compared

| Design | CC1DB wiring | External Rd on CC | Notes |
| --- | --- | --- | --- |
| **zudo-pd v2** (current) | CC1DB ↔ CC1 (dead-battery) | None | ❌ Fails when chip ships with CC1DB internally shorted |
| **SparkFun Power Delivery Board** | CC1DB ↔ CC1 (dead-battery) | None | Standard ST design; works when chips are good |
| **ST STEVAL-ISC005V1** | CC1DB ↔ CC1 (dead-battery) | None | ST's own eval design; works with controlled chip sourcing |
| **STUSB4500 datasheet Fig. 10** | CC1DB ↔ CC1 (dead-battery) | None | "Typical application" — same vulnerability |
| **Instructables DIY Hotplate** | CC1DB ↔ CC1 (dead-battery) | R3 = 10 kΩ on CC1 only | Confirmed working JLCPCB build; asymmetric ext Rd |
| **zudo-pd v3** (planned) | CC1DB → GND, CC2DB → GND | **10 kΩ on both CC1 and CC2** | Defensive against chip-side failures; symmetric |

## References

- [STUSB4500 Datasheet DS12499 Rev 5](https://www.st.com/resource/en/datasheet/stusb4500.pdf) — pages 4, 5, 14, 23, 25, 26 referenced
- [STUSB4500L Datasheet](https://www.st.com/resource/en/datasheet/stusb4500l.pdf) — variant with similar CC pin scheme
- [STEVAL-ISC005V1 Schematic Pack](https://www.st.com/resource/en/schematic_pack/steval-isc005v1_schematic.pdf) — ST eval board reference
- [STEVAL-ISC005V1 User Manual UM2547](https://www.st.com/resource/en/user_manual/dm00493783-getting-started-with-the-stevalisc005v1-evaluation-board-for-stusb4500-stmicroelectronics.pdf)
- [SparkFun Power Delivery Board Schematic (PDF)](https://cdn.sparkfun.com/assets/9/2/6/8/6/SparkFun_PowerDeliveryBoardSchematic.pdf)
- [SparkFun Power Delivery Board product page](https://www.sparkfun.com/products/15801)
- [DIY Smart Hotplate (Instructables)](https://www.instructables.com/DIY-Smart-Hotplate-Powered-by-STM32-USB-C-Power-De/) — working JLCPCB design with 10 kΩ external Rd on CC1
- [GitHub: usb-c/STUSB4500](https://github.com/usb-c/STUSB4500) — official ST reference code
- [USB Type-C 2.0 Specification](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-22) — Rd termination requirements (§4.11.2)
- [PCBA v1 Debug Report](/docs/inbox/pcba-v1-debug) — v1 issues (different failure mode: pin 18 and pin 22 wiring)
- [NVM Programming Setup](/docs/inbox/nvm-programming) — how to program the chip via STSW-STUSB002 GUI
