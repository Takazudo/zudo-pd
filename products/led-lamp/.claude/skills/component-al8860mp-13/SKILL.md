---
name: component-al8860mp-13
description: Audit the exact AL8860MP-13 LED-driver stage and its RLP25FEER200 sense resistor, FXL0630-330-M inductor, and R+O SS26 catch diode. Use for Board L LED current, CTRL/PWM behavior, pins, thermal/layout limits, faults, substitutions, bring-up, or power-stage calculations involving C500782, C459674, C177245, or C7420363.
---

# AL8860MP-13 power-stage audit

Run the central offline validator, then read every local JSON file. Resolve the standalone AL8860 and each subordinate by exact MPN or LCSC ID; never substitute another SS26 vendor or generic magnetic data.

Use facts as conditioned records, not headline ratings. Keep 40 V recommended VIN separate from 42 V absolute maximum. AL8860's identity/inductance/absolute-voltage/temperature/package/duty-band facts are `PASS - primary-source confirmed` from DS39014 (diodes.com, re-verified 2026-08-02). Cjiang FXL0630-330-M identity, inductance, tolerance, DCR max, absolute-maximum voltage, temperature, and package are likewise now `PASS` from a direct cjiang.com.cn retrieval (2026-08-02); its Isat/Irms max-design figures (2.1 A / 1.8 A) remain `UNSOURCED` mirror-only, since the primary document found shows only typical-labeled current columns. R+O SS26 stays fully mirror-only: a manufacturer-identification attempt reached the exact brand (Zhuhai Hongjiacheng Technology) but not an SS26-specific datasheet. Recompute current and power margins only from the listed raw fact IDs. Do not turn typical curves or unverified project LED voltage/temperature into a guaranteed PASS.

The AL8860's recommended analog/PWM duty-cycle range (DSW parameter) is 25-75%, guaranteed by design (`fact-al8860-duty-band`); do not confuse this with the 98% absolute-maximum duty cycle or the 5-100% CTRL-pin analog-dimming range.

For design or bring-up questions, report source IDs, fact IDs, locators, conditions, and one frozen verdict. Verify generated pin/net assertions, EP thermal handling, the SET resistor path, the hysteretic current loop, diode polarity, inductor peak/thermal current, CTRL state, and open/short behavior. Load the integration skill for cross-rail, LED-string, thermal, or firmware interactions; do not silently alter design state.

## Human component reference

Human projection of this bundle: [rec-al8860mp-13](/docs/components/records/al8860mp-13/), [rec-rlp25feer200](/docs/components/records/rlp25feer200/), [rec-fxl0630-330-m](/docs/components/records/fxl0630-330-m/), [rec-ro-ss26](/docs/components/records/ro-ss26/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
