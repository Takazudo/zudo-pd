---
name: component-high-diode-smaj20a-c571370
description: Audit the exact High Diode SMAJ20A C571370 TVS used on Boards P and L. Use for surge protection, polarity, standoff, breakdown, clamp waveform, leakage, package, thermal, bring-up, or substitution.
---

# Exact High Diode SMAJ20A

Run the central validator and read every local artifact. Reject SMAJ20A tables from Littelfuse, Diodes Incorporated, Taiwan Semiconductor, or any other vendor. The official High Diode table confirms 20 V standoff, 22.2–24.5 V breakdown, the conditioned 32.4 V clamp row, leakage, 400 W pulse rating, temperature range, package and cathode band; the stable distributor mirror binds C571370. Keep each waveform condition attached and do not mix superseded or other-vendor tables.

The current project maps pad 1 as cathode on VBUS and pad 2 as anode on GND. Treat that as a static project assertion, not as-built proof. Confirm the D5 and D10 incoming marking, numeric pad mapping, orientation and continuity; simulate both rails with actual source impedance/parasitics and capture the real transient waveforms before production or substitution.

## Human component reference

Human projection of this bundle: [rec-high-diode-smaj20a](/docs/components/records/high-diode-smaj20a/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
