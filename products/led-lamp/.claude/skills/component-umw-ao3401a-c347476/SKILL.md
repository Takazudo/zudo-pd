---
name: component-umw-ao3401a-c347476
description: Audit the exact UMW (Youtai Semiconductor) AO3401A C347476 P-channel load-switch MOSFET. Use for Board P Q1 identity, gate polarity, pinout, ratings, SOA, thermal behavior, bring-up, or substitution decisions.
---

# Exact UMW AO3401A

Run the central validator and read every local JSON artifact. Reject AO3401A data from Alpha & Omega or any other same-name vendor. Pin 1 is gate, pin 2 source, and pin 3 drain for this exact UMW document. Threshold voltage only describes the low-current onset test; use the documented RDS(on) drive conditions for conduction reasoning.

For Board P, verify source at VBUS_IN, drain at VBUS_OUT, and the gate never exceeds +/-12 V relative to source. The 150 kOhm drive path, 100 kOhm pull-up, capacitance, continuous load, transient inrush, body diode, SOA, and thermal rise require staged bench checks; package current headline values do not replace SOA/thermal analysis.

## Human component reference

Human projection of this bundle: [rec-umw-ao3401a](/docs/components/records/umw-ao3401a/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
