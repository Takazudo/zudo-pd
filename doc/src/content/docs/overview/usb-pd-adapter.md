---
title: USB-PD AC Adapter
sidebar_position: 6
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

USB-PD AC adapter requirements for zudo-pd. The adapter plugs into
**[Board A](./board-a-usb-pd-core.md)**, the USB-PD sink core, which negotiates 15 V and
hands the switched rail to [Board B](./board-b-synth-power.md).

<Warning title="No adapter has ever been proven to work with this design">

Across four JLCPCB PCBA orders (0.1.0 → 0.4.0) **no board has ever completed a USB-PD
negotiation with any adapter** — see the
[failure history](../inbox/current-status.md#failure-history-v1-→-v4) and
[v4 USB-PD Failure Diagnosis](../inbox/v4-pd-failure-diagnosis.md). Everything below is a
**requirement and a shortlist**, not a compatibility report. Nothing on this page has
been validated against working hardware.

</Warning>

## Required Specifications

| Specification     | Requirement                |
| ----------------- | -------------------------- |
| **Connector**     | USB Type-C                 |
| **Protocol**      | USB Power Delivery (PD)    |
| **Required PDO**  | **15V / 3A** (45W at 15V)  |
| **Minimum Power** | 45W                        |
| **Recommended**   | 65W or higher              |

### Why 15V / 3A?

Board A uses the **STUSB4500** USB-PD sink controller, NVM-configured to request the 15 V
PDO (Power Data Object).

**Power Budget Calculation:**

| Output Rail      | Current | Power      |
| ---------------- | ------- | ---------- |
| +12V             | 1.2A    | 14.4W      |
| -12V             | 0.8A    | 9.6W       |
| +5V              | 0.5A    | 2.5W       |
| **Total Output** | -       | **26.5W**  |

At the design-target conversion efficiency (~75-80%, itself unmeasured), the input draw
is roughly **33-35 W** — about **2.2-2.4 A at 15 V**. A 45 W adapter (15 V/3 A) therefore
covers the full budget with headroom for inrush and the DC-DC stage's startup behavior.

## Important Considerations

### 1. Must Support 15V PDO

**Critical:** The adapter must explicitly support **15V** in its PDO profile.

Some cheaper adapters only support:

- 5V / 9V / 20V (skipping 15V)

Always verify the product specifications list **15V** as a supported voltage.

<Note title="Program the NVM before plugging into a 20 V-capable source">

A factory-default (unprogrammed) STUSB4500 advertises PDO3 = 20 V/1 A at highest
priority. On an assembled-but-unprogrammed Board A, a 20 V contract overdrives the Q1
gate-source path — which is why decision (e) added the D8 zener clamp. Program the NVM
before first attach anyway; see [NVM Programming Setup](../inbox/nvm-programming.md).

</Note>

### 2. Single Port Usage (For Single zudo-PD)

When using multi-port adapters with a **single** zudo-PD unit, power is typically split
between ports. For reliable operation:

- Use a single USB-C port for full power delivery
- If using multi-port, ensure the port supports 45W+ when used alone

**Note:** For **multi-case setups** with multiple zudo-PD units, using a single
high-wattage multi-port charger is what removes ground loops. See
[Multi-Case Setup](#multi-case-setup-multiple-zudo-pd-units) below.

### 3. GaN Technology Recommended

GaN (Gallium Nitride) adapters offer:

- Smaller size
- Higher efficiency
- Lower heat generation
- Better reliability

### 4. Avoid No-Brand Adapters

Cheap no-brand adapters may:

- Have unstable voltage output
- Skip 15V PDO entirely
- Lack proper safety certifications (PSE in Japan)

## Candidate Products (Amazon Japan)

These are **shortlisted on published specs only**. None has been confirmed against a
working board, for the reason in the warning at the top of this page.

| Brand      | Model             | Power | 15V Support | Ports               | Price Range |
| ---------- | ----------------- | ----- | ----------- | ------------------- | ----------- |
| **Anker**  | Nano II 65W       | 65W   | 15V/3A      | 1x USB-C            | ~4,000      |
| **Anker**  | Nano II 45W       | 45W   | 15V/3A      | 1x USB-C            | ~3,000      |
| **UGREEN** | Nexode 65W        | 65W   | 15V/3A      | 2x USB-C + 1x USB-A | ~4,500      |
| **BESTEK** | G651CA1           | 65W   | 15V/3A      | 1x USB-C + 1x USB-A | ~3,000      |
| **Belkin** | WCH013dq          | 65W   | 15V         | 2x USB-C            | ~5,000      |
| **CIO**    | NovaPort SLIM 45W | 45W   | 15V         | 2x USB-C            | ~4,000      |

### Product Links

1. **[Anker Nano II 65W](https://www.amazon.co.jp/dp/B08X11GD52)** — single-port, ample margin
- Compact design with GaN II technology
- Output: 5V/3A, 9V/3A, 15V/3A, 20V/3.25A

2. **[Anker Nano II 45W](https://www.amazon.co.jp/dp/B08X1M3JN9)** — minimum spec, most compact
- Smallest form factor
- PPS support
- Output: 5V/3A, 9V/3A, 15V/3A, 20V/2.25A

3. **[UGREEN Nexode 65W](https://www.amazon.co.jp/dp/B091BGMKYS)** — multiple ports
- 3 ports for versatility
- GaN II technology
- PD3.0 and PPS support

4. **[BESTEK G651CA1 65W](https://www.amazon.co.jp/dp/B0C36GJJY5)** — budget option
- Explicitly lists 15V/3A support
- Compact design (~102g)

5. **[Belkin WCH013dq 65W](https://www.amazon.co.jp/dp/B0B5QKMCZD)** — premium option
- 5V/9V/12V/15V/20V support
- Dual USB-C ports

6. **[CIO NovaPort SLIM 45W](https://www.amazon.co.jp/dp/B0C42L9H78)** — ultra-thin design
- Only 13mm thick
- Dual USB-C ports

## Verification Before Purchase

Before purchasing, check the product page for:

1. **PDO List** - Should include 15V (e.g., "5V/9V/15V/20V")
2. **Power at 15V** - Should be at least 3A (45W)
3. **Safety Certification** - PSE mark for Japan
4. **Reviews** - Check for stability issues

## Charger Compatibility: What Is and Is Not Known

### The observations

Bench attempts across the PCBA orders produced these results:

| Charger                              | Model        | Power | Ports               | Result           |
| ------------------------------------ | ------------ | ----- | ------------------- | ---------------- |
| **Anker Nano II 65W**                | A2663        | 65W   | 1× USB-C            | No 15V contract  |
| **Anker Prime 200W**                 | A2683        | 200W  | 4× USB-C + 2× USB-A | No 15V contract  |
| **Elecom**                           | EC-AC67150BK | 150W  | 3× USB-C + 1× USB-A | No 15V contract  |

<Danger title="This table does not rank chargers">

An earlier revision of this page listed the Anker Nano II 65W as "✅ Works perfectly" and
blamed the two multi-port units for the failures. That reading does not survive the
record: **every** order failed, including with the single-port charger, so the failures
are not evidence about the chargers at all. They are all consistent with the board-side
front-end defects catalogued in
[v4 USB-PD Failure Diagnosis](../inbox/v4-pd-failure-diagnosis.md). Until Board A
negotiates 15 V with at least one adapter, this project has **no** charger compatibility
data — good or bad.

</Danger>

### Why multi-port chargers are still the harder case

The hypothesis below is retained because it shapes what to test first once Board A works,
not because this project's bench results support it.

Simple PD sink controllers have narrower negotiation behavior than the software PD stacks
in laptops and tablets. Multi-port GaN chargers with intelligent power management assume
an active, responsive sink:

- **Dynamic power management** — multi-port chargers redistribute power as devices
  connect and disconnect, re-advertising PDOs in real time
- **Non-standard timing** — some high-wattage chargers hold VBUS at 0 V until specific
  conditions are met, or run longer negotiation sequences
- **Missing 5 V PDO** — a charger whose Source_Capabilities starts above 5 V violates the
  USB PD spec's PDO1 requirement and can strand a simple sink at the pre-PD 5 V default

The STUSB4500 was chosen partly because it is USB-IF certified and has built-in retry and
error recovery, which is the class of behavior these chargers demand.

<Note title="The old 95%-vs-33% compatibility figures are not evidence">

Earlier writing attached compatibility percentages to the STUSB4500 and to the CH224D
design that preceded it. Neither figure has a source retained in this project, and this
design has never demonstrated a successful negotiation, so neither number should be
quoted as a project result.

</Note>

### Symptoms of a failed negotiation

When the 15 V contract is never established (whatever the cause):

1. Only the -12V LED briefly flickers
2. All LEDs turn off
3. No output voltage on any rail

**Explanation:** With only 5 V present, the DC-DC converters cannot produce their target
voltages. The U4 inverting buck-boost (LM2596S-ADJ) briefly attempts to invert whatever
voltage exists, which is what flickers the -12V LED.

This is the signature the v1-v4 boards produced. Note it is a *sink-side* observation:
per the diagnosis page, a contract that forms and then collapses within a few hundred
milliseconds is indistinguishable from "no negotiation" on a DMM — only a scope on
VBUS_IN and CC separates them.

### Recommended approach

1. **Start with a dedicated single-port charger** — the simplest negotiation, and the
   smallest set of variables while Board A is under bring-up
2. **Test before relying on any charger**, particularly a high-wattage multi-port GaN unit
3. **Report what you find** — this project has no compatibility data to hand you, so a
   confirmed result is genuinely new information

---

## Troubleshooting

### Adapter Not Working

If the power supply doesn't work with your adapter:

1. **Check PDO support** - Adapter may not support 15V
2. **Check cable** - Use a USB-C cable rated for 3A or higher
3. **Check port** - Some multi-port adapters reduce power on certain ports
4. **Check the board** - Given the bring-up history, work through the
   [bench discrimination procedure](../inbox/v4-pd-failure-diagnosis.md#bench-discrimination-procedure-dead-v4-boards-cheapest-first)
   before concluding the adapter is at fault

### LED Not Lighting

The three rail indicators all live on Board B: **LED2** (green) on +12 V, **LED3** (blue)
on +5 V, **LED4** (red) on −12 V. All three dark means Board B never received 15 V, which
points at Board A's negotiation rather than at any single rail:

1. Verify adapter is connected and powered
2. Try a different USB-C cable
3. Verify adapter supports 15V PDO
4. Verify the J4 ↔ J5 interface cable is seated — Board B has no other power source

A *single* dark LED with the other two lit is the opposite situation: the 15 V contract
is fine and that one rail has tripped its PTC or lost its regulator.

## Multi-Case Setup (Multiple zudo-PD Units)

When you need more power for a larger modular synth system, you can power multiple
zudo-PD units from a single multi-port USB-PD charger. This approach has significant
benefits over using separate AC adapters.

### Why Use a Single Multi-Port Charger?

**Ground Loop Elimination:**

When using separate AC adapters for each case, connecting modules via patch cables
creates ground loops:

```
Separate Adapters (BAD):
┌─────────────────┐          ┌─────────────────┐
│   Adapter A     │          │   Adapter B     │
│   GND_A         │          │   GND_B         │
└────────┬────────┘          └────────┬────────┘
         │                            │
    ┌────┴────┐                  ┌────┴────┐
    │ Case A  │◄───patch cable───│ Case B  │
    └─────────┘   (has ground)   └─────────┘
         │                            │
         └─────── ground loop ────────┘
              ↑
         Potential 50/60Hz hum
```

**Single multi-port charger solves this:**

```
Single Multi-Port Adapter (GOOD):
┌─────────────────────────────┐
│  Multi-Port GaN Charger     │
│  (shared internal ground)   │
└──────┬─────────────┬────────┘
       │             │
   ┌───┴───┐     ┌───┴───┐
   │zudo-PD│     │zudo-PD│
   │ Case A│◄───►│ Case B│  ← Patch cables OK!
   └───────┘     └───────┘

No ground loop - both share same ground reference!
```

### Power Requirements

Each zudo-PD unit draws approximately **35 W at 15 V** (≈2.4 A) at its full rail budget —
but it negotiates a 15 V/3 A contract, so budget the charger against the **45 W
contract**, not the 35 W draw.

| Setup   | Contracted | Minimum Charger |
| ------- | ---------- | --------------- |
| 2 units | 90W        | 100W charger    |
| 3 units | 135W       | 150W charger    |
| 4 units | 180W       | 200W charger    |

### Important Considerations

1. **15V must be maintained on all ports** - Some chargers drop to 9V when power is split
2. **Check simultaneous output specs** - Not just total wattage, but per-port when
   multiple ports are used
3. **USB Hubs don't work** - Regular USB hubs only provide 5V, not USB-PD

### ⚠️ Nothing below is verified

**No multi-port charger has been shown to work with zudo-PD — and neither has any
single-port one.** See
[Charger Compatibility](#charger-compatibility-what-is-and-is-not-known) above. The
chargers listed here meet the wattage and PDO requirements on paper; that is all that can
be said about them today.

Before committing to a multi-port charger for a multi-case setup:

1. Confirm the published per-port specs hold 15 V when all ports are loaded
2. Consider multiple single-port chargers instead, with ground-loop mitigation
3. Test before relying on it for live performance

### Multi-Port Chargers (Unverified — Use at Your Own Risk)

These chargers have sufficient power specifications on paper but **have not been verified**
with zudo-PD:

#### For 2 zudo-PD Units

| Brand      | Model                                                                                          | Power | Ports               | Simultaneous Output | Status                  |
| ---------- | ---------------------------------------------------------------------------------------------- | ----- | ------------------- | ------------------- | ----------------------- |
| **Anker**  | [Prime 200W (A2683)](https://www.amazon.co.jp/dp/B0D3GG4M9N)                                   | 200W  | 4× USB-C            | 100W + 100W         | ❓ No contract on v1-v4 |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger) | 200W  | 4× USB-C + 2× USB-A | 100W + 100W         | ❓ Untested             |
| **UGREEN** | [Nexode 100W](https://www.amazon.com/UGREEN-100W-USB-Multiport-Charger/dp/B091Z6JNX4)          | 100W  | 3× USB-C + 1× USB-A | 65W + 30W           | ❓ Untested             |

#### For 3 zudo-PD Units

| Brand      | Model                                                                                          | Power | Ports               | Status                  |
| ---------- | ---------------------------------------------------------------------------------------------- | ----- | ------------------- | ----------------------- |
| **Anker**  | [Prime 250W](https://www.anker.com/products/a2345-anker-prime-charger-250w-6-ports-ganprime)   | 250W  | 4× USB-C + 2× USB-A | ❓ Untested             |
| **Anker**  | [Prime 200W (A2683)](https://www.amazon.co.jp/dp/B0D3GG4M9N)                                   | 200W  | 4× USB-C            | ❓ No contract on v1-v4 |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger) | 200W  | 6 ports             | ❓ Untested             |

**Note:** If you find a charger that negotiates 15 V with zudo-PD, please report it — it
would be the project's first working data point.

### Verification Checklist

Before purchasing a multi-port charger for multi-case setup:

- [ ] Total wattage ≥ (number of units × 45W)
- [ ] Supports 15V PDO on multiple ports simultaneously
- [ ] Check reviews for multi-device usage scenarios
- [ ] Verify power distribution when all ports are used (check manual or QR code specs)

### Alternative: Separate Single-Port Adapters

Separate single-port adapters trade the ground-loop benefit for the simplest possible
negotiation per unit:

**Pros:**

- ✅ Simplest, most predictable PD negotiation
- ✅ Each unit has dedicated power, no per-port sharing to reason about

**Cons:**

- ⚠️ Potential ground loops when connecting patch cables between cases
- ⚠️ More wall outlets needed

**Ground Loop Mitigation (if using separate adapters):**

1. **Use balanced audio connections** where possible
2. **Ground lift on one case** (if your synth supports it)
3. **Use the same power strip** for all adapters (shared AC ground)
4. **Avoid connecting patch cables** between separately-powered cases during performance
