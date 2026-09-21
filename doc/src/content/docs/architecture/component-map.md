---
title: Component Map
sidebar_position: 3
description: Find each circuit function in the exact component inventory and generated catalog.
---

The [catalog](/docs/components/catalog/) lists exact fitted and DNP placements,
order codes, source availability and open evidence domains. It is generated from
records checked against schematic specs.

| Circuit function | Existing selection | Review focus |
| --- | --- | --- |
| USB-PD controller | STUSB4500QTR | NVM, CC connections, sense and enable behavior |
| Board P input TVS | SMAJ16A / C74561 | Mandatory 15 V-only NVM; conditioned clamp, hot behavior and overshoot |
| Input switch | UMW AO3401A | Gate clamp, startup and dissipation |
| +12 V pre-regulator | AP63201WU-7 / C2071044 | Low-line regulation, ceramic-bank assumptions and switching layout |
| +5 V and negative pre-regulators | LM2596S-ADJ | Buck and inverting-stage stress at actual load |
| +12 V buck inductor | ASPI-0630LR-100M-T15 / C1334133, 10 µH | Typical current ratings, ripple and temperature |
| Other converter inductors | CYA1265 100 µH selection | Saturation, RMS current and temperature |
| U3 catch diode D2 | SS34 | Reverse voltage, peak/RMS current and heat |
| U4 catch diode D3 | SDT5A60SA-13 / C3024223, 60 V | Conditioned reverse stress, leakage, current and heat |
| +12 V regulator | LT1963AEQ#PBF / C107286 | Divider tolerance, dropout and thermal conditions |
| +5 V regulator | LT1963AEQ#PBF / C107286 | Divider tolerance, guaranteed headroom and dissipation |
| −12 V regulator | LT3015EQ-12#PBF / C666307 | Corrected exact pin map, headroom and heat |
| Linear output capacitors | Panasonic 25SVPF47M / C136280 | Capacitance, ESR and polarity at the actual regulator pins |
| Output protection | Per-rail PTC and TVS | Derating and regulator/PTC/TVS coordination |
| Synth connectors | DW254P-2X8-L0 / C4749189 | Pin map, key orientation and cable clearance |
| Screw-terminal blocks | [WJ500V-5.08-2P / C8465](/docs/components/records/c8465/) at J6/J7 | Exact pin map, left-facing wire entries and physical termination |
| Passives | Exact catalog records | Orderable identity and per-placement fit state |

The protection circuit has PTCs and TVS diodes. It does not include the backup fuse
suggested in early notes. Combined regulator, PTC and TVS behavior must be reviewed
before claiming sustained-fault protection.

## Evidence stays with the exact component

Records distinguish manufacturer facts, project connectivity and calculations.
An unavailable source stays unavailable; a candidate is not a fitted BOM line;
DNP belongs to a placement. Read a fact's source revision, locator and conditions.

Use the [component-first workflow](../how-to/component-first-design.md) to add or
replace parts. The generated catalog is never edited by hand.
