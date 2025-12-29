---
sidebar_position: 2
---

# Open-Drain Outputs: Understanding the PG Pin

How the CH224Q's Power Good (PG) pin works and why the LED circuit is connected the way it is.

## The Question

When designing the LED status indicator for the USB-PD circuit, I needed to understand:

> "The PG pin connects to GND when power is stable at 15V? So the circuit becomes: +5V → LED → GND, and the LED lights up?"

The answer is **YES** ✅, and here's why.

## What is an Open-Drain Output?

The CH224Q's **PG (Power Good)** pin is an **open-drain output**. This is a common digital output type that works differently from regular logic outputs.

### Regular Logic Output (Push-Pull)

A typical digital output can drive both HIGH and LOW:

```
Regular Output Pin:
├─ HIGH: Connects to VCC (e.g., 3.3V)
└─ LOW:  Connects to GND (0V)
```

### Open-Drain Output

An open-drain output can only pull LOW or float:

```
Open-Drain Output Pin:
├─ Active:   Connects to GND (pulls LOW)
└─ Inactive: High-impedance (floating, not connected to anything)
```

Think of it as a **switch to ground**:
- Switch CLOSED → Pin = GND
- Switch OPEN → Pin = floating (not connected)

## How the PG Pin Works

The CH224Q uses the PG pin to indicate when USB-PD negotiation is successful and 15V is stable.

### Internal Circuit Diagram

```
Inside CH224Q:
                    ┌─────────────┐
                    │   Control   │
                    │   Logic     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
PG pin ────────────┤  Transistor  ├──→ GND (inside chip)
(to LED cathode)   │  (N-channel) │
                   └──────────────┘

                When "power good":
                → Control logic turns transistor ON
                → PG pin connects to GND
```

### Two States

**State 1: Power NOT Good** (negotiating or failed)
```
PG Pin = HIGH-Z (floating)

+5V ──[330Ω]──[LED]──→ PG pin (floating)
                        ↑
                     No path to GND
                     → No current flow
                     → LED OFF ❌
```

**State 2: Power Good** (15V stable)
```
PG Pin = LOW (connected to GND)

+5V ──[330Ω]──[LED]──→ PG pin (= GND)
                        ↓
                      GND

Complete circuit: +5V → Resistor → LED → GND
→ Current flows (~8mA)
→ LED ON ✅ (Green, indicates safe power)
```

## Why Connect LED This Way?

The LED circuit in our design:

```
+5V Rail ──[R1: 330Ω]──[LED Anode]──[LED Cathode]──→ PG pin
```

### Why LED Anode to +5V?

Because the PG pin can only **sink current** (pull to GND), not **source current** (provide voltage). The LED needs a voltage source (+5V) on one side and a current sink (PG → GND) on the other.

### Why Not Connect Directly to 15V?

We **could** connect to 15V, but:
```
If using 15V:
I_LED = (15V - 2.2V) / 330Ω = 38.8mA ❌ (Too high! Max is 20mA)

If using +5V:
I_LED = (5V - 2.2V) / 330Ω = 8.5mA ✅ (Safe and bright)
```

The +5V rail provides the correct voltage for safe LED current with a standard 330Ω resistor.

## Circuit Behavior Timeline

When you plug in a USB-C PD charger:

```
Time 0ms:
- USB-C connected, VBUS starts at 5V
- PG pin = HIGH-Z (floating)
- LED OFF (green)
- Status: "Negotiating..."

Time 0-500ms:
- CH224Q negotiates 15V via CC pins
- PG pin = HIGH-Z (still floating)
- LED OFF (green)
- Status: "Negotiating..."

Time 500ms-1000ms:
- VBUS transitions 5V → 15V
- CH224Q verifies voltage is stable
- PG pin = HIGH-Z (still floating)
- LED OFF (green)
- Status: "Verifying..."

Time >1000ms:
- 15V confirmed stable
- PG pin = LOW (pulls to GND) ✅
- LED ON (green) ✅
- Status: "Power Good - 15V Ready"
```

## Key Takeaways

1. **Open-drain outputs** can only pull LOW or float (they cannot drive HIGH)
2. **PG pin acts like a switch to GND** that closes when power is good
3. **LED must be powered from +5V** (not from the PG pin itself)
4. **When PG pulls LOW**, it completes the circuit: +5V → LED → GND
5. **Green LED ON = Power is safe** (15V negotiated successfully)

## Common Mistake to Avoid

❌ **WRONG** - Trying to power LED from PG pin:
```
PG pin ──[Resistor]──[LED]──→ GND

Problem: PG pin cannot source voltage!
When PG = LOW, both sides of LED are at GND → No current → LED OFF
```

✅ **CORRECT** - Power LED from voltage rail:
```
+5V ──[Resistor]──[LED]──→ PG pin

When PG = LOW: +5V → LED → GND → Current flows → LED ON ✅
```

## Related Circuits

This open-drain concept is used in many digital ICs:
- **I²C bus** (SDA and SCL are open-drain)
- **1-Wire protocol** (Dallas/Maxim sensors)
- **Interrupt outputs** (many sensor ICs)
- **Status indicators** (like our PG pin)

Understanding open-drain outputs is essential for reading datasheets and designing digital circuits correctly!

## See Also

- [CH224D Documentation](/do../components/ch224d) - Full CH224D specifications
- [Circuit Diagrams - Diagram1](/docs/inbox/circuit-diagrams#diagram1-usb-pd-power-supply-section) - Complete USB-PD circuit
