---
name: component-tps26630rger
description: Use to audit exact TPS26630RGER C1850276 Board P input eFuse limits, UVLO/OVP/ILIM/dVdT configuration, latch mode, pins 1-25 and the unreviewed imported VQFN-24 footprint.
---

# TPS26630RGER input eFuse

Read all JSON files in this owner and run the central validator. Use circuit-spec-integration for the
whole 20 V input chain. TI SLVSE94G was retrieved and hashed on 2026-10-31; the PDF is not retained in the
repository. Only the tabulated R(ILIM) points have guaranteed I(OL) limits; 4.02 kOhm gives 4.185-4.815 A.
UVLO must not float, and UVLO to GND selects a 15 V internal threshold that would block a 5 V attach.
Board P uses no external blocking FET, so U2 does not block reverse current. The imported footprint is
unreviewed against the TI land drawing and its courtyard is undersized. Nothing here is measured.

## Human component reference

[TPS26630RGER](/docs/components/records/c1850276/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). The JSON bundle is authoritative.
