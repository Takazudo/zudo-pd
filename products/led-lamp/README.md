# zudo-led-lamp

USB-PD powered LED lamp with fire/wave-like brightness modulation.

Docs: https://zudo-led-lamp.takazudomodular.com/

## Current build path

The current path is zudo-pd **P15 r1** (27 × 40 mm, 3 A NVM image) with the two existing
Board Ls, decided 2026-11-03. The two Board Ls already exist; the P15 modules are not ordered, programmed or measured. See the
[current path](candidates/README.md#current-path-p15-r1--the-two-existing-board-ls) for the
exact revisions and hashes, and the
[before-programming checklist](firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md) before any
power-on. `boards/board-p/` remains the as-ordered 2026-09-19 Board P reference.
The [current state and completion page](doc/src/content/docs/architecture/current-state.mdx)
lists what is ordered, programmed and measured, and the owner actions in order.

Start the two-P15 order preparation at the [prototype-order handoff](manufacturing/README.md).
Supplier preview, order-day availability and total cost remain owner checkout gates.

## Repo layout

- `doc/` — zudo-doc documentation site (source of truth for specs, notes, and build logs)
- `boards/board-p/` — KiCad project: USB-PD front end board
- `boards/board-l/` — KiCad project: driver + control + LED array board
- `boards/swd-adapter/` — KiCad project: ST-LINK/V2 20-pin to Board L 1x5 SWD adapter
- `enclosure/` — parametric starburst enclosure generator and [print/assembly guide](enclosure/README.md)
- `symbols/`, `footprints/` — shared KiCad symbol/footprint/3D libraries for all projects (see `footprints/CLAUDE.md`)

## Component selection

Read the [draft selection and socket comparison guidance](doc/src/content/docs/architecture/component-selection-guidelines.mdx) before proposing parts. Exact evidence ownership remains in the component-spec-audit inventory.
