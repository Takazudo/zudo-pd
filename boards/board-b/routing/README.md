# Corner-support routing

The active PCB is 110 × 85 mm. J5 is on the front at (37.2,24.9), 270 degrees.
Board P faces Board B with P(x,y) mapping to B(y−0.5,x+12); its nominal CAD face plane is
11.1 mm above B. In the installed orientation B faces down on legs and its back
silkscreen is visible from above. Nominal CAD spacing is not a qualified spacer.

P projects to x=−0.5–39.5 mm, y=12–39 mm, freeing the independent top-left support.
Its three Ø3.2 mm holes are H1(3.5,16), H2(3.5,35) and H3(32.1,24.8).
The four independent HC-11 Ø3.0 mm corner holes are H4(106,4), H5(4,81),
H6(106,81) and H7(4,4). Keep those interfaces separate.

C5 moves to (18,6), 0°; C46 to (28,6.5), 180°; C32 to (26,22), 0°;
R3 to (26,29), 180°; R4 to (26,26), 90°; and D2 to (33.75,35), 90°.
The complete seven-contact pogo row moves 20 mm right: P1 center (60,1.8),
TP3/TP4/TP5 at (66.35,1.8)/(68.89,1.8)/(71.43,1.8). Its voltage legend is
centered at (88,2). Preserve all electrical assignments and both-side terminal labels.

The active `../board-b.kicad_pcb` is the layout source. Current placement rules
are in `scripts/pcb/board_b_layout.py`; do not reconstruct the PCB from a
superseded migration input or route session.
Input paths use 1.5 mm traces; measurement and status branches use 0.25 mm.
Load outputs retain the 1 mm screen. Measurement branches are excluded from
current-path proofs. Existing ground pours remain; affected old ground branches
are removed so the filled planes reconnect their pads. All existing ground,
thermal, connectivity and current-path checks still apply.

Copy the active `.kicad_pro` beside a temporary PCB after generation, because a
native pcbnew save can reset project defaults. Refill and check the candidate,
then promote only after native DRC and mechanical/power checks pass. Run parity
against the actual matching schematic and project. Use `configure-board-b.py`
after native project changes to restore the reviewed routing/manufacturing rules.

For a fresh route, `place-board-b.py` generates current placement,
`prepare-routing.py` applies explicit net classes, and `finish-board-b.py`
imports the new session and adds pours. Do not apply a prior session's special
completion paths. Every new route requires native and geometry checks.

Only the latest PCB and its current workflow are maintained. The PCB is implemented and native layout
and power-path checks pass. Package reports determine CAD and export status; the
destination is `manufacturing/releases/corner-support-review/`. This is a prototype
review package, not a released product or submitted order.

HC-11's 11 mm height does not clear the front-down assembly over a flat floor.
P's back substrate reaches 12.7 mm and the terminal drawing maximum is 14.2 mm.
The [support evidence](../supports/README.md) records that earlier option's height
and head/base envelope limits. The separately developed
[18 mm printed leg](../../../3dp-files/adhesive-leg/README.md) addresses the nominal
height conflict without changing the PCB or routing. Its own CAD verification and
physical fit checks are separate from the HC-11 support-option evidence.
