# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hardware project for designing a USB-PD powered modular synthesizer power supply that converts USB-C PD 15V to +12V/1.2A, -12V/0.8A, and +5V/0.5A outputs for modular synthesizers. The project uses a multi-stage design with DC-DC converters followed by linear regulators for low-noise output.

## Repository Structure

- `/notes/` - Organized documentation and specifications
  - `diagram.md` - Complete circuit diagrams for all stages
  - `parts.md` - Detailed parts list with JLCPCB part numbers and pricing
- `/generated-docs/` - Generated documentation (unorganized)
  - `complete-circuit-diagram.md` - Complete circuit implementation
  - `initial-idea.html` - HTML visualization of the circuit design
- `/footprints/` - PCB footprint files for components
  - `CH224Q.png` - Footprint for USB PD controller
  - `USB-TYPE-C-009.png` - Type-C connector footprint
- `/inbox/` - Working directory for temporary files

## Technical Architecture

The power supply uses a 4-stage architecture:

1. **USB-PD Stage**: CH224Q IC negotiates 15V from USB-C PD
2. **DC-DC Stage**: Multiple LM2596S-ADJ converters create intermediate voltages
   - +15V → +13.5V (for +12V rail)
   - +15V → +7.5V (for +5V rail)  
   - +15V → -15V (ICL7660 voltage inverter) → -13.5V (for -12V rail)
3. **Linear Regulator Stage**: LM78xx/LM79xx series for final low-noise outputs
   - LM7812: +13.5V → +12V
   - LM7805: +7.5V → +5V
   - LM7912: -13.5V → -12V
4. **Protection Stage**: Fuses and TVS diodes for overcurrent/overvoltage protection

## Key Design Features

- **Low-noise design**: DC-DC + Linear regulator combination for <1mVp-p ripple
- **JLCPCB compatibility**: All parts selected for JLCPCB SMT assembly
- **Safety margins**: 150%+ current capacity on all circuits
- **Modular synth optimized**: Voltage and current specifications match typical modular synthesizer requirements

## Documentation Language

All documentation is in Japanese. The project targets Japanese makers and uses Japanese component sourcing.

## File Types

- `.md` files contain technical specifications and circuit diagrams in text format
- `.html` files provide styled visualizations of the circuit design
- `.png` files are component footprint references
- No code compilation or testing is required - this is a hardware design project