---
title: Release Readiness
sidebar_position: 4
description: What the design files establish and what must be closed before a prototype order.
---

The renewed boards are development hardware prepared for **prototype
fabrication and assembly review**. Board B's screw-terminal revision retains
110 × 85 mm, two copper layers and 2 oz outer copper. Two top-side
WJ500V-5.08-2P / C8465 blocks replace the Fastons; their wire entries face left.
The left edge is plain and no printed terminal guard is required. Board B is
installed front-down on legs. Front-side J5 carries the face-down PD module above
B in CAD and physically below B when installed. P's own 27 × 40 mm PCB is unchanged.
Voltage labels appear on both sides and must read normally from each side.
P moves down to free the independent top-left corner support. P1 and TP3/TP4/TP5
move 20 mm right together, retaining seven top-edge contacts on 2.54 mm pitch.

The PCB is implemented and native layout and power-path checks pass. Package
reports determine CAD and export status. Required reports check input/output
power paths, thermal vias, copper-polygon connectivity,
specified ground stitches and modeled assembly clearance against the recorded revision. Aggregate sampled copper
width is distinct from the largest individual run; it does not describe one
continuous corridor. Geometry cannot establish current capacity, wire termination,
cooling or full-load output performance. Physical wire fit, tightening torque,
support retention and connector seating also remain unmeasured.

The selected [18 mm printed adhesive-leg prototype](https://github.com/Takazudo/zudo-pd/blob/main/3dp-files/adhesive-leg/README.md)
addresses the earlier HC-11 option's nominal height conflict: P's back substrate
plane reaches 12.7 mm and the terminal drawing maximum is 14.2 mm. The PCB remains
unchanged, including its Ø3.0 mm corner holes. M3 screw passage has zero nominal
diametral clearance and needs an actual fit check. Printed fit, screw retention,
adhesive loading and temperature behavior remain unqualified; see the
[support contract](./board-contract.md#independent-corner-supports). The HC-11
support record documents that option's limitations; the leg has separate CAD verification.

Use the [manufacturing guide](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md) and
[corner-support review destination](https://github.com/Takazudo/zudo-pd/tree/main/manufacturing/releases/corner-support-review) for source snapshots,
BOM/CPL scope, drawings and check reports. Local paths are `manufacturing/README.md`
and `manufacturing/releases/corner-support-review/`. Package reports determine final ERC,
DRC and fabrication-file status. Maintain only this current prototype package and
the active design files. No renewal hardware has been released or ordered; the
directory name `releases` does not establish product-release status.

The [STEP datum audit](https://github.com/Takazudo/zudo-pd/blob/main/footprints/kicad/step-datum-verification.json) covers the reviewed active STEP/WRL pairs.
Its sampled surface checks establish model consistency, with the documented BD8
interior-face exception; they do not establish exact physical geometry or mating
fit. The [manufacturing guide](https://github.com/Takazudo/zudo-pd/blob/main/manufacturing/README.md#native-3d-review)
gives the read-only replay command. Refresh the active model set when a component
changes instead of relying on a prior revision's report.

Board P's new 16 V TVS makes factory 20 V operation unsafe. Follow the mandatory
[configuration and input-protection procedure](./board-p.md) before first PD use.
The 26 V clamp screen and 60 V D3 improve the prototype's conditioned stress margin;
hot, installed surge and overshoot behavior remain unqualified.

## The selected power stage requires qualification

The output targets remain +12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A. The
selected chain now uses AP63201, LT1963A and adjustable LT3015 parts to address the old
regulator-headroom constraints. The schematic, catalog and layout must describe
those same selections. Selection research is retained in
[Power Stage Options](./power-stage-options.md).

## Order gates

| Gate | Required evidence |
| --- | --- |
| Exact parts | Strict inventory, pin-map and generator parity checks pass |
| Electrical rules | ERC reviewed; exclusions have specific reasons |
| PCB connectivity | Layout matches final schematic; no unresolved airwires |
| PCB geometry | DRC reviewed; closed outline; mounting and connector clearance checked |
| Corner supports | Printed-leg fit; M3 passage through Ø3.0 mm holes; screw/adhesive retention; 116 × 91 mm base footprint and actual enclosure clearance |
| Power layout | Converter loops, return paths, trace/via current and cooling reviewed |
| Input compatibility | First programming at 5 V only; NVM readback disables 20 V and confirms the 15 V-only policy; current path, pinout and startup documented |
| Manufacturing files | Gerbers, drills, BOM and CPL from one final revision |
| Assembly | DNP, side, rotation and through-hole assembly scope checked |
| Prototype tests | Staged bring-up and load, thermal and ripple measurement procedure |

The [integration records](/docs/components/integration/) identify unresolved
arithmetic and evidence. Headroom calculations are conditioned on source/path voltage, temperature and
ripple assumptions. A clean DRC cannot prove the output targets are achievable.

The root PCB and `jlcpcb-order-snapshots/` are historical order artifacts. Do not
mix their Gerbers or assembly tables with renewed board files.

See [JLCPCB package preparation](../how-to/jlcpcb-package.md) for file-level review.
Every package must state its blockers instead of presenting a partial layout as
ready to order.
