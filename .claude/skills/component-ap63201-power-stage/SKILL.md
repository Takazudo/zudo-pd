---
name: component-ap63201-power-stage
description: Use when auditing exact AP63201WU-7 C2071044 synchronous buck, ASPI-0630LR-100M-T15 C1334133 inductor, GRM32ER71H106KA12L C77102 ceramic bank and precision feedback divider in Board B U2.
---

# Positive pre-regulator evidence

Load the exact record by MPN or LCSC in manifest.json; read sources, facts, pin maps,
coverage and interactions. Run component-spec-audit before relying on the inventory.
AP63201 is the adjustable 500 kHz forced-PWM member; do not substitute fixed-output
AP63203 or AP63205 using their family name. Pins are 1 FB, 2 EN, 3 VIN, 4 GND,
5 SW and 6 BST. This synchronous stage omits the old external catch diode D1 and
22 nF feedforward C31; the manufacturer's optional pF-range feedforward is not the
old LM2596 network.

Nominal pre-rail is 13.44 V. FB limits cover full -40..85 C; divider TCR must be
included. Near-100% duty and typical RDS(on) do not establish guaranteed dropout.
The Murata capacitance curve is a retained manufacturer mirror and explicitly
typical. The 27.54 uF bank calculation is a conservative project assumption, not
a guaranteed minimum; verify at operating voltage, temperature and load. Keep
low-line, thermal, inductor current, stability and transient domains open until
measured. Input/output ceramic banks and bootstrap require compact PCB loops.

## Human component reference

- [AP63201WU-7](/docs/components/records/ap63201wu-7/)
- [ASPI-0630LR-100M-T15](/docs/components/records/aspi-0630lr-100m-t15/)
- [GRM32ER71H106KA12L](/docs/components/records/grm32er71h106ka12l/)
- [RT0603BRE07158KL](/docs/components/records/rt0603bre07158kl/)
- [RT0603BRD0710KL](/docs/components/records/rt0603brd0710kl/)

See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/).

The ASPI-0630LR model is a project-generated maximum envelope (7.5 × 6.85 × 3.0 mm),
not exact manufacturer CAD. The official STEP link exists but returned HTTP 403
during this retrieval. The Rev C mechanical dimensions remain authoritative;
terminals, fillets and markings are unspecified in the visualization.
