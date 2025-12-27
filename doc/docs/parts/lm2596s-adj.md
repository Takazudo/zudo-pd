---
sidebar_position: 2
---

# LM2596S-ADJ Buck Converter

A high-efficiency 3A step-down switching regulator used for intermediate voltage generation through DC-DC conversion.

## Overview

The LM2596S-ADJ is a 3A output capable step-down (Buck) switching regulator from Texas Instruments. In this project, three LM2596S-ADJ units are used to convert the 15V voltage obtained from USB-C PD into various intermediate voltages.

Being an adjustable output type (ADJ), the output voltage can be freely set using external resistors. The high-efficiency (85-90%) switching method significantly reduces heat generation compared to linear regulators. The 150kHz switching frequency optimizes the size of inductors and capacitors.

## Specifications

### Electrical Characteristics

| Parameter | Value |
|-----------|-------|
| **Input Voltage Range** | 4.5V - 40V DC |
| **Output Voltage Range** | 1.23V - 37V (adjustable) |
| **Maximum Output Current** | 3A |
| **Switching Frequency** | 150kHz (typical) |
| **Efficiency** | 85% - 90% (typical, depends on load) |
| **Reference Voltage** | 1.23V (internal) |
| **Operating Temperature** | -40°C to +125°C |
| **Dropout Voltage** | ~1.5V (minimum Vin - Vout) |
| **ON/OFF Control** | High = ON, Low = Shutdown |

### Package Information

- **Package Type**: TO-263-5 (D2PAK)
- **Pin Count**: 5 pins
- **Mounting**: SMD (Surface Mount Device)
- **Thermal Pad**: Large metal tab for heat dissipation

## Pin Configuration

```
          LM2596S-ADJ (TO-263-5)
             Top View

        ┌───────────────────┐
        │   ▓▓▓▓▓▓▓▓▓▓▓▓▓   │ ← Thermal Tab (GND)
        │                   │
        │  1   2   3   4   5│
        └───┬───┬───┬───┬───┘
            │   │   │   │
           VIN OUT GND FB  ON/OFF
```

### Pin Descriptions

| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN | Voltage Input (4.5V - 40V) |
| 2 | OUTPUT | Switching Output (connect to inductor) |
| 3 | GND | Ground (also thermal tab) |
| 4 | FEEDBACK | Voltage Feedback Input (1.23V reference) |
| 5 | ON/OFF | Enable Control (High = ON, connect to VIN for always-on) |
| TAB | GND | Thermal Tab (must connect to GND plane) |

## Application in This Project

In this project, three LM2596S-ADJ units are used in the following configuration:

### U2: +15V → +13.5V Conversion (for +12V rail)

```
+15V ─────┬─── L1: 100µH ──┬─── D1 ──┬─── C3: 470µF ──┬─→ +13.5V/1.3A
          │    (4.5A)      │   SS34  │    (25V)       │
          │                │    ↓    │                │
          │           ┌────┴─────────┴──┐             │
          │           │5  VIN      OUT │4────────────┤
          └───────────┤3  ON        FB │2─────┬──────┘
                      │1  GND          │      │
                      └────────────────┘      │
                              │               │
                             GND          ┌───┴───┐
                                          │ R1    │ 10kΩ
                                          │ 10kΩ  │
                                          └───┬───┘
                                          ┌───┴───┐
                                          │ R2    │ 1kΩ
                                          │ 1kΩ   │
                                          └───┬───┘
                                              │
                                             GND
```

**Output Voltage Calculation**:
```
Vout = 1.23V × (1 + R1/R2)
     = 1.23V × (1 + 10kΩ/1kΩ)
     = 1.23V × 11
     = 13.53V
```

**Component Values**:
- **L1**: 100µH, 4.5A Inductor (JLCPCB: C19268674, CYA1265-100UH)
- **D1**: SS34 Schottky Diode 3A/40V (JLCPCB: C8678)
- **C3**: 470µF/25V Electrolytic Capacitor (JLCPCB: C3351)
- **R1**: 10kΩ ±1% 0603 (JLCPCB: C25804)
- **R2**: 1kΩ ±1% 0603 (JLCPCB: C21190)

### U3: +15V → +7.5V Conversion (for +5V rail)

```
+15V ─────┬─── L2: 100µH ──┬─── D2 ──┬─── C4: 470µF ──┬─→ +7.5V/0.6A
          │    (4.5A)      │   SS34  │    (10V)       │
          │                │    ↓    │                │
          │           ┌────┴─────────┴──┐             │
          │           │5  VIN      OUT │4────────────┤
          └───────────┤3  ON        FB │2─────┬──────┘
                      │1  GND          │      │
                      └────────────────┘      │
                              │               │
                             GND          ┌───┴───┐
                                          │ R3    │ 5.1kΩ
                                          │ 5.1kΩ │
                                          └───┬───┘
                                          ┌───┴───┐
                                          │ R4    │ 1kΩ
                                          │ 1kΩ   │
                                          └───┬───┘
                                              │
                                             GND
```

**Output Voltage Calculation**:
```
Vout = 1.23V × (1 + R3/R4)
     = 1.23V × (1 + 5.1kΩ/1kΩ)
     = 1.23V × 6.1
     = 7.50V
```

**Component Values**:
- **L2**: 100µH, 4.5A Inductor (JLCPCB: C19268674)
- **D2**: SS34 Schottky Diode (JLCPCB: C8678)
- **C4**: 470µF/10V Electrolytic Capacitor (JLCPCB: C335982)
- **R3**: 5.1kΩ ±1% 0603 (JLCPCB: C23186)
- **R4**: 1kΩ ±1% 0603 (JLCPCB: C21190)

### U4: -15V → -13.5V Conversion (for -12V rail)

```
-15V ─────┬─── L3: 100µH ──┬─── D3 ──┬─── C7: 470µF ──┬─→ -13.5V/0.9A
          │    (4.5A)      │   SS34  │    (25V)       │
          │                │    ↓    │                │
          │           ┌────┴─────────┴──┐             │
          │           │5  VIN      OUT │4────────────┤
          └───────────┤3  ON        FB │2─────┬──────┘
                      │1  GND          │      │
                      └────────────────┘      │
                              │               │
                             GND          ┌───┴───┐
                                          │ R5    │ 10kΩ
                                          │ 10kΩ  │
                                          └───┬───┘
                                          ┌───┴───┐
                                          │ R6    │ 1kΩ
                                          │ 1kΩ   │
                                          └───┬───┘
                                              │
                                             GND
```

**Output Voltage**: -13.53V (same calculation as U2)

**Component Values**:
- **L3**: 100µH, 4.5A Inductor (JLCPCB: C19268674)
- **D3**: SS34 Schottky Diode (JLCPCB: C8678)
- **C7**: 470µF/25V Electrolytic Capacitor (JLCPCB: C3351)
- **R5**: 10kΩ ±1% 0603 (JLCPCB: C25804)
- **R6**: 1kΩ ±1% 0603 (JLCPCB: C21190)

## Design Considerations

### 1. Feedback Resistor Selection

The output voltage is determined by the following formula:

```
Vout = Vref × (1 + R_upper / R_lower)
```

Where Vref = 1.23V (internal reference voltage).

**Recommended Resistor Values**:
- R_lower: 1kΩ (fixed, optimizes feedback current)
- R_upper: Select based on desired output voltage

| Target Vout | R_upper | Actual Vout |
|-------------|---------|-------------|
| 3.3V | 1.7kΩ | 3.32V |
| 5V | 3.0kΩ | 4.92V |
| 7.5V | 5.1kΩ | 7.50V |
| 12V | 8.7kΩ | 12.01V |
| 13.5V | 10kΩ | 13.53V |

### 2. Inductor Selection

**Key Parameters**:
- **Inductance**: 100µH (recommended, selectable within 47µH-220µH range)
- **Saturation Current**: 1.5x or more of output current (4.5A or higher for this project)
- **DCR (DC Resistance)**: As low as possible (for improved efficiency)

**Selected Component for This Project**:
- CYA1265-100UH: 100µH, 4.5A saturation current, SMD power inductor
- JLCPCB: C19268674

### 3. Diode Selection

**Schottky Diode Required**:
- High-speed switching capability (150kHz)
- Low forward voltage drop (for improved efficiency)
- Current Rating: Equal to or greater than output current (3A for this project)
- Reverse Voltage: Equal to or greater than input voltage (40V or higher recommended)

**Selected Component for This Project**:
- SS34: 3A, 40V Schottky Diode
- JLCPCB: C8678 (Very High Stock: 1,859,655 units)

### 4. Capacitor Selection

**Input Capacitor** (Between VIN and GND):
- Electrolytic or ceramic capacitor
- Capacitance: 100µF or higher recommended
- Voltage Rating: 1.5x or more of input voltage

**Output Capacitor** (Between VOUT and GND):
- **Required**: Low ESR electrolytic capacitor
- Capacitance: 220µF - 1000µF (470µF for this project)
- ESR: 0.5Ω or less (for ripple reduction)
- Voltage Rating: 1.5x or more of output voltage

### 5. PCB Layout Guidelines

**Important Points**:
1. **Input loop**: Minimize the area of VIN - L - D - Cout loop
2. **Ground plane**: Ensure a continuous, wide GND plane
3. **Thermal relief**: Connect TO-263 package tab directly to GND plane
4. **FB trace**: Keep feedback trace short and away from noise sources
5. **Via placement**: Place multiple thermal vias (for enhanced heat dissipation)

**Recommended Trace Widths**:
- VIN, VOUT: 2mm or wider (for 3A current handling)
- GND: As wide as possible (plane recommended)
- FB: 0.2mm-0.3mm (thin and short)

### 6. Efficiency Optimization

**Factors Affecting Efficiency**:
- **Inductor DCR**: Lower is better
- **Diode Vf**: Lower is better (Schottky recommended)
- **Output capacitor ESR**: Lower is better
- **Input-Output voltage difference**: Smaller difference yields higher efficiency

**Efficiency Estimates for This Project**:
- U2 (15V→13.5V): ~88% (High efficiency due to small voltage difference)
- U3 (15V→7.5V): ~85% (Moderate voltage difference)
- U4 (-15V→-13.5V): ~88% (Equivalent efficiency for negative voltage)

### 7. Thermal Considerations

**Heat Dissipation Calculation Example** (U2: 15V→13.5V, 1.3A):
```
Power dissipation = (Vin - Vout) × Iout × (1 - Efficiency)
                  ≈ (15V - 13.5V) × 1.3A × 0.12
                  ≈ 0.23W
```

TO-263 package thermal resistance: ~40°C/W (when mounted on PCB)
Temperature rise: 0.23W × 40°C/W ≈ 9°C

**Conclusion**: No heatsink required (natural convection cooling is sufficient)

## JLCPCB Information

- **Part Number**: [C347423](https://jlcpcb.com/partdetail/347423-LM2596S_ADJ_UMW)
- **Manufacturer P/N**: LM2596S-ADJ(UMW)
- **Manufacturer**: UMW (Youtai Semiconductor)
- **Stock Availability**: 12,075 units
- **Package**: TO-263-5
- **Price**: $0.266 (as of December 2024)

**Note**: The UMW version is a compatible replacement for the Texas Instruments LM2596S-ADJ. Electrical characteristics are equivalent, and the price is significantly lower.

## External Resources

- [JLCPCB Part Page](https://jlcpcb.com/partdetail/347423-LM2596S_ADJ_UMW) - Official part page
- [Texas Instruments LM2596 Datasheet](https://www.ti.com/product/LM2596) - Original datasheet
- [SIMPLE SWITCHER Design Tools](https://www.ti.com/design-resources/design-tools-simulation.html) - TI official design tools

## Notes

- The LM2596S-ADJ is a very common DC-DC converter, and many compatible parts exist
- The 150kHz switching frequency avoids audible noise (below 20kHz)
- Connecting the ON/OFF pin to VIN enables always-on operation; connecting to GND activates shutdown mode
- This project uses the always-on configuration
- Feedback resistors with ±1% tolerance are recommended (directly affects output voltage accuracy)
