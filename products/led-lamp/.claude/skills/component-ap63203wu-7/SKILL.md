---
name: component-ap63203wu-7
description: Audit the exact AP63203WU-7 3.3 V synchronous buck and its FNR4030S4R7MT inductor and CL21A226MAQNNNE output capacitors. Use for Board L V3P3 startup, EN-open behavior, pins, switching/fault timing, L/C stability, thermal/layout work, substitutions, or calculations involving C780769, C167874, or C45783.
---

# AP63203WU-7 logic-buck audit

Run the central offline validator and read every local JSON file. Resolve AP63203WU-7, FNR4030S4R7MT, and CL21A226MAQNNNE independently by exact MPN/LCSC; do not use a nearby AP6320x variant or generic 4.7 uH/22 uF part as evidence.

Keep 32 V recommended VIN, 35 V DC stress, and 40 V/400 ms transient distinct. Treat EN open as an intentional automatic-start state. Preserve uncertainty around minimum off-time, effective MLCC capacitance, switch-node behavior, and board thermal performance. The locked Samsung PDF confirms that Class II capacitance changes under DC voltage but gives no exact 3.3 V effective-capacitance value; never infer a guaranteed PASS from nominal capacitance.

FNR4030S4R7MT's identity, inductance, tolerance, DCR max, SRF min, Isat max, Irms max, temperature, and package are now `PASS - primary-source confirmed` from a direct cjiang.com.cn retrieval (2026-08-02) that exactly matched the retained mirror on every electrical parameter. This primary confirmation makes `fact-fnr-irated-margin` a firm finding, not a mirror guess: the FNR4030S4R7MT's own 2.0 A max-design heating-current rating is 0.7 A below the AP63203's 2.7 A full-load design target (35% headroom over 2 A). Actual Board L load, ripple, ambient, and airflow remain unresolved (`int-fnr-filter`, `int-ap63203-power-stage` both stay `NEEDS BENCH`) — do not treat this as a closed thermal-adequacy result, and do not treat it as reason to skip bench verification either way.

Report conditioned facts with IDs, source locks, locators, and frozen verdicts. Check fixed-output FB sensing, BST-SW decoupling, L/C envelope, current-limit/hiccup behavior, hot-loop layout, and generated nets before reasoning. Load the integration skill for rail startup, input protection, MCU load, or thermal interactions; do not modify design state from an audit result.

## Human component reference

Human projection of this bundle: [rec-ap63203wu-7](/docs/components/records/ap63203wu-7/), [rec-fnr4030s4r7mt](/docs/components/records/fnr4030s4r7mt/), [rec-cl21a226maqnnne](/docs/components/records/cl21a226maqnnne/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
