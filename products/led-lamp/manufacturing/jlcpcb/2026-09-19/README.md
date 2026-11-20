# JLCPCB upload sets

Prepared for quoting and placement review; read ORDER-NOTES.md before checkout.

| Board | Gerber ZIP | BOM | CPL | Fitted parts |
| --- | --- | --- | --- | --- |
| board-p | [board-p-gerbers.zip](board-p/board-p-gerbers.zip) | [bom.csv](board-p/bom.csv) | [cpl.csv](board-p/cpl.csv) | 19 |
| board-l | [board-l-gerbers.zip](board-l/board-l-gerbers.zip) | [bom.csv](board-l/bom.csv) | [cpl.csv](board-l/cpl.csv) | 67 |
| swd-adapter | [swd-adapter-gerbers.zip](swd-adapter/swd-adapter-gerbers.zip) | [bom.csv](swd-adapter/bom.csv) | [cpl.csv](swd-adapter/cpl.csv) | 2 |

All intended fitted components, including all connector headers, are requested
for JLCPCB soldering. Intentional Board P DNP options remain excluded.

RV1 CPL rotation is corrected from 0 to 180 degrees, matching the user-adjusted
JLCPCB bottom preview on 2026-09-19. Do not apply that correction a second time.

Board L RV1: confirm manufacturer-compatible soldering and 1.6 mm board seating
with JLCPCB. Stock and their placement preview still need checkout review.

Checks: no DRC/ERC errors; no unrouted connections; BOM/CPL identities and
population match; Gerber/drill ZIPs independently parsed and rendered.
Existing DRC/ERC warnings are retained under each board/checks directory.
