---
title: v3 USB-PD Failure Diagnosis (pin 18 root cause)
sidebar_position: 10
---

Why the v3 board still fails to negotiate USB-PD even after (a) the STUSB4500 NVM was
correctly reprogrammed (`SNK_PDO_NUMB=2`, 15 V/3 A) and (b) pin 18 was bodged.

**Method:** every claim below was verified by reading the actual net topology in
`usb-pd-input.kicad_sch` against U1's own symbol pin table (symbol origin `176.53,63.5`,
**not mirrored**; absolute pin = `176.53+dx, 63.5−dy`). A first multi-agent pass produced
several **false** findings from guessing pin numbers by screen position; those are listed in
"Ruled out" so nobody chases them.

## Authoritative U1 (STUSB4500QTR) pin map — verified

| Pin | Name | Abs (x,y) | Connects to | Verdict |
| --- | --- | --- | --- | --- |
| 1 | CC1DB | 156.21,49.53 | → R19 (0 Ω) → GND, isolated from CC1 | ok |
| 2 | CC1 | 156.21,52.07 | CC1 net (D4, R17 5.1k→GND, J1.A5) | ok |
| 3 | NC | 156.21,54.61 | no_connect | ok |
| 4 | CC2 | 156.21,57.15 | CC2 net (D4, R18 5.1k→GND, J1.B5) | ok |
| 5 | CC2DB | 156.21,59.69 | → R20 (0 Ω) → GND, isolated from CC2 | ok |
| 6 | RESET | 156.21,62.23 | → `RST` → GND (active-low idle = run) | ok |
| 7 | SCL | 156.21,64.77 | → `SCL-pin1` (R15 4.7k pull-up, J2) | ok |
| 8 | SDA | 156.21,67.31 | → `SDA-pin2` (R16 4.7k pull-up, J2) | ok |
| 9 | DISCH | 156.21,69.85 | (internal discharge) | check |
| 10 | GND | 156.21,72.39 | → wire to GND | ok |
| 11 | ATTACH | 156.21,74.93 | → `ATT` label | ok |
| 12 | ADDR0 | 156.21,77.47 | → GND (#PWR043) | ok (addr strap) |
| 13 | ADDR1 | 196.85,77.47 | → GND | ok (addr strap) |
| 14 | POWER_OK3 | 196.85,74.93 | label / NC | ok |
| 15 | GPIO | 196.85,72.39 | label | ok |
| 16 | VBUS_EN_SNK | 196.85,69.85 | → `VBEN` → Q1 gate | ok |
| 17 | A_B_SIDE | 196.85,67.31 | label / NC | ok |
| **18** | **VBUS_VS_DISCH** | **196.85,64.77** | **→ R14 (470 Ω) → GND. NO VBUS.** | **BUG (blocker)** |
| 19 | ALERT | 196.85,62.23 | label / NC | ok |
| 20 | POWER_OK2 | 196.85,59.69 | → `POWER_OK2` label | ok |
| 21 | VREG_1V2 | 196.85,57.15 | → **C34 (1µF) decap** to GND | ok |
| 22 | VSYS | 196.85,54.61 | → GND (#PWR047) — hard tie | ok (correct for VBUS-powered) |
| 23 | VREG_2V7 | 196.85,52.07 | → `VREG_2V7` rail + **C30 (1µF) decap** | ok |
| 24 | VDD | 196.85,49.53 | → `VDD` global label | ok (powered) |
| 25 | EP | (center) | GND | ok |

ADDR0=GND, ADDR1=GND ⇒ I2C address **0x28** (matches what the programmer saw — consistent).

## ROOT CAUSE (blocker): pin 18 VBUS_VS_DISCH tied to GND

Verified net of pin 18 = `{ U1.18, the VBUS_VS_DISCH label, R14.1, TP6 }`, and **R14's other
end goes to a GND symbol** (`#PWR046` at 236.22,76.2). The net **never touches VBUS anywhere**
(confirmed: no VBUS_IN / VBUS_OUT node on it).

```
pin18 ──┬── VBUS_VS_DISCH label ── TP6
        └── R14 (470 Ω) ── GND        ← WRONG: should reach VBUS, not GND
```

**Why this kills negotiation:** VBUS_VS_DISCH is the high-voltage analog input the STUSB4500
uses to confirm VBUS is in a valid window before it asserts VBUS_EN_SNK (the load-switch
enable). Held at 0 V, the chip believes VBUS is permanently absent → never enables the sink
path → no contract. This is why "NVM correct + pin 18 bodged, still dead": the bodge restored
a *connection*, but to **GND**, so the sense input is still grounded. Even a perfect respin of
the current schematic would still fail.

> **Datasheet note (why GND looked plausible):** ST DS12499 calls pin 18 VBUS_VS_**DISCH** —
> it doubles as a VBUS discharge path (≤50 mA, hence a series R). That dual name is what led
> the original design (and our earlier docs) to tie it toward GND. But its **primary** job is
> VBUS *voltage sensing*, so the pin-18 network's far end must reach the **VBUS rail**, not
> ground. The v1-debug doc said exactly this ("pin 18 → 470 Ω → VBUS_IN").

### The fix (schematic)

Pin 18 needs to see VBUS through a series/divider, not a pull to GND. Two options:

- **Simplest (matches v1-debug intent):** make R14 the series element to VBUS:
  `VBUS_IN → R14 (470 Ω) → pin 18`. Delete the R14→GND wire + `#PWR046`.
- **Safer divider (recommended):** `VBUS_IN → R_top (≈470 kΩ) → pin 18 → R14 (470 Ω) → GND`,
  so the pin sees a small, current-limited fraction of VBUS. Keep TP6 on the pin-18 node.

Confirm the exact recommended topology/value against the ST datasheet Fig. 10 and the SparkFun
Power Delivery Board before committing — see the open question below.

### Fastest bench bodge to PROVE it (minutes, before any respin)

1. Lift R14's GND end (or remove R14).
2. Wire **VBUS_IN** (Q1 source / J1 VBUS / a VBUS test point) **→ ~470 kΩ → pin 18 (or TP6)**,
   and refit R14 (470 Ω) from pin 18 → GND. Net: `VBUS_IN → 470k → pin18 → 470Ω → GND`.
3. Re-plug USB-C. **DMM TP6:** was ~0 V (broken) → now non-zero, rising with VBUS (pass).
   Watch VBEN (pin 16) assert and the +12/+5/−12 rails come up.

If that single bodge brings PD up, pin 18 was the whole story.

## Secondary items — all verified OK (no action)

- **VSYS (pin 22):** hard-tied to GND (#PWR047) — correct for a VBUS-powered (non-battery)
  design. (Earlier audit's "floating, missing decap" was wrong.)
- **VREG_2V7 (pin 23):** decoupled by **C30 (1 µF)**. OK. Bench: ≈ 2.7 V when powered.
- **VREG_1V2 (pin 21):** decoupled by **C34 (1 µF)**. OK. Bench: ≈ 1.2 V when powered.
- **DISCH (pin 9):** confirm intended connection per datasheet (minor, not a blocker).

**Conclusion: pin 18 → GND is the _only_ confirmed bug. The rest of the front end is correct.**

## Ruled out — do NOT chase (false findings from position-guessing)

- **"VDD (pin 24) shorted to GND"** — FALSE. Pin 24 carries the `VDD` global label. The GND
  the agent saw was on **pin 13 ADDR1**, a correct address strap.
- **"ADDR0→CC1DB / ADDR1→VDD mis-wired"** — FALSE. Both ADDR pins go to GND (addr 0x28).
- **"RESET tied to GND is wrong"** — FALSE. Active-low idle; held low = normal run.
- **"SCL shorted to RESET/GND"** — FALSE. SCL/SDA route correctly to their labels + pull-ups.
- **"Pin 10 GND / pins floating"** — FALSE. Every U1 pin has a wire; pin 10 reaches GND.
- **Q1 load switch** — schematic OK (source→VBUS_IN, drain→VBUS_OUT, gate via VBEN). Worth a
  PCB continuity spot-check but not the blocker.

## Open question for you

R14's far end should go to **VBUS** — but VBUS_IN or VBUS_OUT? VBUS_IN = raw USB-C VBUS
(present before the load switch); VBUS_OUT = after Q1. For *sink* VBUS validity sensing you
generally want the **receptacle-side VBUS (VBUS_IN)**, which is also what the v1-debug doc
specified. Recommend VBUS_IN unless the datasheet Fig. 10 says otherwise. Want me to fetch the
datasheet figure and the SparkFun reference to lock down the exact value + which VBUS node, and
then apply the schematic edit for you?
