---
name: component-murata-ncp18xh103f03rb
description: Resolve the exact Murata NCP18XH103F03RB NTC used on Board L. Use for nominal resistance, beta context, divider topology, ADC interpretation, self-heating, thermal response, lifecycle, and temperature-threshold questions.
---

# Murata NCP18XH103F03RB

Run the central validator and read all local JSON before using this record. Murata's current primary part list confirms exact identity, NRND status, 10 kOhm nominal resistance, B-value context, and a 0.1 mA maximum **operating** current (Murata's own column header is "Maximum Operating Current (25 C)"; it is an installed-current ceiling, not a measurement/test condition).

Do not convert the 3380 K beta value into a guaranteed full resistance-temperature table. Exact full R-T tolerance, installed self-heating/dissipation, thermal time constant, placement response, and firmware thresholds stay open and require further primary data or measurement.

Board L places RT1 from NTC_SENSE to ground, with R26 (100 kOhm, C25803) pulling up to V3P3 and C24 shunting the sense node. This establishes divider topology only. ADC code-to-temperature behavior still depends on the exact pull-up, supply/reference, sampling time, tolerances, self-heating, airflow, PCB coupling, conversion algorithm, and threshold policy.

## Human component reference

Human projection of this bundle: [rec-c13564](/docs/components/records/c13564/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
