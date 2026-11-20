---
name: component-alps-rk10j11e0034
description: Use to audit exact RK10J11E0034 C470643 stopped absolute brightness potentiometer, manufacturer evidence, JLCPCB sourcing, PCB pin mapping and prototype requirements.
---

# RK10J11E0034 stopped absolute brightness potentiometer

Run component-spec-audit first and read every JSON file in this owner. Use circuit-spec-integration for cross-component behavior. The exact part is fitted on Board L and sourced through JLCPCB; supplier stock is a dated observation, not a reservation or assembled-board proof.

RV1 uses single-unit Drawing No.1, not the imported dual-unit electrical map. Terminals 1/3 are ends and 2 is the wiper; all four MP pins are mechanically retained and electrically unconnected. The 270-degree stopped thumbwheel replaces the encoder: absolute position needs ADC sampling and endpoint/inversion calibration, not quadrature decoding. The catalog notation Insertion (t: 2 mm) does not independently prove a mandatory substrate thickness; the actual 1.6 mm PCB requires physical seating, retention and solderability validation. The manufacturer lists Manual soldering while JLCPCB offers Wave Soldering; resolve the permitted assembly process before fabrication. Firmware text describes targets, not flashed behavior.

## Human component reference

Generated [C470643 record](/docs/components/records/c470643/), [catalog](/docs/components/catalog/) and [integration](/docs/components/integration/). JSON evidence remains authoritative.
