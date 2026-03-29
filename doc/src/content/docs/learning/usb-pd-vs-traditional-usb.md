---
title: "USB-PD vs Traditional USB: Why Power Hubs Don't Exist"
sidebar_position: 5
---

# USB-PD vs Traditional USB: Why Power Hubs Don't Exist

This page explains the fundamental differences between traditional USB power distribution and USB Power Delivery (USB-PD), and why you can't simply use a "USB-C hub" to split USB-PD power.

## Traditional USB (2.0/3.0) - Simple Power Distribution

Traditional USB hubs were simple because of the fixed voltage system.

```
AC Adapter (5V)
      │
      ▼
┌─────────────┐
│   USB Hub   │  ← Just splits 5V to all ports
└─┬───┬───┬───┘
  │   │   │
  5V  5V  5V     ← Same voltage everywhere, no negotiation
```

**Key characteristics:**

- **Fixed 5V** - no voltage negotiation needed
- **Simple current limits** - 500mA (USB 2.0) or 900mA (USB 3.0) per port
- **Passive distribution** - hub just connects 5V rail to all ports
- Devices draw what they need (up to the limit)

The hub is essentially just a power splitter with some current limiting. Very simple, very cheap.

## USB-PD - Complex Negotiation Required

USB Power Delivery is fundamentally different. Each device negotiates its own voltage and current requirements.

```
Charger (supports 5V/9V/15V/20V)
      │
      ▼
┌─────────────┐
│   USB Hub   │  ← Must negotiate with EACH device separately
└─┬───┬───┬───┘
  │   │   │
  ?V  ?V  ?V     ← Each device wants different voltage!

Device A wants 20V/3A (laptop)
Device B wants 9V/2A (tablet)
Device C wants 15V/3A (zudo-PD)
```

**Why it's complicated:**

1. **Voltage negotiation per port** - Each device negotiates via CC pins
2. **Dynamic power budget** - Hub must track total power and reallocate
3. **Voltage conversion** - If charger provides 20V but device wants 9V, hub needs DC-DC converter
4. **Each port needs PD controller IC** - Adds cost and complexity
5. **Re-negotiation** - When devices plug/unplug, everything must re-negotiate

## Comparison Table

| Feature            | Traditional USB      | USB-PD                           |
| ------------------ | -------------------- | -------------------------------- |
| Voltage            | Fixed 5V             | 5V/9V/12V/15V/20V (negotiated)   |
| Negotiation        | None                 | Required per device              |
| Hub complexity     | Passive splitter     | Active controller per port       |
| Power sharing      | Simple current limit | Complex budget management        |
| Cost to distribute | Very low             | High (needs ICs, DC-DC per port) |

## How Multi-Port USB-PD Chargers Actually Work

Multi-port USB-PD chargers are **not simple hubs**. They have sophisticated internal architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Port GaN Charger                   │
│                                                             │
│  ┌─────────────┐                                            │
│  │   AC → DC   │  Single main power stage                   │
│  │   (GaN)     │  Converts AC to internal DC bus            │
│  └──────┬──────┘  (e.g., 24V or 48V internal)               │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │   Central   │  "Brain" - manages total power budget      │
│  │     MCU     │  Decides how much each port can have       │
│  └──────┬──────┘                                            │
│         │                                                   │
│    ┌────┴────┬────────┬────────┐                            │
│    ▼         ▼        ▼        ▼                            │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                         │
│ │DC-DC │ │DC-DC │ │DC-DC │ │DC-DC │  Per-port converters    │
│ │ + PD │ │ + PD │ │ + PD │ │ + PD │  (voltage conversion    │
│ │ IC   │ │ IC   │ │ IC   │ │ IC   │   + PD negotiation)     │
│ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                         │
│    │        │        │        │                             │
└────┼────────┼────────┼────────┼─────────────────────────────┘
     ▼        ▼        ▼        ▼
   USB-C    USB-C    USB-C    USB-C
   Port1    Port2    Port3    Port4
```

### Key Components

| Component                  | Role                                                              |
| -------------------------- | ----------------------------------------------------------------- |
| **AC-DC Stage**            | Single conversion from AC to internal DC bus (GaN for efficiency) |
| **Central MCU**            | Power budget manager - decides allocation per port                |
| **DC-DC per port**         | Converts internal bus to negotiated voltage (5V/9V/15V/20V)       |
| **PD Controller per port** | Handles CC negotiation with each device                           |

### Dynamic Power Allocation Example

```
Example: 200W charger, 4 ports

Device plugs into Port 1, requests 100W
  → MCU: "OK, 100W available for Port 1"

Device plugs into Port 2, requests 65W
  → MCU: "OK, 65W for Port 2, total 165W used"

Device plugs into Port 3, requests 100W
  → MCU: "Only 35W left! Re-negotiate..."
  → Tells Port 1 & 2: "reduce power"
  → Redistributes: 65W + 65W + 65W = 195W
```

This is why good chargers (Anker, UGREEN, etc.) publish power distribution tables - the central MCU follows specific rules for allocation.

## Key Terms

### GaN (Gallium Nitride)

A **semiconductor material** - alternative to traditional silicon.

| Property        | Silicon (old) | GaN (new)   |
| --------------- | ------------- | ----------- |
| Switching speed | Slower        | Much faster |
| Heat generation | More          | Less        |
| Size            | Larger        | Smaller     |
| Efficiency      | ~85%          | ~95%        |

**Result:** GaN chargers are smaller, cooler, and more efficient.

```
Same 65W output:

┌─────────────┐      ┌───────┐
│   Silicon   │  vs  │  GaN  │
│   Charger   │      │       │
│             │      └───────┘
└─────────────┘
     Large            Compact
```

### MCU (Micro Controller Unit)

A **tiny computer chip** - the "brain" inside devices.

```
┌─────────────────────────┐
│          MCU            │
│  ┌─────┐ ┌─────┐ ┌───┐  │
│  │ CPU │ │ RAM │ │I/O│  │  All in one tiny chip
│  └─────┘ └─────┘ └───┘  │
└─────────────────────────┘
```

- Runs simple programs
- Reads sensors, controls outputs
- Very low power, very cheap
- Found in almost everything: chargers, appliances, toys, cars...

**In USB-PD charger:** MCU monitors all ports, calculates power budget, tells each port how much power it can provide.

## Why You Can't Use a Regular USB-C Hub for Power

A regular USB-C hub (for data) cannot distribute USB-PD power because:

1. **No PD controllers** - Data hubs don't have PD negotiation ICs
2. **No DC-DC converters** - Can't provide different voltages per port
3. **No power management** - No MCU to manage power budget
4. **Fixed 5V only** - Most hubs only pass through 5V for charging

**Bottom line:** Multi-port USB-PD **chargers** exist (each port has its own PD controller and DC-DC converter), but USB-PD **hubs** that split power from a single upstream source are rare, expensive, and complex.

## Implications for Modular Synth Power

For powering multiple zudo-PD units, use a **multi-port USB-PD charger** (not a hub):

- Each port independently negotiates 15V
- Shared ground eliminates ground loops between cases
- Central MCU manages power allocation

See [USB-PD AC Adapter](/docs/overview/usb-pd-adapter#multi-case-setup-multiple-zudo-pd-units) for recommended multi-port chargers.
