---
sidebar_position: 3
---

# Eurorack Power Distribution Best Practices

Lessons learned from commercial Eurorack power systems, particularly the Toppobrillo Eurobus.

## Introduction

When designing a Eurorack power supply, the distribution system is just as important as the power regulation itself. This document explores best practices from commercial designs and their applicability to DIY/JLCPCB-compatible builds.

## Case Study: Toppobrillo Eurobus

The Toppobrillo Eurobus is a high-end Eurorack power distribution system that represents best-in-class design practices.

**Specifications:**

- Power: +12V @ 3.5A, -12V @ 2A, +5V @ 1.5A
- 20 keyed power connectors
- 4-layer PCB with stitched ground plane
- Zone-filtered distribution
- Soft-start and comprehensive protection

**Key Design Philosophy:**

> "By utilizing the full width of the busboard for thicker traces and uninterrupted ground planes, routing and return paths are optimized - reducing impedances, improving power delivery, and lowering noise across the board."

## Critical Design Features

### 1. Keyed Connectors (Critical Safety Feature)

**What:** Polarized/keyed 16-pin IDC connectors that physically prevent reverse insertion.

**Why important:**

- Eurorack modules can be **destroyed instantly** by reverse polarity
- +12V to GND short creates catastrophic failure
- Users work in cramped cases with poor visibility
- Ribbon cables are easy to connect backwards

**Standard vs Keyed:**

```
Standard 2x8 Header (No Keying):
  Can be inserted either way
  ❌ No protection against reverse connection
  ❌ User must check red stripe alignment
  ⚠️  Risk of module destruction

Keyed 2x8 Header:
  Physical key prevents backward insertion
  ✅ Impossible to connect backwards
  ✅ Foolproof connection
  ✅ Critical for beginners and low-light conditions
```

**Implementation Options:**

| Approach                   | PCB Side            | Cable Side          | JLCPCB Compatible | Safety Level                |
| -------------------------- | ------------------- | ------------------- | ----------------- | --------------------------- |
| **Standard (our current)** | Standard pin header | Standard IDC        | ✅ Yes            | ⚠️ Low (user dependent)     |
| **Hybrid (recommended)**   | Standard pin header | Keyed IDC connector | ✅ Yes            | ✅ High (cable-side keying) |
| **Full keyed**             | Keyed pin header    | Keyed IDC connector | ❌ No             | ✅✅ Highest                |

**Recommendation for DIY builds:**

- Use standard pin header on PCB (JLCPCB compatible)
- **Strongly recommend keyed IDC connectors** on ribbon cables (user-sourced)
- Document the pinout clearly with pin 1 marked

**Where to source keyed connectors:**

- Tayda Electronics: 16-pin box headers
- Mouser/Digikey: Keyed IDC connectors
- Modular synth suppliers: Pre-made keyed cables

### 2. Zone Filtering Architecture

**What:** Multiple decoupled power distribution zones instead of a single point.

**Eurobus approach:**

```
Power Input
    │
    ├─→ Zone 1 (Connectors 1-10)
    │   ├─→ Bulk capacitor (470µF)
    │   ├─→ Ceramic decoupling (100nF × N)
    │   └─→ 10× Output connectors
    │
    └─→ Zone 2 (Connectors 11-20)
        ├─→ Bulk capacitor (470µF)
        ├─→ Ceramic decoupling (100nF × N)
        └─→ 10× Output connectors
```

**Benefits:**

- Isolates noise between module groups
- Reduces voltage sag from distant modules
- Lowers ground bounce and crosstalk
- Better current distribution

**Our current design:**

```
Power Input
    │
    └─→ Single output point
        ├─→ Bulk capacitor (470µF)
        ├─→ Ceramic decoupling (100nF)
        └─→ 1× Output connector
```

**When to implement zones:**

- Systems with >10 modules
- Multiple cases/busboards
- High-power digital modules (sampling, DSP)

**For single-output designs (like ours):**

- Zone filtering not necessary
- Good decoupling at regulator output is sufficient
- Keep output connector close to final filter caps

### 3. PCB Design for Low Impedance Distribution

**Eurobus best practices:**

#### 4-Layer PCB Stackup

```
Layer 1 (Top):     Signal traces, component pads
Layer 2 (Inner):   Ground plane (continuous)
Layer 3 (Inner):   Power planes (+12V, -12V, +5V)
Layer 4 (Bottom):  Ground plane, return paths
```

**Why 4 layers:**

- Continuous ground reference reduces impedance
- Power planes minimize voltage drop
- Better EMI/noise performance
- More routing flexibility

**2-layer alternative (cost-optimized):**

```
Layer 1 (Top):     Signal + power traces (thick copper)
Layer 2 (Bottom):  Ground plane + power traces
```

**Trade-offs:**

- 4-layer: Better performance, higher cost (~2-3× PCB cost)
- 2-layer: Adequate for small systems, lower cost

#### Copper Thickness

**Standard:** 1oz copper (35µm)
**Eurobus:** Extra-thick copper (2oz or more)

**Benefits of thick copper:**

- Lower resistance → less voltage drop
- Better current capacity
- Improved thermal dissipation

**Voltage drop calculation:**

```
Example: 10cm trace, 1.2A current

1oz copper (35µm), 1mm width:
  Resistance: ~17mΩ
  Voltage drop: 1.2A × 17mΩ = 20mV ⚠️

2oz copper (70µm), 2mm width:
  Resistance: ~4.3mΩ
  Voltage drop: 1.2A × 4.3mΩ = 5mV ✅
```

**Recommendation:**

- Power traces: 2oz copper, 2mm+ width
- Ground pour: Maximum copper area
- Signal traces: 1oz acceptable

#### Ground Plane Stitching

**What:** Multiple vias connecting top and bottom ground planes.

```
Bad (High Impedance):
  Top GND ═══════════════ Few vias
                          ↕ (long path)
  Bot GND ═══════════════

Good (Low Impedance):
  Top GND ═╪═╪═╪═╪═╪═╪═╪═ Many vias
           ↕ ↕ ↕ ↕ ↕ ↕ ↕  (short paths)
  Bot GND ═╪═╪═╪═╪═╪═╪═╪═
```

**Guidelines:**

- Via spacing: Every 5-10mm on ground areas
- Around high-current components: 2-3mm spacing
- Creates "stitched" ground plane with low impedance

### 4. Distributed Decoupling Strategy

**Eurobus approach:**

- Bulk electrolytic capacitors at each zone
- Multiple ceramic capacitors distributed along bus
- Low-ESR polycapacitors for high-frequency filtering

**Capacitor placement hierarchy:**

```
1. Regulator output (immediate):
   └─→ Large electrolytic (470µF) + ceramic (100nF)

2. Zone/distribution point (medium distance):
   └─→ Electrolytic (100-470µF) + ceramic (100nF)

3. Each connector (local):
   └─→ Small ceramic (10-100nF) very close to pin
```

**Why distributed:**

- Large electrolytics: Bulk energy storage, slow response
- Small ceramics: Fast transient response, low ESR
- Multiple locations: Reduces inductance from wire length

**Practical implementation:**

```
Poor (single-point decoupling):
  Regulator → [470µF] → 50cm trace → Connector
                                     ↑ Inductance kills fast response

Good (distributed decoupling):
  Regulator → [470µF][100nF] → 25cm → [100µF][10nF] → Connector
              ↑ Bulk              ↑ Local            ↑ Very close
```

### 5. Thermal Management

**Eurobus achievement:** 90% efficiency, runs "relatively cool"

**Heat sources in power supplies:**

1. DC-DC converters (switching losses)
2. Linear regulators (dropout voltage × current)
3. PTCs when tripped (self-heating)

**Thermal design checklist:**

✅ **Component spacing:**

- Keep heat-generating components apart
- LM7812 away from PTC fuses
- DC-DC converters in open area

✅ **PCB heat dissipation:**

- Large copper pours act as heatsinks
- Thermal vias under hot components (TO-263 packages)
- Multiple vias from thermal pad to ground plane

✅ **Airflow:**

- Don't block component top side
- Consider case ventilation
- Modular cases are usually well-ventilated

**Thermal via pattern example:**

```
TO-263 Package (top view):
  ┌─────────────┐
  │  [Thermal]  │ ← Large thermal pad
  │  [[[[]]]]]  │ ← 5-9 vias to bottom ground
  │  Pin Pin    │
  └─────────────┘

Bottom layer:
  Large copper pour connected via thermal vias
  Acts as heatsink (dissipates to case/air)
```

## Comparison: Eurobus vs Our Design

| Feature               | Eurobus                       | Our USB-PD Design                    | Gap                                         |
| --------------------- | ----------------------------- | ------------------------------------ | ------------------------------------------- |
| **Power Output**      | +12V@3.5A, -12V@2A, +5V@1.5A  | +12V@1.5A, -12V@1A, +5V@1.5A         | Smaller capacity (suitable for ~10 modules) |
| **Connectors**        | 20× keyed                     | 1× standard                          | ⚠️ No keying, single output                 |
| **Zone Filtering**    | 2 zones                       | Single point                         | Not needed for 1 output                     |
| **PCB Layers**        | 4-layer                       | TBD (recommend 4)                    | Should specify                              |
| **Copper Thickness**  | Extra-thick                   | TBD (recommend 2oz)                  | Should specify                              |
| **Protection**        | OCP, OVP, thermal, soft-start | 4-layer (USB-PD, DC-DC, LM78xx, PTC) | ✅ Comparable                               |
| **Decoupling**        | Polycaps, distributed         | Electrolytic + ceramic               | ✅ Good                                     |
| **Auto-reset**        | Yes (electronic)              | Yes (PTC)                            | ✅ Excellent                                |
| **JLCPCB Compatible** | No (custom parts)             | Yes (100% JLCPCB parts)              | ✅ Major advantage                          |

**Our design strengths:**

- ✅ Full JLCPCB compatibility (low cost, high availability)
- ✅ 4-layer protection (exceeds most commercial designs)
- ✅ PTC auto-reset (better than manual fuses)
- ✅ Low-noise architecture (DC-DC + linear)

**Areas for improvement:**

- ⚠️ Add keyed connector recommendation to documentation
- ⚠️ Specify 4-layer PCB in design files
- ⚠️ Specify 2oz copper for power traces
- ⚠️ Add thermal via guidelines

## Recommendations for Our Design

### Immediate (Documentation Updates)

**1. Update BOM connector section:**

```markdown
**Strongly recommended for cable assembly:**
Use keyed IDC connectors instead of standard ribbon cable connectors.
This prevents reverse insertion and protects modules from damage.

Sources:

- Tayda Electronics: 16-pin box header connectors
- Mouser/Digikey: Keyed IDC cable assemblies
```

**2. Add PCB design guidelines:**

- Recommend 4-layer PCB (or explain 2-layer trade-offs)
- Specify 2oz copper on power layers
- Thermal via pattern for TO-263 regulators
- Ground stitching recommendations

**3. Add assembly notes:**

- Mark Pin 1 clearly on silkscreen
- Add polarity warning labels
- Include Eurorack pinout diagram on PCB

### Future Enhancements (v2.0)

**If expanding to multiple outputs:**

1. Implement zone filtering (2 zones, 10 connectors each)
2. Add distributed decoupling at each zone
3. Consider larger current capacity (2A per rail)

**If moving to custom PCB manufacturer:**

1. Source keyed pin headers (not on JLCPCB)
2. Specify 2oz+ copper thickness
3. Add mounting holes for robust mechanical connection

## Key Takeaways

### 1. Keying is Critical for Safety

**Reverse polarity destroys modules instantly.** While not available on JLCPCB, strongly recommend keyed IDC connectors on cable side.

### 2. PCB Design Matters

**4-layer PCB with thick copper** significantly reduces noise and voltage drop. Worth the extra cost for >10 module systems.

### 3. Distributed Decoupling Works

**Multiple capacitor types at multiple locations** provides better transient response than single-point decoupling.

### 4. Our Design is Competitive

**4-layer protection + PTC auto-reset** exceeds many commercial designs. JLCPCB compatibility is a major advantage for DIY builders.

### 5. Thermal Management is Essential

**Component spacing, thermal vias, and copper pours** keep the supply cool and reliable. Don't neglect thermal design.

## References

### Commercial Systems Studied

- **Toppobrillo Eurobus**: High-end zone-filtered distribution
  - [Product Page](https://toppobrillo.com/products/eurobus)
  - [MOD WIGGLER Discussion](https://www.modwiggler.com/forum/viewtopic.php?t=284015)
  - [Perfect Circuit](https://www.perfectcircuit.com/toppobrillo-eurobus-6u-kit-1-5a-5v-option.html)

### Related Documentation

- **Protection Strategy**: `/doc/docs/learning/protection-fuse-strategy.md`
- **Bill of Materials**: `/doc/docs/overview/bom.md`
- **Circuit Diagrams**: `/doc/docs/overview/circuit-diagrams.mdx`

### Further Reading

- [Buyer's guide: Eurorack cases and power - Signal Sounds](https://www.signalsounds.com/blog/buyers-guide-eurorack-cases-and-power)
- Eurorack power best practices (modular synth community wikis)
- PCB thermal design guidelines (various manufacturers)
