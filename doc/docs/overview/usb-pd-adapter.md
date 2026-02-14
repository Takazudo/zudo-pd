---
sidebar_position: 3
---

# USB-PD AC Adapter

This page describes the USB-PD AC adapter requirements for the Zudo Power USB-PD power supply module.

## Required Specifications

| Specification     | Requirement               |
| ----------------- | ------------------------- |
| **Connector**     | USB Type-C                |
| **Protocol**      | USB Power Delivery (PD)   |
| **Required PDO**  | **15V / 3A** (45W at 15V) |
| **Minimum Power** | 45W                       |
| **Recommended**   | 65W or higher             |

### Why 15V / 3A?

This power supply uses the **STUSB4500** USB-PD controller to negotiate **15V** from the adapter. The STUSB4500 is configured via NVM to request specifically 15V PDO (Power Data Object).

**Power Budget Calculation:**

| Output Rail      | Current | Power     |
| ---------------- | ------- | --------- |
| +12V             | 1.5A    | 18W       |
| -12V             | 1.0A    | 12W       |
| +5V              | 1.5A    | 7.5W      |
| **Total Output** | -       | **37.5W** |

Accounting for conversion efficiency (~75-80%), the input power required is approximately **35-40W**. A 45W adapter (15V/3A) meets this requirement with some margin.

## Important Considerations

### 1. Must Support 15V PDO

**Critical:** The adapter must explicitly support **15V** in its PDO profile.

Some cheaper adapters only support:

- 5V / 9V / 20V (skipping 15V)

Always verify the product specifications list **15V** as a supported voltage.

### 2. Single Port Usage (For Single zudo-PD)

When using multi-port adapters with a **single** zudo-PD unit, power is typically split between ports. For reliable operation:

- Use single USB-C port for full power delivery
- If using multi-port, ensure the port supports 45W+ when used alone

**Note:** For **multi-case setups** with multiple zudo-PD units, using a single high-wattage multi-port charger is actually recommended. See [Multi-Case Setup](#multi-case-setup-multiple-zudo-pd-units) below.

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

## Recommended Products (Amazon Japan)

### Top Recommendations

| Brand      | Model             | Power | 15V Support | Ports               | Price Range |
| ---------- | ----------------- | ----- | ----------- | ------------------- | ----------- |
| **Anker**  | Nano II 65W       | 65W   | 15V/3A      | 1x USB-C            | ~4,000      |
| **Anker**  | Nano II 45W       | 45W   | 15V/3A      | 1x USB-C            | ~3,000      |
| **UGREEN** | Nexode 65W        | 65W   | 15V/3A      | 2x USB-C + 1x USB-A | ~4,500      |
| **BESTEK** | G651CA1           | 65W   | 15V/3A      | 1x USB-C + 1x USB-A | ~3,000      |
| **Belkin** | WCH013dq          | 65W   | 15V         | 2x USB-C            | ~5,000      |
| **CIO**    | NovaPort SLIM 45W | 45W   | 15V         | 2x USB-C            | ~4,000      |

### Product Links

1. **[Anker Nano II 65W](https://www.amazon.co.jp/dp/B08X11GD52)** - Best overall choice
- Compact design with GaN II technology
- Proven reliability
- Output: 5V/3A, 9V/3A, 15V/3A, 20V/3.25A

2. **[Anker Nano II 45W](https://www.amazon.co.jp/dp/B08X1M3JN9)** - Minimum spec, most compact
- Smallest form factor
- PPS support
- Output: 5V/3A, 9V/3A, 15V/3A, 20V/2.25A

3. **[UGREEN Nexode 65W](https://www.amazon.co.jp/dp/B091BGMKYS)** - Best value with multiple ports
- 3 ports for versatility
- GaN II technology
- PD3.0 and PPS support

4. **[BESTEK G651CA1 65W](https://www.amazon.co.jp/dp/B0C36GJJY5)** - Budget option
- Explicitly lists 15V/3A support
- Compact design (~102g)

5. **[Belkin WCH013dq 65W](https://www.amazon.co.jp/dp/B0B5QKMCZD)** - Premium option
- Trusted brand
- 5V/9V/12V/15V/20V support
- Dual USB-C ports

6. **[CIO NovaPort SLIM 45W](https://www.amazon.co.jp/dp/B0C42L9H78)** - Ultra-thin design
- Only 13mm thick
- Dual USB-C ports

## Verification Before Purchase

Before purchasing, check the product page for:

1. **PDO List** - Should include 15V (e.g., "5V/9V/15V/20V")
2. **Power at 15V** - Should be at least 3A (45W)
3. **Safety Certification** - PSE mark for Japan
4. **Reviews** - Check for stability issues

## USB-PD Controller Compatibility with Multi-Port GaN Chargers

### Known Issue: High-Wattage Multi-Port Chargers May Not Work

**Important Discovery:** Some high-wattage multi-port GaN chargers may have compatibility issues with simple PD sink controllers. The v1.1 design uses STUSB4500 which has significantly better charger compatibility (~95%+) compared to the v1.0 CH224D design (~33%).

#### Confirmed Working

| Charger               | Model | Power | Ports    | Status             |
| --------------------- | ----- | ----- | -------- | ------------------ |
| **Anker Nano II 65W** | A2663 | 65W   | 1× USB-C | ✅ Works perfectly |

#### Confirmed NOT Working

| Charger              | Model        | Power | Ports               | Status            |
| -------------------- | ------------ | ----- | ------------------- | ----------------- |
| **Anker Prime 200W** | A2683        | 200W  | 4× USB-C + 2× USB-A | ❌ All ports fail |
| **Elecom**           | EC-AC67150BK | 150W  | 3× USB-C + 1× USB-A | ❌ All ports fail |

### Why This Happens

Simple PD sink controllers may have limited negotiation capabilities compared to the **sophisticated software PD stacks** in laptops and tablets. Multi-port GaN chargers with intelligent power management expect active, responsive PD sinks.

#### Comparison: Simple vs Advanced PD Controllers

| Aspect               | PC / iPad                             | Simple PD Sink (e.g., CH224D) | STUSB4500 (v1.1)         |
| -------------------- | ------------------------------------- | ----------------------------- | ------------------------ |
| **PD Controller**    | Full software stack with dedicated IC | Simple hardware-only sink IC  | USB-IF certified sink IC |
| **Negotiation**      | Active, bi-directional communication  | Passive, one-shot request     | Active with retry logic  |
| **Retries**          | Multiple retry attempts with backoff  | Limited or no retry logic     | Built-in retry mechanism |
| **Timing Tolerance** | Flexible, handles delays              | Strict timing requirements    | Flexible timing          |
| **Re-negotiation**   | Handles dynamic PDO changes           | May fail on PDO updates       | Handles re-negotiation   |
| **Error Recovery**   | Sophisticated error handling          | Falls back to 5V or fails     | Built-in error recovery  |

The STUSB4500 used in v1.1 addresses most of these issues with USB-IF certification and built-in retry logic.

### Root Causes

#### 1. Dynamic Power Management Interference

Multi-port chargers constantly redistribute power as devices connect/disconnect. Features like:

- **Anker PowerIQ / ActiveShield** - Proprietary device detection
- **Dynamic PDO re-advertisement** - Changes available power in real-time
- **Intelligent power sharing** - May confuse simple sink controllers

#### 2. Non-Standard Timing

Some high-wattage chargers:

- Output 0V initially until specific conditions are met
- Have longer negotiation sequences
- Use stricter CC line detection than USB PD specification requires

#### 3. Missing 5V PDO (Some Chargers)

Some chargers violate USB PD specification by not including 5V as PDO1:

- USB PD spec requires 5V as the first PDO
- When CH224D receives Source_Capabilities starting at 9V, negotiation fails
- Device falls back to pre-PD 5V default (insufficient for zudo-PD)

### Symptoms When Charger Is Incompatible

When connecting zudo-PD to an incompatible charger:

1. Only the -12V LED briefly flickers
2. All LEDs turn off
3. No output voltage on any rail

**Explanation:** With only 5V input (failed negotiation), the DC-DC converters cannot produce proper voltages. The ICL7660 voltage inverter briefly attempts to invert whatever voltage exists, causing the -12V LED to flicker momentarily.

### Recommendations

#### For Best Compatibility

| Charger Type                     | Compatibility                |
| -------------------------------- | ---------------------------- |
| **Single-port PD chargers**      | ✅ Best - Simple negotiation |
| **Laptop chargers (65W-100W)**   | ✅ Usually works             |
| **Multi-port chargers &lt;100W** | ⚠️ Test before relying on    |
| **Multi-port GaN &gt;100W**      | ❌ Often fails               |

#### Recommended Approach

1. **Use a dedicated single-port charger** for zudo-PD
2. **Test before purchasing** - If possible, test with your specific charger before committing to a setup
3. **Avoid high-wattage multi-port GaN chargers** unless confirmed working

### Multi-Case Setup Caveat

The [Multi-Case Setup](#multi-case-setup-multiple-zudo-pd-units) section recommends multi-port chargers for ground loop elimination. However, due to potential compatibility issues:

- **Preferred:** Use confirmed-working chargers (like Anker Nano II series)
- **Alternative:** Accept separate adapters with proper ground management
- **Testing required:** Always test multi-port chargers before relying on them for live performance

### STUSB4500 Improves Compatibility (v1.1)

The v1.1 design uses the **STUSB4500** USB-IF certified controller, which significantly improves charger compatibility (~95%+) compared to the v1.0 CH224D design (~33%). The STUSB4500 includes built-in retry logic and error recovery that resolves most compatibility issues with modern GaN chargers.

---

## Troubleshooting

### Adapter Not Working

If the power supply doesn't work with your adapter:

1. **Check PDO support** - Adapter may not support 15V
2. **Check cable** - Use a USB-C cable rated for 3A or higher
3. **Check port** - Some multi-port adapters reduce power on certain ports

### LED Not Lighting

If LED2 (power indicator) doesn't light:

1. Verify adapter is connected and powered
2. Try a different USB-C cable
3. Verify adapter supports 15V PDO

## Multi-Case Setup (Multiple zudo-PD Units)

When you need more power for a larger modular synth system, you can power multiple zudo-PD units from a single multi-port USB-PD charger. This approach has significant benefits over using separate AC adapters.

### Why Use a Single Multi-Port Charger?

**Ground Loop Elimination:**

When using separate AC adapters for each case, connecting modules via patch cables creates ground loops:

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

Each zudo-PD unit requires approximately **40W at 15V** (15V × 2.5A with some margin).

| Setup   | Power Required | Minimum Charger |
| ------- | -------------- | --------------- |
| 2 units | ~80W           | 100W charger    |
| 3 units | ~120W          | 150W charger    |
| 4 units | ~160W          | 200W charger    |

### Important Considerations

1. **15V must be maintained on all ports** - Some chargers drop to 9V when power is split
2. **Check simultaneous output specs** - Not just total wattage, but per-port when multiple ports are used
3. **USB Hubs don't work** - Regular USB hubs only provide 5V, not USB-PD

### ⚠️ Critical Compatibility Warning

**The multi-port chargers listed below have NOT been tested with zudo-PD.** Based on our testing (see [USB-PD Controller Compatibility](#usb-pd-controller-compatibility-with-multi-port-gan-chargers)), high-wattage multi-port GaN chargers often fail to work with the CH224D controller (v1.0 design). The STUSB4500 (v1.1) improves this significantly.

**Confirmed NOT working:**

- Anker Prime 200W (A2683) - ❌ All ports fail
- Elecom EC-AC67150BK (150W) - ❌ All ports fail

**Before purchasing any multi-port charger for multi-case setup:**

1. Check if the specific model has been tested with CH224D-based devices
2. Consider using multiple single-port chargers instead (with ground loop mitigation)
3. Test before relying on for live performance

### Multi-Port Chargers (Untested - Use at Your Own Risk)

The following chargers have sufficient power specifications but **have not been verified** to work with zudo-PD:

#### For 2 zudo-PD Units

| Brand      | Model                                                                                          | Power | Ports               | Simultaneous Output | Compatibility            |
| ---------- | ---------------------------------------------------------------------------------------------- | ----- | ------------------- | ------------------- | ------------------------ |
| **Anker**  | [Prime 200W (A2683)](https://www.amazon.co.jp/dp/B0D3GG4M9N)                                   | 200W  | 4× USB-C            | 100W + 100W         | ❌ Confirmed NOT working |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger) | 200W  | 4× USB-C + 2× USB-A | 100W + 100W         | ❓ Untested              |
| **UGREEN** | [Nexode 100W](https://www.amazon.com/UGREEN-100W-USB-Multiport-Charger/dp/B091Z6JNX4)          | 100W  | 3× USB-C + 1× USB-A | 65W + 30W           | ❓ Untested              |

#### For 3 zudo-PD Units

| Brand      | Model                                                                                          | Power | Ports               | Compatibility            |
| ---------- | ---------------------------------------------------------------------------------------------- | ----- | ------------------- | ------------------------ |
| **Anker**  | [Prime 250W](https://www.anker.com/products/a2345-anker-prime-charger-250w-6-ports-ganprime)   | 250W  | 4× USB-C + 2× USB-A | ❓ Untested              |
| **Anker**  | [Prime 200W (A2683)](https://www.amazon.co.jp/dp/B0D3GG4M9N)                                   | 200W  | 4× USB-C            | ❌ Confirmed NOT working |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger) | 200W  | 6 ports             | ❓ Untested              |

**Note:** If you find a multi-port charger that works with zudo-PD, please report it so we can update this list.

### Verification Checklist

Before purchasing a multi-port charger for multi-case setup:

- [ ] Total wattage ≥ (number of units × 45W)
- [ ] Supports 15V PDO on multiple ports simultaneously
- [ ] Check reviews for multi-device usage scenarios
- [ ] Verify power distribution when all ports are used (check manual or QR code specs)

### Alternative: Separate Single-Port Adapters

Given the compatibility issues with multi-port GaN chargers, using separate single-port adapters may be more reliable:

**Pros:**

- ✅ Confirmed working (Anker Nano II 65W tested)
- ✅ Simple, predictable PD negotiation
- ✅ Each unit has dedicated power

**Cons:**

- ⚠️ Potential ground loops when connecting patch cables between cases
- ⚠️ More wall outlets needed

**Ground Loop Mitigation (if using separate adapters):**

1. **Use balanced audio connections** where possible
2. **Ground lift on one case** (if your synth supports it)
3. **Use the same power strip** for all adapters (shared AC ground)
4. **Avoid connecting patch cables** between separately-powered cases during performance
