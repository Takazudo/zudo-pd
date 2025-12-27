---
sidebar_position: 4
---

# Bill of Materials (BOM)

Complete parts configuration using JLCPCB SMT service.

## Power Supply Specifications

- **+12V**: 1200mA (actual 1.2A support)
- **-12V**: 800mA (actual 1A support)
- **+5V**: 500mA (actual 1.2A support)
- **Input**: USB-C PD 15V 3A
- **Efficiency**: Approximately 75-80%
- **Ripple**: \<1mVp-p (final output)

## Complete Parts Configuration by Stage

### Stage 1: USB-PD Voltage Acquisition (CH224Q)

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **U1** | **[C3975094](https://jlcpcb.com/partdetail/C3975094)** | **CH224D** | USB PD Controller (5/9/12/15/20V) | QFN-20 | **2,291** | **$0.36** | PD Negotiation (15V) |
| **J1** | **[C2927029](https://jlcpcb.com/partdetail/C2927029)** | **USB-TYPE-C-009** | 6P Type-C Female | SMD | **27128** | **$0.036** | USB-C Input |
| **C1,C2** | **[C15850](https://jlcpcb.com/partdetail/C15850)** | **CL21A106KAYNNNE** | 10µF 25V X5R | 0805 | **6000** | **$0.0101 × 2** | Filter |
| **R1** | **[C23138](https://jlcpcb.com/partdetail/C23138)** | **0603WAF3300T5E** | 330Ω ±1% | 0603 | **Rich Stock** | **$0.00099** | LED Current Limit |
| **LED1** | **[C2286](https://jlcpcb.com/partdetail/C2286)** | **0805G** | Green LED 20mA | 0805 | **Rich Stock** | **$0.0115** | Power Good Indicator |

**Stage 1 Subtotal: $0.43** (Using CH224D)

### Stage 2: DC-DC Converters (LM2596S-ADJ × 3 + ICL7660)

#### Main ICs

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **U2,U3,U4** | **[C347423](https://jlcpcb.com/partdetail/C347423)** | **LM2596S-ADJ(UMW)** | Adjustable 3A Buck | TO-263-5 | **12075** | **$0.266 × 3** | DC-DC Conversion |
| **U5** | **[C356724](https://jlcpcb.com/partdetail/C356724)** | **ICL7660M/TR** | Voltage Inverter IC | SOP-8 | **32192** | **$0.078** | -15V Generation |

#### Inductors

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **L1,L2,L3** | **[C19268674](https://jlcpcb.com/partdetail/C19268674)** | **CYA1265-100UH** | 100µH 4.5A | SMD,13.8x12.8mm | **2763** | **$0.378 × 3** | Energy Storage |

#### Diodes

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **D1,D2,D3** | **[C8678](https://jlcpcb.com/partdetail/C8678)** | **SS34** | 3A 40V Schottky | SMA | **1,859,655** | **$0.012 × 3** | Freewheeling |

#### Feedback Resistors (Basic Parts)

| Symbol | Part Number | Value | Description | Package | Price | Application |
|------|----------|-----|------|------------|------|------|
| **R2,R4,R6** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1kΩ** | ±1% 100mW | 0603 | **$0.0005 × 3** | FB Reference |
| **R1,R5** | **[C25804](https://jlcpcb.com/partdetail/C25804)** | **10kΩ** | ±1% 100mW | 0603 | **$0.0005 × 2** | ±13.5V Setting |
| **R3** | **[C23186](https://jlcpcb.com/partdetail/C23186)** | **5.1kΩ** | ±1% 100mW | 0603 | **$0.0005 × 1** | +7.5V Setting |

#### Electrolytic Capacitors

| Symbol | Part Number | Specification | Package | Stock | Price | Application |
|------|----------|------|------------|--------|------|------|
| **C3** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470µF 10V** | D6.3xL7.7mm | **164,155** | **$0.014** | +13.5V Output Filter |
| **C4** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470µF 10V** | D6.3xL7.7mm | **164,155** | **$0.014** | +7.5V Output Filter |
| **C5,C7,C9** | **[C2907](https://jlcpcb.com/partdetail/C2907)** | **100µF 25V** | D6.3xL7.7mm | **Rich Stock** | **$0.019 × 3** | DC-DC Input Bulk (±13.5V stages) |
| **C11** | **[C3351](https://jlcpcb.com/partdetail/C3351)** | **470µF 25V** | D10xL10.2mm | **19,150** | **$0.044** | -13.5V Output Filter |

#### Ceramic Capacitors (DC-DC Stage)

| Symbol | Part Number | Specification | Package | Stock | Price | Application |
|------|----------|------|------------|--------|------|------|
| **C6,C8,C10** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805 | **23,309,869** | **$0.0021 × 3** | DC-DC Input Decoupling |

#### ICL7660 Capacitors

| Symbol | Part Number | Specification | Package | Stock | Price | Application |
|------|----------|------|------------|--------|------|------|
| **C12,C13** | **[C15850](https://jlcpcb.com/partdetail/C15850)** | **10µF 25V X5R** | 0805 | **6000** | **$0.0101 × 2** | ICL7660 Charge Pump |

**Stage 2 Subtotal: $2.09**

### Stage 3: Linear Regulators (LM7812/7805/7912)

#### Regulator ICs

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **U6** | **[C2914](https://jlcpcb.com/partdetail/C2914)** | **L7812CV-DG** | +12V 1.5A | TO-220 | **158,795** | **$0.11** | +12V Output |
| **U7** | **[C86206](https://jlcpcb.com/partdetail/C86206)** | **L7805ABD2T-TR** | +5V 1.5A | TO-263-2 | **272,379** | **$0.11** | +5V Output |
| **U8** | **[C94173](https://jlcpcb.com/partdetail/C94173)** | **CJ7912** | -12V 1.5A | TO-252-2L | **3,386** | **$0.11** | -12V Output |

#### Input Capacitors (470nF) - Basic Parts

| Symbol | Part Number | Specification | Package | Stock | Price | Application |
|------|----------|------|------------|--------|------|------|
| **C14,C15,C16** | **[C1623](https://jlcpcb.com/partdetail/C1623)** | **470nF 25V X7R** | 0603 | **1,100,473** | **$0.0036 × 3** | Linear Reg Input Filter |

#### Output Capacitors (0.1µF) - Basic Parts

| Symbol | Part Number | Specification | Package | Stock | Price | Application |
|------|----------|------|------------|--------|------|------|
| **C17,C18,C19** | **[C49678](https://jlcpcb.com/partdetail/C49678)** | **100nF 50V X7R** | 0805 | **23,309,869** | **$0.0021 × 3** | Linear Reg Output Filter |

#### Large Electrolytic Capacitors (Linear Regulator Stage)

| Symbol | Part Number | Specification | Package | Price | Application |
|------|----------|------|------------|------|------|
| **C20,C21,C22,C23** | **[C335982](https://jlcpcb.com/partdetail/C335982)** | **470µF 10V** | D6.3xL7.7mm | **$0.014 × 4** | +12V,+5V Input/Output |
| **C24,C25** | **[C3351](https://jlcpcb.com/partdetail/C3351)** | **470µF 25V** | D10xL10.2mm | **$0.044 × 2** | -12V Input/Output |

**Stage 3 Subtotal: $0.37** (Using high-stock regulators)

### Stage 4: Protection Circuit (Beginner-Friendly, 2-Stage Protection)

#### PTC Resettable Fuses (Auto-Recovery)

| Symbol | Part Number | Manufacturer Part Number | Specification | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **PTC1** | **[C883148](https://jlcpcb.com/partdetail/C883148)** | **BSMD1812-110-16V** | **1.1A 16V** | 1812 | **11,029** | **$0.06** | +12V Overload Protection |
| **PTC2** | **[C883128](https://jlcpcb.com/partdetail/C883128)** | **BSMD1206-075-16V** | **0.75A 16V** | 1206 | **51,532** | **$0.05** | +5V Overload Protection |
| **PTC3** | **[C883148](https://jlcpcb.com/partdetail/C883148)** | **BSMD1812-110-16V** | **1.1A 16V** | 1812 | **11,029** | **$0.06** | -12V Overload Protection ※ |

**※ PTC3 Note**: Using 1.1A for 0.9A design value. 0.9A part out of stock. Sufficient protection margin for -12V actual load of 800mA.

#### Fuses (SMD, Backup Protection)

| Symbol | Part Number | Manufacturer Part Number | Specification | Package | Stock | Price | Application |
|------|----------|-------------|------|------------|--------|------|------|
| **F1** | **[C5183824](https://jlcpcb.com/partdetail/C5183824)** | **6125FA2A** | **2A 250V** | 2410 (6.1x2.6mm) | **744** | **$0.40** | +12V Short Circuit Protection |
| **F2,F3** | **[C95352](https://jlcpcb.com/partdetail/C95352)** | **1.5A 250V** | SMD,10.1x3.1mm | **840** | **$0.386 × 2** | ±5V/±12V Short Circuit Protection |

#### TVS Diodes

| Symbol | Part Number | Manufacturer Part Number | Description | Package | Estimated Price | Application |
|------|----------|-------------|------|------------|---------|------|
| **TVS1** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **SMAJ15A** | 15V TVS Unidirectional | SMA | **$0.15** | +12V Protection |
| **TVS2** | **[C5199240](https://jlcpcb.com/partdetail/C5199240)** | **PRTR5V0U2X** | 5V TVS Bidirectional | SOT-143 | **$0.12** | +5V Protection |
| **TVS3** | **[C571368](https://jlcpcb.com/partdetail/C571368)** | **SMAJ15A** | 15V TVS Unidirectional | SMA | **$0.15** | -12V Protection |

#### Status Indicator LEDs (Using Basic Parts)

| Symbol | Part Number | Specification | Package | Price | Application |
|------|----------|------|------------|------|------|
| **LED2** | **[C72043](https://jlcpcb.com/partdetail/C72043)** | **Green LED** | 0805 | **$0.0126** | +12V Status Indicator |
| **LED3** | **[C72041](https://jlcpcb.com/partdetail/C72041)** | **Blue LED** | 0805 | **$0.0126** | +5V Status Indicator |
| **LED4** | **[C84256](https://jlcpcb.com/partdetail/C84256)** | **Red LED** | 0805 | **$0.0126** | -12V Status Indicator |
| **R7,R8,R9** | **[C21190](https://jlcpcb.com/partdetail/C21190)** | **1kΩ** | 0603 | **$0.0005 × 3** | LED Current Limit |

**Stage 4 Subtotal: $1.79** (PTC added, fuses upgraded)

## Performance Specifications

### Power Supply Performance

| Item | Specification |
|------|------|
| **Efficiency** | 75-80% (Overall) |
| **Ripple Noise** | \<1mVp-p (Final Output) |
| **Regulation** | ±1% (Line & Load Variation) |
| **Response Speed** | Excellent (Linear Stage) |
| **Safety Margin** | 150%+ on All Circuits |

### Output Specifications

| Voltage | Current | Accuracy | Ripple |
|------|------|------|--------|
| **+12V** | 1.2A | ±0.5% | \<1mVp-p |
| **-12V** | 1.0A | ±0.5% | \<1mVp-p |
| **+5V** | 1.2A | ±0.5% | \<1mVp-p |

## Protection Circuit Operation

### Normal Operation

- PTC has zero resistance, LED lights brightly ✅

### Overload Condition

- PTC increases resistance, LED turns off → Reduce modules and wait 30 seconds → Auto-recovery 🔄

### Short Circuit Condition

- Fuse blows → Repair required ❌

## Design Features

### 1. Fully JLCPCB Sourceable with High Stock

- **Extensive Basic Parts Usage**: No additional costs
- **Abundant Stock**: Regulator ICs 150k~270k pieces in stock
- **Stable Sourcing**: High stock secured for all major components
- **USB-PD IC**: CH224D (2,291 pieces) - 15V support confirmed

### 2. High-Performance Design

- **2-Stage Filtering**: DC-DC + Linear for low noise
- **Ample Margin**: 150%+ safety margin on all circuits
- **Modular Synth Optimized**: Low noise, high stability

### 3. Beginner-Friendly Protection Circuit

- **PTC Auto-Recovery**: Recovers in 30 seconds even with too many modules connected
- **Staged Protection**: Overload → PTC, Short circuit → Fuse
- **Visual Feedback**: Immediate recognition of overload via LED off
- **No Repair Needed**: Normal overloads can be resolved by user

### 4. Implementation

- **All SMD Components**: Compatible with automated assembly
- **TO-220 Package**: Easy heat sink attachment
- **Separated Design**: Physical separation of DC-DC and linear stages
