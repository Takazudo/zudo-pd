# PD20 native schematic evidence — 2026-11-10 JST

Executed on the selected Mac using the exact pinned Linux AMD64 KiCad 10.0.6 image. `execution.json` binds execution revision, dirty-worktree source hashes, actual tool binaries, commands and raw outputs. Board P and B20 exported netlists match their owned specs. Neither schematic has ERC errors; B20 has no warnings. Board P has 27 imported-symbol pin-type warnings, individually dispositioned in `warning-disposition.json` against the native netlist, spec and exact owner pin evidence.

The Unspecified symbol types limit ERC's ability to check electrical driving rules. They are not converted into a clean electrical sign-off, blanket suppression, or a change to shared P15 identity. The independent warning review found no wrong-net defect. Direct STUSB4500 PDF inspection was NOT RUN in this warning review because the previously acquired PDF was not found locally; retained owner pin-table evidence was checked. TVS2200 Table 6-1 was inspected directly.

PCB DRC, connectivity, assembly, simulation, supplier acceptance and physical performance remain distinct. See `boards/board-p/r3-draft/native-drc-receipt.json`, `boards/board-b20-draft/u6-bypass-review.json` and the [readiness ledger](../../prototype-order-readiness.md). All physical tests remain NOT RUN.

## Final native Mac execution

`final-erc/` retains the fresh 22-second native Mac CLI execution against the current authored projects, including B20's three stricter legend rules. Both netlists match the owned specs; neither board has ERC errors, B20 has zero warnings and P has the same 27 warning objects as the independently reviewed Docker run. The parent compared the parsed warning objects exactly and reran the per-warning netlist/spec/evidence audit against the new source/tool/report hashes. The original Docker receipt remains historical evidence above.

## Final corrected pair assembly

[Final execution receipt](final-assembly.json) records the actual isolated Mac 10.0.6 run on P `56cbe0ab…` and B20 `7dd3cc43…`. All 63 artifact hashes were independently checked before exact promotion to `boards/board-b20-draft/assembly-preview/`. The populated collision screen checked 12195 pairs with zero unintended intersection; supplemental U2/U3 PROJECT envelopes and both native renders passed review. Large assembled STEP derivatives remain local and ignored. This is nominal CAD evidence, not supplier, physical, electrical or thermal acceptance.
