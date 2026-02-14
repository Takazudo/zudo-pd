---
sidebar_position: 7
---

# CH224D USB PD Sink Controller

Understanding the CH224D USB Power Delivery sink controller and how it negotiates voltage with PD adapters.

## What is CH224D?

CH224D is a **USB PD sink controller** - a specialized IC that:

- Communicates with USB-C PD (Power Delivery) adapters
- Requests specific voltages (5V, 9V, 12V, 15V, or 20V)
- Negotiates power up to 100W (with E-Mark simulation)
- Handles all PD protocol communication automatically

**Key advantage**: You don't need a microcontroller - just set a resistor value and the IC does everything!

## How USB Power Delivery Works

### Traditional USB Power (Without PD)

```
USB-A Port → Fixed 5V @ 0.5A-3A (max 15W)
```

Problem: Limited to 5V, insufficient for high-power devices.

### USB Power Delivery (With PD)

```
USB-C PD Adapter ← Negotiation via CC pins → Device (CH224D)
                     "I need 15V @ 3A"
                     "OK, switching to 15V"
VBUS: 5V → 15V (voltage changes on same wire!)

Result: Up to 100W power delivery (20V @ 5A)
```

### Critical Concept: VBUS is Both Input and Output

**This is the most important thing to understand:**

```
┌─────────────┐         VBUS          ┌─────────────┐
│   USB-C     │ ────────────────────→ │   CH224D    │
│ PD Adapter  │   5V (initial)        │  (pin 2)    │
│             │                       │             │
│             │ ← CC negotiation →    │             │
│             │                       │             │
│             │   15V (after PD)      │             │
│             │ ────────────────────→ │             │
└─────────────┘         VBUS          └─────────────┘
```

**CH224D does NOT have a separate output pin!**

- Pin 2 (VBUS) is the ONLY power pin
- Initially: VBUS = 5V (default USB voltage)
- After negotiation: VBUS = 15V (or requested voltage)
- Your circuit connects directly to VBUS

This is fundamentally different from DC-DC converters which have separate input and output pins!

## CH224D Pin Functions

### Power Pins

| Pin | Name       | Type      | Function                                                             |
| --- | ---------- | --------- | -------------------------------------------------------------------- |
| 2   | VBUS       | Power I/O | **Main power pin** - both input (5V) and output (negotiated voltage) |
| 7   | VDD        | Power out | Internal 4.7V LDO output (needs 1µF decoupling cap)                  |
| 0   | GND (EPAD) | Ground    | Thermal pad - connect to ground plane                                |

### Communication Pins (PD Protocol)

| Pin | Name     | Type | Function                                    |
| --- | -------- | ---- | ------------------------------------------- |
| 11  | CC1      | I/O  | Configuration Channel 1 - PD communication  |
| 10  | CC2      | I/O  | Configuration Channel 2 - PD communication  |
| 8   | DP (UDP) | I/O  | USB D+ data line (not used in PD-only mode) |
| 9   | DM (UDM) | I/O  | USB D- data line (not used in PD-only mode) |

**For PD-only applications**: Short DP (pin 8) to DM (pin 9) to disable BC1.2 and other USB data protocols.

### Configuration Pins

| Pin | Name | Type       | Function                                           |
| --- | ---- | ---------- | -------------------------------------------------- |
| 1   | DRV  | Analog out | Drives configuration resistor (weak output)        |
| 19  | CFG1 | Analog in  | Voltage selection input (resistor mode)            |
| 13  | CFG2 | Digital in | Voltage selection (level mode, built-in pull-down) |
| 12  | CFG3 | Digital in | Voltage selection (level mode, built-in pull-down) |

#### How DRV Pin Works (Voltage Selection Magic!)

**DRV (pin 1)** is a **weak voltage output** (~4.7V) used to determine which PD voltage you want.

**The clever voltage selection circuit:**

```
DRV (pin 1) ──┬── CFG1 (pin 19)  ← Connect DRV to CFG1
              │
            Rset (e.g., 56kΩ)
              │
             GND
```

**How it determines voltage:**

1. **DRV outputs ~4.7V** (weak current, can't power external circuits)
2. **Rset creates voltage divider** between DRV and GND
3. **Specific voltage appears at CFG1** (depends on Rset value)
4. **CH224D's internal ADC reads CFG1 voltage**
5. **Based on CFG1 voltage → requests specific PD voltage**

**Example with our 56kΩ resistor:**

```
DRV (4.7V) ─┬─ CFG1
            │
          56kΩ ← Creates specific voltage at CFG1
            │
           GND

CH224D reads CFG1 voltage → "Ah, user wants 15V!" → Requests 15V from PD adapter
```

**Different resistors → Different voltages:**

```
Rset = 6.8kΩ  → CFG1 = X volts → Request 9V
Rset = 24kΩ   → CFG1 = Y volts → Request 12V
Rset = 56kΩ   → CFG1 = Z volts → Request 15V ✅ (our design)
Rset = NC     → CFG1 = ~4.7V   → Request 20V
```

**Why "weak" output?**

- Can drive high-impedance loads (kΩ resistors) ✅
- Cannot drive LEDs, motors, or power circuits ❌
- Just for voltage sensing - perfect for this use!

**Simple and elegant:** No microcontroller needed - just one resistor tells CH224D what voltage you want!

### Power Switching Pins (Internal vs External MOSFET)

CH224D has a **built-in MOSFET** (rated up to 5A) to switch VBUS power on/off.

| Pin | Name  | Function                                         | Our Connection                          |
| --- | ----- | ------------------------------------------------ | --------------------------------------- |
| 5   | GATE  | Drives MOSFET gate (internal or external)        | **NC** (not connected - using internal) |
| 6   | NMOS# | Selects internal (LOW) or external (HIGH) MOSFET | **GND** (use internal MOSFET)           |

#### How It Works:

**For ≤5A applications (like ours at 3A):**

- Pin 6 (NMOS#) → **GND** = Use internal MOSFET
- Pin 5 (GATE) → **NC** (not connected)
- CH224D's internal 5A MOSFET handles the switching
- Simple and works great! ✅

**For >5A applications (e.g., 100W chargers):**

- Pin 6 (NMOS#) → Configured for external mode
- Pin 5 (GATE) → **Connected to external MOSFET gate**
- External high-current MOSFET handles the power
- CH224D controls the external MOSFET via GATE pin

**Why external MOSFET?** When you need more than 5A, you need a more powerful MOSFET that can handle the high current without overheating.

### Current Sensing Pins (Optional Feature)

| Pin | Name | Function               | Our Connection              |
| --- | ---- | ---------------------- | --------------------------- |
| 14  | ISP  | Current sense positive | **Shorted to pin 15 → GND** |
| 15  | ISN  | Current sense negative | **Shorted to pin 14 → GND** |

**What they do:**

- Can monitor current flowing through the power path
- Useful for overcurrent protection or current measurement
- Requires external sense resistor

**Why we don't use them:**

- CH224D provides built-in overcurrent protection
- Our design doesn't need current monitoring
- Simplifies the circuit

**Connection:** Short pins 14 and 15 together, then connect to GND.

### VDD Pin - Internal Regulator Output

**Pin 7 (VDD)** is the output of CH224D's internal 4.7V LDO regulator.

**Critical requirement:** VDD **MUST** have a 1µF decoupling capacitor to GND!

```
VDD (pin 7) → C30 (1µF ceramic) → GND
```

**Why C30 is critical:**

- ⚡ **Regulator stability** - LDO requires output cap to remain stable
- 🔇 **Noise filtering** - Filters high-frequency noise from internal circuits
- ⚡ **Transient response** - Provides instant current during load changes
- ✨ **Clean power** - Ensures accurate PD negotiation and voltage selection

**Without C30, the CH224D will not work correctly!** The internal regulator could oscillate, causing PD negotiation to fail.

**Note:** VDD powers only the IC's internal circuits (analog/digital logic). Your external circuits connect to VBUS (pin 2), not VDD.

### Unused Pins

| Pins            | Status                                                                 |
| --------------- | ---------------------------------------------------------------------- |
| 3, 4, 16-18, 20 | NC (Not Connected) - leave floating                                    |
| 18              | **NC** - No separate output pin! VBUS (pin 2) is both input and output |

## Voltage Selection Methods

CH224D supports two configuration methods:

### Method 1: Resistor Configuration (Used in This Project)

Simple and static - set once with a resistor value.

```
Circuit:
DRV (pin 1) ──┬── CFG1 (pin 19)
              │
            Rset
              │
             GND

Voltage Selection:
┌──────────┬──────────────────┐
│ Rset     │ Requested Voltage│
├──────────┼──────────────────┤
│ 6.8 kΩ   │ 9V               │
│ 24 kΩ    │ 12V              │
│ 56 kΩ    │ 15V ✅ (This)    │
│ NC       │ 20V              │
└──────────┴──────────────────┘

CFG2 (pin 13) = Open/GND
CFG3 (pin 12) = Open/GND
```

**Advantages**:

- ✅ Simple - just one resistor
- ✅ No microcontroller needed
- ✅ Voltage fixed at design time
- ✅ Low cost

**Our design uses 56kΩ → 15V**

### Method 2: Level Configuration

Dynamic - can change voltage with MCU or switches.

```
Circuit:
CFG1, CFG2, CFG3 connect to MCU GPIO or VDD/GND

Voltage Selection:
┌──────┬──────┬──────┬──────────────────┐
│ CFG1 │ CFG2 │ CFG3 │ Requested Voltage│
├──────┼──────┼──────┼──────────────────┤
│  1   │  -   │  -   │ 5V               │
│  0   │  0   │  0   │ 9V               │
│  0   │  0   │  1   │ 12V              │
│  0   │  1   │  1   │ 15V              │
│  0   │  1   │  0   │ 20V              │
└──────┴──────┴──────┴──────────────────┘

Note: CFG2 and CFG3 have built-in pull-down resistors
```

**Advantages**:

- ✅ Dynamic voltage selection
- ✅ Can change voltage during operation
- ✅ Multiple voltage outputs from same board

**Disadvantages**:

- ❌ Requires MCU or manual switches
- ❌ More complex
- ❌ CFG voltage limits: &lt;5V for CH224D

## USB Type-C CC Pin Configuration

### The 5.1kΩ Pull-Down Resistors (R12, R13) - CRITICAL!

**Without R12 and R13, your circuit will NOT work!** These resistors are the "handshake" that starts PD negotiation.

```
USB-C Connector:
CC1 ───┬──→ CH224D pin 11 (CC1)
       │
    R12: 5.1kΩ (Rd resistor)
       │
      GND

CC2 ───┬──→ CH224D pin 10 (CC2)
       │
    R13: 5.1kΩ (Rd resistor)
       │
      GND
```

### How USB-C Device Detection Works

**Step 1: PD Adapter checks CC pins**

```
PD Adapter sends test signals:
CC1 ──→ Measures resistance to GND
CC2 ──→ Measures resistance to GND
```

**Step 2: Resistance determines device type**

```
Measured Resistance = Device Type:
┌──────────┬─────────────────────────┐
│ 5.1kΩ    │ SINK (wants power) ✅   │ ← This is us!
│ 56kΩ     │ Audio accessory         │
│ Open     │ Nothing connected       │
│ Other    │ Power source or cable   │
└──────────┴─────────────────────────┘
```

**Step 3: Cable orientation detection**

- USB-C cables can plug in either way (reversible)
- One of CC1 or CC2 will be the "active" pin (lower resistance path)
- Adapter uses the active CC pin for PD communication
- The 5.1kΩ resistor on that pin tells adapter which way cable is oriented

**Step 4: Start PD negotiation**

- Only if 5.1kΩ detected → Adapter recognizes device as PD sink
- Adapter initiates PD communication via active CC pin
- CH224D requests desired voltage (15V in our case)
- Adapter responds and negotiates power delivery

### What Happens WITHOUT R12/R13?

**Critical failure scenario:**

```
No 5.1kΩ resistors:
  ↓
PD adapter sees "open circuit" on CC pins
  ↓
Adapter thinks: "Nothing connected" or "Wrong device type"
  ↓
❌ NO PD negotiation happens
  ↓
❌ VBUS stays at 5V (default USB voltage)
  ↓
❌ Your circuit gets 5V instead of 15V
  ↓
❌ DC-DC converters and power supply don't work!
```

### Why Exactly 5.1kΩ?

**USB Type-C Specification defines this value:**

- **Sink devices MUST have Rd = 5.1kΩ (±20%)**
- This is a **universal standard** that all USB-C devices follow
- PD adapters are designed to detect this specific resistance value
- Not arbitrary - it's carefully chosen to distinguish device types

**Tolerance:**

- ±20% is acceptable (4.08kΩ to 6.12kΩ)
- We use ±1% for reliability (5.05kΩ to 5.15kΩ)
- Part: 0603 5.1kΩ ±1% resistor (JLCPCB C23186)

### Component Specifications

| Component | Value     | Tolerance | Purpose                | JLCPCB Part |
| --------- | --------- | --------- | ---------------------- | ----------- |
| **R12**   | **5.1kΩ** | **±1%**   | **CC1 pull-down (Rd)** | **C23186**  |
| **R13**   | **5.1kΩ** | **±1%**   | **CC2 pull-down (Rd)** | **C23186**  |

### Common Mistakes to Avoid

❌ **Mistake 1**: Forgetting R12/R13 entirely

- Result: No PD negotiation, stuck at 5V

❌ **Mistake 2**: Using wrong resistance value

- Result: Adapter misidentifies device type, no PD negotiation

❌ **Mistake 3**: Only installing one resistor (R12 or R13)

- Result: Cable orientation might not be detected correctly

❌ **Mistake 4**: Connecting resistors to wrong pins

- Result: CC communication fails

✅ **Correct**: 5.1kΩ ±1% on BOTH CC1 and CC2 to GND

### Summary

**R12 and R13 (5.1kΩ pull-downs) are the FIRST thing a PD adapter checks!**

Without them:

- ❌ No device identification
- ❌ No PD negotiation
- ❌ No 15V output
- ❌ Circuit doesn't work

With them:

- ✅ Adapter recognizes device as PD sink
- ✅ PD negotiation starts
- ✅ 15V power delivery works
- ✅ Happy modular synth! 🎵

## 6-Pin vs 24-Pin USB-C Connectors

### Full 24-Pin Connector

```
Pins: VCC, GND (4 each), CC1, CC2, DP, DM, TX/RX lanes, SBU, etc.
Use case: Full USB functionality (data + power)
Cost: Higher
```

### 6-Pin Power-Only Connector (Our Choice)

```
Pins: VBUS (2), GND (2), CC1, CC2
Use case: Power delivery only (no data)
Cost: Lower (~$0.036 vs $0.50+)
Part: C456012 (TYPE-C 6P)
```

**Why 6-pin is sufficient for PD:**

- ✅ VBUS pins carry negotiated voltage
- ✅ CC pins handle PD communication
- ✅ GND provides reference
- ✅ No data pins needed for power-only applications

**What we lose with 6-pin:**

- ❌ No USB data transfer (DP/DM)
- ❌ No alternate modes (DisplayPort, etc.)
- ✅ But we only need power, so perfect!

## PD-Only Mode (Why Short DP to DM)

When using 6-pin connector with no DP/DM pins:

**Datasheet requirement (Section 5.5):**

> "If there is no need to use A-port protocols (various protocols realized by DP/DM communication), the DP/DM pin on CH224K/CH224D is required to be disconnected from the DP/DM on the Type-C connector, and the **DP pin on CH224 is required to be shorted to the DM** on CH224."

```
CH224D:
Pin 8 (DP) ──┬── Short on PCB
Pin 9 (DM) ──┘

Effect: Disables BC1.2 and other USB data protocols
Result: PD-only operation
```

**Why this matters:**

- BC1.2 = Battery Charging specification (uses DP/DM)
- We don't need BC1.2 since we have PD
- Shorting DP to DM tells CH224D to ignore data protocols
- Focuses on PD negotiation only

## PD Negotiation Sequence

Step-by-step process when you plug in the USB-C cable:

### Step 1: Initial Connection (0-100ms)

```
┌─────────────┐                  ┌─────────────┐
│ USB-C PD    │ ──── VBUS ────→  │   CH224D    │
│ Adapter     │      5V          │   Device    │
└─────────────┘                  └─────────────┘

VBUS = 5V (default USB voltage)
```

- Adapter provides 5V default voltage
- CH224D powers up (VDD regulator starts)
- No negotiation yet - just basic USB power

### Step 2: Orientation Detection (100-200ms)

```
CC Pins:
CC1 ─── 5.1kΩ ─── GND  }  CH224D detects which CC pin
CC2 ─── 5.1kΩ ─── GND  }  is active (cable orientation)
```

- USB-C is reversible (can plug in either way)
- Only ONE CC pin is active at a time
- Active CC pin = cable orientation
- 5.1kΩ pull-downs identify device as sink

### Step 3: Capability Discovery (200-300ms)

```
Device:  "What voltages do you support?"
Adapter: "I have: 5V/3A, 9V/3A, 12V/3A, 15V/3A, 20V/2.25A"
```

- CH224D sends Source Capabilities request via CC
- Adapter responds with available power profiles
- This is PD protocol communication (digital)

### Step 4: Voltage Request (300-400ms)

```
CH224D reads CFG1 resistor:
- Rset = 56kΩ detected
- Requests: 15V @ 3A

Device:  "I want 15V @ 3A (45W)"
Adapter: "Accepted, switching voltage..."
```

- CH224D determines requested voltage from Rset
- Sends Request message via CC
- Adapter checks if it can provide that power

### Step 5: Voltage Transition (400-1000ms)

```
VBUS voltage transition:
5V → [ramping] → 15V

Adapter gradually increases VBUS voltage
```

- **Critical**: VBUS voltage changes on the same pin!
- Voltage ramps up smoothly (not instant)
- Downstream circuits must handle this transition
- Input capacitors smooth the transition

### Step 6: Power Ready (>1000ms)

```
VBUS = 15V stable
PG pin goes LOW (power good indicator)
System can draw up to 45W (15V × 3A)
```

- Negotiation complete
- LED1 lights up (PG indicator)
- Main power supply can operate
- DC-DC converters receive 15V input

## Design Considerations

### Input Filtering

VBUS needs filtering capacitors:

```
VBUS ──┬─── C1 (10µF) ──→ GND    (Bulk filtering)
       │
       └─── C2 (100nF) ─→ GND    (HF decoupling)
```

**Why both capacitors?**

- **10µF (bulk)**: Stores energy during voltage transition (5V→15V)
- **100nF (ceramic)**: Filters high-frequency noise, placed close to IC
- Together provide stable power during negotiation

### VDD Decoupling

Internal 4.7V regulator needs decoupling:

```
VDD (pin 7) ─── C30 (1µF) ──→ GND
```

**Why needed?**

- VDD powers internal circuits
- 1µF cap stabilizes internal regulator
- Prevents oscillation and noise
- Datasheet requires this!

### Power Good (PG) Indicator

```
+5V ──→ R10 (330Ω) ──→ LED1 (Green) ──→ PG (pin 8) ──→ GND
                                        (open-drain)
```

**How it works:**

- PG pin is open-drain output
- Normal operation: PG = HIGH (LED off)
- After successful negotiation: PG = LOW (LED on)
- LED lights up when 15V is ready!

**Why connect to +5V instead of VBUS?**

- VBUS changes from 5V to 15V
- +5V rail is stable (from linear regulator)
- LED brightness stays constant
- No need to worry about voltage changes

### PCB Layout Guidelines

**Critical traces:**

1. **VBUS**: Wide traces (≥1mm) or copper pour - carries up to 3A
2. **CC pins**: Keep traces short, symmetric length, away from noisy signals
3. **GND**: Solid ground plane, thermal pad (pin 0) with multiple vias
4. **VDD**: 1µF cap placed close to pin 7

**Component placement:**

- C2 (100nF) very close to VBUS pin
- C30 (1µF) very close to VDD pin
- R12, R13 (5.1kΩ CC pull-downs) close to IC

## CH224 Family Comparison

There are three variants in the CH224 family:

### CH224D (QFN-20) - Used in This Project

- **Package**: QFN-20 (3×3mm)
- **Features**: Full featured, VBUS up to 22V, GATE pin for NMOS
- **Configuration**: Resistor or level mode
- **Best for**: Advanced designs, higher power
- **Cost**: Medium

### CH224K (ESSOP-10)

- **Package**: ESSOP-10 (larger)
- **Features**: Similar to CH224D, has VBUS detection pin
- **Configuration**: Resistor or level mode
- **Best for**: Through-hole friendly designs
- **Cost**: Medium

### CH221K (SOT23-6)

- **Package**: SOT23-6 (tiny!)
- **Features**: PD protocol only, simplified
- **Configuration**: Resistor mode only
- **Best for**: Space-constrained, cost-sensitive
- **Cost**: Lowest

**Why we chose CH224D:**

- ✅ Small SMD package (good for JLCPCB assembly)
- ✅ Full PD features
- ✅ Resistor configuration (simple)
- ✅ Good stock availability (2,291 units)

## Common Mistakes to Avoid

### ❌ Mistake 1: Expecting a separate output pin

```
WRONG thinking:
VBUS (input) → CH224D → VOUT (output)

CORRECT understanding:
VBUS (5V input, 15V output) - same pin!
```

### ❌ Mistake 2: Forgetting CC pull-down resistors

```
WRONG: CC1, CC2 → CH224D (no pull-downs)
Result: PD negotiation fails!

CORRECT: CC1 → 5.1kΩ → GND, CC2 → 5.1kΩ → GND
Result: Identified as sink, negotiation works!
```

### ❌ Mistake 3: Using wrong Rset value

```
WRONG: Rset = 24kΩ → requests 12V instead of 15V!

CORRECT: Rset = 56kΩ → requests 15V ✅
```

### ❌ Mistake 4: Not shorting DP to DM with 6-pin connector

```
WRONG: DP and DM left floating
Result: IC may behave unpredictably

CORRECT: DP (pin 8) shorted to DM (pin 9)
Result: PD-only mode works correctly
```

### ❌ Mistake 5: Forgetting VDD decoupling capacitor

```
WRONG: VDD pin with no capacitor
Result: Unstable operation, oscillation

CORRECT: VDD → 1µF cap → GND
Result: Stable internal regulator
```

## Why CH224D is Perfect for This Project

Our modular synth power supply needs:

- ✅ **15V from USB-C PD** → CH224D negotiates this automatically
- ✅ **Simple configuration** → Just one 56kΩ resistor
- ✅ **No microcontroller** → Standalone operation
- ✅ **Power-only application** → 6-pin connector sufficient
- ✅ **Up to 45W (15V × 3A)** → Enough for our DC-DC converters
- ✅ **JLCPCB compatible** → SMD package, good stock

**Alternative approaches would be worse:**

- ❌ Fixed 12V adapter → Less portable, requires wall outlet
- ❌ USB-C to DC barrel cable → Only 20V max, needs extra converter
- ❌ PD trigger boards → Usually larger, more expensive
- ❌ Microcontroller-based PD → Complex, overkill for fixed voltage

**CH224D = Perfect balance of simplicity and functionality!**

## Related Documentation

- [CH224D Component Page](/docs/components/ch224d) - Full specifications and pinout
- [J1 USB-C Connector](/docs/components/usb-c-connector) - Connector specifications
- [Diagram1: USB-PD Section](/docs/overview/circuit-diagrams#diagram1-usb-pd-power-supply-section) - Complete circuit
- [USB Type-C Pinout](/docs/learning/usb-type-c-pinout) - Understanding USB-C pins
- [CH224D Datasheet](/datasheets/CH224D-datasheet.pdf) - Official datasheet

## References

- [CH224D Datasheet](http://www.wch-ic.com/products/CH224.html) - WCH Official
- [USB Power Delivery Specification 3.1](https://www.usb.org/document-library/usb-power-delivery) - USB-IF
- [USB Type-C Specification](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-21) - USB-IF
