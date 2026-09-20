---
title: JLCPCB Package Preparation
sidebar_position: 2
---

The [corner-support review destination](https://github.com/Takazudo/zudo-pd/tree/main/manufacturing/releases/corner-support-review) tracks the
110 × 85 mm Board B with four independent corner holes, the shifted front-side
PD stack and seven contacts moved right along the top edge. The PCB is implemented;
native layout and power-path checks pass. Package reports determine CAD and export status.
Read the [manufacturing guide](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md) alongside the package's check reports, assembly drawings and
BOM/CPL tables. Physical wire fit, tightening torque, leg clearance, connector
seating and full-load qualifications remain open. The separately developed 18 mm
printed leg addresses the earlier HC-11 option's nominal height conflict without
changing the PCB or package. Check the
[support contract](../architecture/board-contract.md#independent-corner-supports),
including actual M3 passage through the existing Ø3.0 mm PCB holes.
Earlier release packages belong
to different geometry.

Export each board independently from its final KiCad project. Retain validation
reports and exports in a revision-specific release directory. Record source revision,
board dimensions and tool versions.

| File | Review |
| --- | --- |
| Gerber ZIP | Copper, mask, silkscreen and Edge.Cuts for the intended stack |
| Drill data | Plated/non-plated holes, units and origin |
| BOM CSV | References, values, footprints, exact LCSC codes; DNP omitted |
| CPL CSV | References, X/Y, rotation and side; DNP omitted |
| ERC/DRC reports | Errors resolved or accepted exclusions documented |
| Release manifest | Revision, dimensions, assembly scope and blockers |

## Reconcile the package

BOM and CPL must cover the same fitted assembly scope. Through-hole connectors need
an explicit assembly decision; a stock listing alone does not establish standard
SMT assembly coverage. Review pin 1, key orientation and component rotations against
the PCB in the order preview.

Inspect Gerber and drill views independently of the PCB editor. Confirm outline,
mounting-hole centers, plated/non-plated classification and mating-cable clearance.
The four corner holes are Ø3.0 mm NPTH, distinct from the three Ø3.2 mm PD mounts.
Keep separately installed adhesive supports outside the electrical BOM and CPL.
The C4749189 connectors replace the old printed-guard requirement; the historical
guard-shaped outline is not the new mechanical specification.

J6/J7 now use two-pole screw-terminal blocks with wire entries facing left. Check
J6.1=GND, J6.2=−12 V, J7.1=+5 V and J7.2=+12 V in both the schematic and assembly
preview. Confirm both the retained front voltage labels and normally readable back
labels against those pins. Check the front-down installation and front-side J5
stack in the assembly preview. The current left edge is plain. The
[old printed accessories](https://github.com/Takazudo/zudo-pd/blob/main/3dp-files/README.md)
and their notch contract remain archived and are not assembly requirements.

A package can exist while its design still has blockers. Its manifest must list
those blockers and must not label it ready to order until the
[release gates](../architecture/release-readiness.md) are closed.

After an order is placed, retain exactly the submitted files in
`jlcpcb-order-snapshots/` and advance the order counter through the versioning
workflow. Preparing files alone does not count as a PCBA order.

## Repository export and independent rendering

Preserve the existing review package. To regenerate, run the gated exporter from
the repository root with a new output directory, for example:

```sh
python3 scripts/pcb/export-jlcpcb.py manufacturing/releases/corner-support-next-review --boards board-p board-b
uv run --with gerbonara --with resvg-py python scripts/pcb/verify-jlcpcb.py manufacturing/releases/corner-support-next-review
```

The exporter checks ERC, DRC and schematic/PCB parity. Inspect its reports and
the [manufacturing guide](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md) for actual release status. The independent rendering step
checks the manufactured layer files separately from KiCad. Both commands operate
on local files and do not submit an order.
