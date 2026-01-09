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

### 2. Single Port Usage Recommended

When using multi-port adapters, power is typically split between ports. For reliable operation:

- Use single USB-C port for full power delivery
- If using multi-port, ensure the port supports 45W+ when used alone

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
