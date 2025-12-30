---
sidebar_position: 1
---

# Learning Notes

Electronics concepts and circuit design lessons learned while building this USB-PD power supply project.

## About This Section

This section contains technical explanations, design decisions, and circuit theory concepts discovered during the development of this modular synthesizer power supply. Each entry documents a specific learning moment or circuit behavior that helped improve the design.

## Topics Covered

### Digital Logic & Control
- [Open-Drain Outputs: Understanding the PG Pin](./open-drain-pg-pin.md) - How the CH224D's Power Good pin works and why LEDs connect the way they do

### Power Supply Design
- [How Buck Converters Work: Feedback Control Explained](./buck-converter-feedback.md) - Understanding the LM2596S-ADJ feedback mechanism and why it's like an op-amp
- Coming soon: Linear regulator input/output capacitor selection
- Coming soon: Protection circuit staged design

### Component Selection
- Coming soon: Why TVS diodes vs Zener diodes
- Coming soon: PTC vs glass fuses for overcurrent protection

---

These notes are written as I learn about hardware design. If you find errors or have better explanations, please feel free to suggest improvements!
