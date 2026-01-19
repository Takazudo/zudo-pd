---
sidebar_position: 2
slug: project-overview
---

# Project Overview

A compact power supply module that provides ±12V/+5V power for modular synthesizers using USB-C PD 15V as input.

## Design Goals

### Output Specifications

- **+12V**: 1500mA max (L7812CD2T-TR)
- **-12V**: 1000mA max (CJ7912)
- **+5V**: 1500mA max (L7805ABD2T-TR)

### Input

- **USB-C PD 15V 3A** (max 45W)

### Performance Characteristics

- **Efficiency**: Approx. 75-80% (overall)
- **Ripple Noise**: &lt;1mVp-p (final output)
- **Regulation**: ±1% (line & load variation)
- **Response Speed**: Excellent (due to linear stage)
- **Safety Margin**: 150%+ across all circuits

## Architecture

### 4-Stage Design

This project adopts a 4-stage architecture to achieve efficient power conversion while minimizing noise.

```
USB-C 15V ──┬─→ +13.5V (DC-DC) ──→ +12V (LDO) ──→ +12V OUT
            │
            ├─→ +7.5V  (DC-DC) ──→ +5V  (LDO) ──→ +5V OUT
            │
            └─→ -15V (Inverter) ──→ -13.5V (DC-DC) ──→ -12V (LDO) ──→ -12V OUT
```

#### Stage 1: USB-PD Power Delivery

- **STUSB4500 IC**: USB-IF certified USB-C PD protocol negotiation
- **15V Output**: Obtains stable 15V through PD negotiation
- **Load Switch**: AO3401A P-MOSFET enables power after successful negotiation

#### Stage 2: DC-DC Converter

- **LM2596S-ADJ × 3**: High-efficiency buck converter
  - +15V → +13.5V (for +12V rail)
  - +15V → +7.5V (for +5V rail)
  - -15V → -13.5V (for -12V rail)
- **LM2586SX-ADJ**: Inverted SEPIC converter (+15V → -15V, 3A capable)
- **Efficiency**: Approx. 85-90%

#### Stage 3: Linear Regulator

- **LM7812**: +13.5V → +12V (noise reduction)
- **LM7805**: +7.5V → +5V (noise reduction)
- **LM7912**: -13.5V → -12V (noise reduction)
- **Ripple**: &lt;1mVp-p

#### Stage 4: Protection Circuit (Beginner-Friendly, 2-Level Protection)

- **PTC Resettable Fuse**: Auto-recovery during overload
- **SMD Fuse**: Backup protection during short circuit
- **TVS Diode**: Surge voltage protection
- **LED Indicator**: Status display for each voltage line

## Design Features

### 1. All Parts Available from JLCPCB

- **Extensive Basic Parts Usage**: No additional costs
- **Rich Inventory**: From minimum 2,763 to maximum 21 million units
- **Stable Sourcing**: Stable supply chain

### 2. High-Performance Design

- **2-Stage Filter**: DC-DC + Linear for low noise
- **Sufficient Margin**: 150%+ safety margin across all circuits
- **Modular Synth Optimized**: Low noise, high stability

### 3. Beginner-Friendly Protection Circuit

- **PTC Auto-Recovery**: Recovers in 30 seconds even with excessive module connections
- **Staged Protection**: Overload → PTC, Short circuit → Fuse
- **Visual Feedback**: Instantly recognize overload by LED extinguishing
- **No Repair Needed**: Users can resolve normal overloads themselves

### 4. Manufacturability

- **All SMD Components**: Compatible with automated assembly
- **TO-220 Package**: Easy heatsink mounting
- **Separated Design**: Physical separation of DC-DC and linear stages

## Protection Circuit Operation

### Normal Operation

- PTC has zero resistance
- LED lights brightly ✅

### Overload (1.2-2A)

- PTC becomes high resistance
- LED extinguishes
- Reduce modules and wait 30 seconds
- Auto-recovery 🔄

### Short Circuit (>2A)

- Fuse blows
- Repair required ❌

## Next Steps

1. **Finalize Unsearched Components**:
   - PTC Resettable Fuse (1.1A, 0.75A, 0.9A @ 16V)
   - 2A SMD Fuse (+12V backup)

2. **PCB Design**:
   - 4-layer PCB (power plane separation)
   - Thermal via placement
   - EMI countermeasure layout

3. **Prototype Manufacturing**:
   - Use JLCPCB SMT service
   - Initial lot of approximately 10 units

4. **Performance Verification**:
   - Ripple noise measurement
   - Load response characteristics
   - Thermal design verification
