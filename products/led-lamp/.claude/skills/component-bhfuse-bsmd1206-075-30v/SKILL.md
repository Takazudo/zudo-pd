---
name: component-bhfuse-bsmd1206-075-30v
description: Audit the exact BHFUSE BSMD1206-075-30V resettable input PPTC on Board L. Use for C976305/F1 identity, hold/trip behavior, V15 input protection, time-current response, ambient derating, resistance, cycling/reset, package, layout, substitution, fault analysis, or bring-up.
---

# BSMD1206-075-30V input-PPTC audit

Run the central offline validator and read every local JSON file. Resolve the exact `BSMD1206-075-30V`/`C976305`; do not borrow behavior from another BSMD1206 current or voltage suffix.

Keep hold current, trip current, maximum voltage/current, and average time-current curves conditioned. A PPTC is thermal and resettable, not a precision fuse or switch. Account for ambient derating, one-hour hold wording, resistance after trip/reflow, repeated-trip degradation, local heat sources, processing history, fault source impedance, and cooling before declaring protection behavior.

Report source/fact IDs, locators, conditions, and one frozen verdict. Tie F1.1=VBUS_L and F1.2=V15 to the generator without treating the V15 net name as a transient bound. Load the integration skill for upstream PD/harness fault energy or downstream converter load; do not silently change the design.

## Human component reference

Human projection of this bundle: [rec-bsmd1206-075-30v](/docs/components/records/bsmd1206-075-30v/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
