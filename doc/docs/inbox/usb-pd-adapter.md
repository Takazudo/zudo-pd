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

This power supply uses the **CH224D** USB-PD controller to negotiate **15V** from the adapter. The CH224D is configured to request specifically 15V PDO (Power Data Object).

**Power Budget Calculation:**

| Output Rail      | Current | Power     |
| ---------------- | ------- | --------- |
| +12V             | 1.2A    | 14.4W     |
| -12V             | 0.8A    | 9.6W      |
| +5V              | 0.5A    | 2.5W      |
| **Total Output** | -       | **26.5W** |

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

### Recommended Multi-Port Chargers

#### For 2 zudo-PD Units

| Brand      | Model                                                                                           | Power | Ports               | Simultaneous Output | Price |
| ---------- | ----------------------------------------------------------------------------------------------- | ----- | ------------------- | ------------------- | ----- |
| **Anker**  | [Prime 200W (A2683)](https://www.anker.com/products/a2683-anker-prime-charger-200w-6-ports-gan) | 200W  | 4× USB-C            | 100W + 100W ✅      | ~$90  |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger)  | 200W  | 4× USB-C + 2× USB-A | 100W + 100W ✅      | ~$100 |
| **UGREEN** | [Nexode 100W](https://www.amazon.com/UGREEN-100W-USB-Multiport-Charger/dp/B091Z6JNX4)           | 100W  | 3× USB-C + 1× USB-A | 65W + 30W ⚠️        | ~$60  |

**Best Choice for 2 units:** **Anker Prime 200W** - Well documented, proven 100W + 100W simultaneous output on two USB-C ports.

#### For 3 zudo-PD Units

| Brand      | Model                                                                                           | Power | Ports               | Notes                            |
| ---------- | ----------------------------------------------------------------------------------------------- | ----- | ------------------- | -------------------------------- |
| **Anker**  | [Prime 250W](https://www.anker.com/products/a2345-anker-prime-charger-250w-6-ports-ganprime)    | 250W  | 4× USB-C + 2× USB-A | Maximum headroom                 |
| **Anker**  | [Prime 200W (A2683)](https://www.anker.com/products/a2683-anker-prime-charger-200w-6-ports-gan) | 200W  | 4× USB-C            | 200W ÷ 3 = 66W each (sufficient) |
| **UGREEN** | [Nexode 200W Desktop](https://us.ugreen.com/products/ugreen-nexode-200w-usb-c-desktop-charger)  | 200W  | 6 ports             | Likely sufficient for 3 units    |

**Note:** Verify each port maintains 15V when 3 devices are connected. Anker provides detailed power distribution specs via QR code in the manual.

### Verification Checklist

Before purchasing a multi-port charger for multi-case setup:

- [ ] Total wattage ≥ (number of units × 45W)
- [ ] Supports 15V PDO on multiple ports simultaneously
- [ ] Check reviews for multi-device usage scenarios
- [ ] Verify power distribution when all ports are used (check manual or QR code specs)

### Alternative: Separate Adapters (Not Recommended)

If you must use separate adapters:

1. **Do not connect patch cables between cases** - This creates ground loops
2. Keep each system completely isolated
3. Use separate audio interfaces/mixers for each system

Using a single multi-port charger is the recommended approach for multi-case modular synth setups.
