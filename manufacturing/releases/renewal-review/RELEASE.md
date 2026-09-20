# Renewal prototype fabrication package

The output targets remain **+12 V / 1.2 A, −12 V / 0.8 A and +5 V / 0.5 A**.
These are prototype targets; assembled performance is not yet qualified.

Use each board’s files together as a separate fabrication/assembly job.

| Board | Fabrication | Assembly | Review |
| --- | --- | --- | --- |
| P: 27 × 40 mm, 2 layers, 1.6 mm, 1 oz | [Gerber/drill ZIP](board-p/board-p-gerbers.zip) | [BOM](board-p/bom.csv) · [CPL](board-p/cpl.csv) | [Schematic](board-p/schematic.pdf) · [Top](board-p/gerber-top.png) · [Bottom](board-p/gerber-bottom.png) |
| B: 150 × 115 mm, 2 layers, 1.6 mm, 2 oz | [Gerber/drill ZIP](board-b/board-b-gerbers.zip) | [BOM](board-b/bom.csv) · [CPL](board-b/cpl.csv) | [Schematic](board-b/schematic.pdf) · [Top](board-b/gerber-top.png) · [Bottom](board-b/gerber-bottom.png) |

Board P has 19 fitted parts / 14 BOM lines. Board B has 74 fitted parts / 39 BOM lines;
J5 is on the bottom. Bare copper and DNP exclusions are listed per board.

Both boards pass native ERC/DRC with **zero errors and zero unrouted connections**.
Warnings remain documented in each board’s checks folder. Board B’s exact socket,
mating-hole and power-path checks pass. Independent Gerber/drill, identity,
coordinate and checksum checks pass, as do the three negative integrity cases.

Read [order and assembly notes](ORDER-NOTES.md) before using these files.
**First power and programming must be 5 V only, with Board B disconnected. Verify
15 V-only NVM settings and readback before connecting a PD-capable source. Never
request 20 V with the revised 16 V TVS.**

Exact-part JLCPCB placement/orientation and through-hole assembly review, physical
stack/cable fit, and full-load startup, ripple, thermal and surge qualification
remain open. The [power budget](power-budget.md) distinguishes conditioned
calculations from measured capability.

[Independent validation](independent-validation.json) · [Negative checks](negative-validation.json) · [Source/artifact manifest](manifest.json) · [Checksums](SHA256SUMS)
