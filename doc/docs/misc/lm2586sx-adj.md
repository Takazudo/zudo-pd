---
sidebar_position: 3
---

import InverterU5Diagram from '../\_fragments/inverter-u5-diagram.mdx';

# [outdated] LM2586SX-ADJ Flyback Converter

:::danger Component Not Used in Current Design
**This component has been removed from the project due to FB pin voltage violation issues.**

**Reason for removal**: The LM2586 flyback topology violated the FB pin voltage specification (required to stay between GND and VCC, but flyback configuration forced it below GND).

**Replacement**: The negative voltage rail now uses **LM2596S-ADJ (U4) in inverting buck-boost configuration** (+15V → -13.5V), which is simpler, more reliable, and uses the same IC as the other DC-DC stages.

**Current diagram**: See [Diagram4: +15V → -13.5V Inverting Buck-Boost](/docs/inbox/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4)

This documentation is kept for reference and educational purposes only.
:::

## Historical Information

A high-efficiency 3A switching regulator designed for flyback, boost, and forward topologies. **Was previously planned** to generate negative voltage (-15V) from positive input (+15V) using flyback transformer topology, but **has been replaced** with a simpler LM2596S inverting buck-boost design.

- 🔗 [View on JLCPCB: C181324](https://jlcpcb.com/partdetail/C181324)
- 📄 Datasheet: Available from [Texas Instruments](https://www.ti.com/product/LM2586)

:::info Footprint Files Removed
Footprint files and preview images for this component have been removed from the documentation as it is no longer used in the current design.
:::

## Overview

The LM2586SX-ADJ is a 3A output capable switching regulator from Texas Instruments designed for multiple topologies including **flyback**, boost, and forward converters. In this project, it's configured as a **flyback converter** to generate -15V from +15V input using a coupled transformer.

**Why LM2586 flyback instead of charge pump (ICL7660)?**

- **Current requirement**: The -12V rail needs 800mA, but charge pumps like ICL7660 only provide ~100mA
- **High current capability**: LM2586 can deliver 3A, providing ample headroom for the 800mA requirement
- **Input voltage compatibility**: Handles 4V-40V input (ICL7660 max is 10V, requiring voltage clamping)
- **Isolated topology**: Flyback provides magnetic isolation between input and output (polarity inversion)

Being an adjustable output type (ADJ), the output voltage can be set using a feedback resistor divider. The 200kHz switching frequency allows for reasonably sized magnetic components.

## Specifications

### Electrical Characteristics

| Parameter                  | Value                                      |
| -------------------------- | ------------------------------------------ |
| **Input Voltage Range**    | 4V - 40V DC                                |
| **Output Voltage Range**   | Adjustable (flyback: negative outputs)     |
| **Maximum Output Current** | 3A                                         |
| **Switching Frequency**    | 200kHz (typical)                           |
| **Efficiency**             | 75% - 85% (typical, flyback configuration) |
| **Reference Voltage**      | 1.23V (internal, for feedback)             |
| **Operating Temperature**  | -40°C to +125°C                            |
| **ON/OFF Control**         | Floating = ON, ≥3V = Shutdown              |
| **Shutdown Current**       | 56µA typical (16µA to VIN, 40µA to ON/OFF) |

### Package Information

- **Package Type**: TO-263-7 (DDPAK, 7-pin)
- **Dimensions**: 10.2mm × 8.6mm (approx)
- **Pin Count**: 7 pins
- **Mounting**: SMD (Surface Mount Device)
- **Thermal Pad**: Large metal tab for heat dissipation
- **LCSC Part Number**: C181324
- **Stock**: 89 units (as of last check - limited availability)

## Pin Configuration

```
         TOP VIEW (KTW Package)
    ┌──────────────┐
    │7            1│
    │VIN  Freq.Adj.│
    │              │
    │6            2│
    │Sync     Comp │
    │              │
    │5            3│
    │SW         FB │
    │              │
    │4             │
    │GND           │
    │              │
    └──────────────┘
      TO-263-7
```

| Pin | Name                | Function                                                |
| --- | ------------------- | ------------------------------------------------------- |
| 1   | Freq. Adj. - On/Off | Frequency adjustment or shutdown control (Float = ON)   |
| 2   | Compensation        | Error amplifier compensation (RC network to GND)        |
| 3   | Feedback            | Feedback input (voltage sense via resistor divider)     |
| 4   | Ground              | Ground reference                                        |
| 5   | Switch              | Switch output (connects to flyback transformer primary) |
| 6   | Freq. Sync.         | Frequency synchronization (not used in this project)    |
| 7   | VIN                 | Input voltage (+15V from Diagram1)                      |

## Obsolete Bill of Materials

The following components were planned but never manufactured. This design was abandoned before PCB production.

### Planned Components (Not Ordered)

**Main IC:**

- **U5**: LM2586SX-ADJ - [C181324](https://jlcpcb.com/partdetail/C181324) - $0.50 (estimated) - **89 units stock**

**Transformer:**

- **T1**: MSD1514-473MED - [C40657138](https://jlcpcb.com/partdetail/C40657138) - Coilcraft 47µH:47µH coupled transformer - **Price TBD**

**Feedback/Compensation Resistors:**

- **R7**: 10kΩ ±1% 0603 - [C25804](https://jlcpcb.com/partdetail/C25804) - $0.0005
- **R8**: 910Ω ±1% 0603 - Standard value (E96 series) - $0.0005 (estimated)
- **R9**: 3kΩ ±1% 0603 - [C22790](https://jlcpcb.com/partdetail/C22790) - $0.0005

**Capacitors:**

- **C13**: 100µF 25V electrolytic - Input bulk filter
- **C14**: 100µF 25V electrolytic - Output filter (reversed polarity)
- **C15**: 47nF ceramic X7R - Compensation capacitor
- **C16**: 100nF 50V X7R ceramic - Input decoupling

**Diode:**

- **D4**: SS34 Schottky 3A 40V - [C8678](https://jlcpcb.com/partdetail/C8678) - $0.012

**Why These Components Were Never Ordered:**

- Design flaw discovered during circuit simulation (FB pin voltage violation)
- Replaced with simpler LM2596S inverting buck-boost topology
- New design uses components already in BOM for other stages
- Saves cost and reduces unique part count

## Application in This Project (Historical)

### Flyback Converter Configuration (Old Diagram4: U5)

<InverterU5Diagram />

### Component Values for -15V Output (As Planned)

| Component | Value                   | Purpose                                     |
| --------- | ----------------------- | ------------------------------------------- |
| **T1**    | 47µH:47µH coupled (1:1) | Flyback transformer (MSD1514-473MED)        |
| **C13**   | 100µF electrolytic      | Input bulk filter capacitor                 |
| **C16**   | 100nF ceramic (X7R)     | Input decoupling capacitor (high-frequency) |
| **C14**   | 100µF electrolytic      | Output filter capacitor (reversed polarity) |
| **D4**    | Schottky diode, 3A      | Output rectifier (SS34, MBRS340)            |
| **R7**    | 10kΩ                    | Feedback resistor (upper)                   |
| **R8**    | 910Ω                    | Feedback resistor (lower, sets -15V output) |
| **R9**    | 3kΩ                     | Compensation resistor (Pin 2)               |
| **C15**   | 47nF ceramic            | Compensation capacitor (Pin 2 to GND)       |

:::warning Coupled Transformer Required
T1 must be a **coupled transformer** with magnetically linked primary and secondary windings on the same core. Separate inductors will NOT work in flyback topology.
:::

### Output Voltage Calculation

The output voltage is set by the feedback resistor divider:

```
VOUT = -1.23V × (1 + R7/R8)

For -15V output:
-15V = -1.23V × (1 + 10kΩ/R8)
15V / 1.23V = 1 + 10kΩ/R8
12.195 = 1 + 10kΩ/R8
R8 = 10kΩ / 11.195 = 893Ω

Using closest standard E96 value:
R8 = 910Ω → VOUT = -14.75V (-1.7% error, acceptable)
```

## Design Considerations

### Flyback Transformer Selection (T1)

**Critical Requirements:**

- **Coupled transformer**: Primary and secondary MUST be magnetically coupled on same core
- **Turns ratio**: 1:1 for equal voltage transformation
- **Inductance**: 47µH:47µH (primary:secondary)
- **Current rating**: Minimum 3A primary current
- **Saturation current**: 7.5A or higher for safety margin
- **DCR (DC resistance)**: Lower is better for efficiency (&lt;100mΩ recommended)

**Recommended Part:**

- Coilcraft MSD1514-473MED (JLCPCB: C40657138)
- 47µH:47µH, 7.5A, 75mΩ DCR, Shielded

### Capacitor Selection

**Input Capacitors (Dual-stage filtering):**

- **C13 (100µF electrolytic)**: Bulk energy storage, low-frequency ripple filtering
- **C16 (100nF ceramic)**: High-frequency decoupling, essential for switching noise suppression
- **Voltage rating**: ≥25V (input is +15V with safety margin)
- **Placement**: Both capacitors must be placed close to VIN and GND pins

**Output Capacitor:**

- **C14 (100µF electrolytic)**: Output ripple filtering
- **Polarity**: Reversed for negative voltage (positive terminal to GND)
- **Voltage rating**: ≥25V (output is -15V with safety margin)
- **ESR**: Low ESR type for better ripple performance

**Compensation Capacitors:**

- **C15 (47nF ceramic)**: Type II compensation network stability
- **Type**: X7R or C0G/NP0 for temperature stability
- **Placement**: Close to Pin 2 (COMP)

### Diode Selection (D4)

**Requirements:**

- **Type**: Schottky diode (essential for 200kHz switching)
- **Forward voltage**: &lt;0.5V at rated current for efficiency
- **Current rating**: Minimum 3A average
- **Reverse voltage**: ≥40V (must handle input + output voltage swing)
- **Recommended**: SS34, MBRS340, or equivalent

### Compensation Network (Pin 2)

**Purpose:** Stabilizes the control loop for flyback operation

**Type II Compensation:**

- **R9** (3kΩ): Sets compensation pole location
- **C15** (47nF): Sets compensation zero location
- **Configuration**: Series RC from Pin 2 to GND

**Datasheet Reference:** Figure 16 (page 14) shows typical compensation values

### ON/OFF Pin Control

For **always-on operation** (this project):

- Leave Pin 1 **floating (open circuit)**
- Do not connect to VIN or GND
- Internal pull-up enables converter automatically

For **enable/disable control** (future enhancement):

- Float or pull low (&lt;0.8V) = Enable
- Pull high (≥3V to VIN) = Shutdown
- Low shutdown current: 56µA typical

### Thermal Management

**Power Dissipation Calculation:**

```
Efficiency ≈ 80% (flyback at 15V→-15V)
Input Power = 15V × 1A = 15W
Output Power = 15V × 0.8A = 12W
Power Loss = 15W - 12W = 3W
```

**Thermal Considerations:**

- **Maximum junction temperature**: 150°C
- **Typical power loss**: 2-3W at 800mA load
- **Heat dissipation**: Requires adequate copper pour on thermal pad
- **Thermal vias**: Use multiple vias under thermal pad to bottom ground plane
- **Copper area**: Minimum 2 square inches for proper heat spreading

## PCB Layout Guidelines

### Critical Components (Minimize Trace Length)

1. **Input capacitors (C13, C16)**:
   - Place immediately adjacent to VIN (Pin 7) and GND (Pin 4)
   - C16 ceramic must be closest to pins (high-frequency path)
   - Minimize loop area to reduce EMI

2. **Flyback transformer (T1)**:
   - Keep primary connection to SW (Pin 5) short and wide
   - Secondary side traces to D4 should be short
   - Minimize magnetic coupling to other components

3. **Output diode (D4)**:
   - Place close to T1 secondary terminal
   - Short, wide trace to C14 output capacitor
   - Minimize high-frequency current loop

4. **Feedback resistors (R7, R8)**:
   - Keep close to FB (Pin 3)
   - Use ground plane beneath for noise immunity
   - Kelvin connection to output for accurate sensing

5. **Compensation network (R9, C15)**:
   - Place immediately adjacent to COMP (Pin 2)
   - Short trace to clean GND point

### Ground Plane Strategy

**Recommended Layout:**

- **Power ground**: Carries high switching currents (SW, D4, C13, C14)
- **Signal ground**: Low-noise reference (FB, COMP)
- **Connection**: Single-point connection near Pin 4 (GND)
- **Thermal pad**: Large copper pour connected to power ground with thermal vias

**Ground Current Paths:**

```
Input: C13/C16 → GND (Pin 4) → T1 Primary return → +15V
Output: C14 → GND → T1 Secondary → D4 → -15V
```

### Component Placement

**Optimal Layout Flow:**

```
         +15V IN
            │
    ┌───────┴─────────┐
    │  C13      C16   │  (Input caps close to IC)
    │  100µF   100nF  │
    └────────┬────────┘
             │
        ┌────┴─────┐
        │ LM2586   │
        │   U5     │
        └────┬─────┘
             │ SW (Pin 5)
             │
          ┌──┴──┐
          │ T1  │ (Flyback transformer)
          │ 1:1 │
          └──┬──┘
             │
            D4 (Schottky, close to T1 secondary)
             │
            C14 (Output cap, reversed polarity)
             │
          -15V OUT
```

**Layer Stackup Recommendation:**

- **Top layer**: Components, signal traces
- **Inner layer 1** (optional): Ground plane
- **Inner layer 2** (optional): Power plane
- **Bottom layer**: Ground plane with thermal vias

### High-Frequency Noise Mitigation

1. **Input filter**: C13 (bulk) || C16 (ceramic) creates low-impedance path
2. **Switch node**: Keep SW (Pin 5) trace short, avoid running under sensitive signals
3. **Output rectifier**: Minimize D4 to C14 loop area (radiates at 200kHz)
4. **Feedback path**: Shield R7/R8 divider from switching noise
5. **Grounding**: Use star-point grounding near IC GND pin

## Stock and Availability

:::warning Limited Stock
**JLCPCB Stock**: 89 units (as of last check)

This is **significantly lower** than other components in this project:

- LM2596S: 12,075 units
- CH224D: 2,291 units

**Recommendations**:

1. Order early if using JLCPCB assembly
2. Consider alternative suppliers (Mouser, Digikey) for hand-assembly
3. Alternative part numbers: LM2586S-ADJ/NOPB (through-hole variant)
4. Monitor stock levels before PCB production
   :::

## Troubleshooting

### No Output Voltage

**Check:**

- ✓ **ON/OFF pin (Pin 1)**: Should be floating or pulled low (NOT high)
- ✓ **Input voltage**: Verify +15V present at VIN (Pin 7)
- ✓ **Transformer connections**:
  - Primary: +15V to one end, SW (Pin 5) to other end
  - Secondary: GND to one end, D4 cathode to other end
- ✓ **Diode polarity**: Cathode to T1 secondary, anode to -15V output
- ✓ **Feedback divider**: R7/R8 properly connected to FB (Pin 3)

### Low Output Voltage (less negative than -15V)

**Check:**

- ✓ **Feedback resistors**: Verify R7 = 10kΩ, R8 = 910Ω
- ✓ **Transformer saturation**: May need higher saturation current rating
- ✓ **Diode forward voltage**: Use low-VF Schottky (SS34, not 1N4001)
- ✓ **Load current**: Verify not exceeding 3A rating
- ✓ **Compensation network**: Verify R9 = 3kΩ, C15 = 47nF present

### High Output Ripple

**Check:**

- ✓ **Output capacitor ESR**: Use low-ESR electrolytic (&lt;100mΩ)
- ✓ **Ceramic bypass**: Add 10µF ceramic in parallel with C14
- ✓ **PCB layout**: Minimize D4 to C14 loop area
- ✓ **Ground connection**: Ensure C14 negative terminal has solid GND connection

### Oscillation or Instability

**Check:**

- ✓ **Compensation network**: Verify R9 and C15 are present and correct values
- ✓ **Feedback path**: Check for noise coupling into FB (Pin 3)
- ✓ **Layout**: Ensure compensation components (R9, C15) are close to Pin 2
- ✓ **Load transient**: May need increased output capacitance for fast load changes

### Overheating

**Check:**

- ✓ **Load current**: Verify &lt;3A continuous
- ✓ **Thermal pad connection**: Ensure good solder coverage and thermal vias
- ✓ **Input voltage**: Higher VIN increases switching losses
- ✓ **Transformer DCR**: High resistance increases I²R losses
- ✓ **Diode selection**: Use Schottky (low VF) not standard rectifier

### Unexpected Shutdown

**Check:**

- ✓ **ON/OFF pin**: Ensure floating or &lt;0.8V (not driven high)
- ✓ **Thermal shutdown**: Check if IC temperature exceeds 150°C
- ✓ **Overcurrent protection**: May be triggering at 5A+ peak current
- ✓ **Input undervoltage**: Verify VIN stays above 4V minimum

## Related Documents

**Current Design:**

- [Diagram4: +15V → -13.5V Inverting Buck-Boost (Current)](/docs/inbox/circuit-diagrams#diagram4-15v---135v-inverting-buck-boost-lm2596s-adj-u4)
- [LM2596S-ADJ Component Page](../components/lm2596s-adj) - The IC actually used for negative voltage generation

**Historical (Not Used):**

- Old Diagram4: Used LM2586 Flyback (removed)
- Old Diagram5: Used -15V → -13.5V Buck (removed)
- [Bill of Materials: Obsolete Components Section](../components/bom#obsolete-components---not-used-in-current-design)
- [Overview: System Architecture](../inbox/overview)
- [Quick Reference: Component Specifications](../inbox/quick-reference)

## References

- [Texas Instruments LM2586 Product Page](https://www.ti.com/product/LM2586)
- Application Note: "Flyback Regulator Design" (Texas Instruments)
- [JLCPCB Part Detail: C181324](https://jlcpcb.com/partdetail/C181324)
- [Coilcraft MSD1514-473MED Datasheet](https://www.coilcraft.com/en-us/products/power/coupled-inductors/shielded-coupled-inductors/msd/)
