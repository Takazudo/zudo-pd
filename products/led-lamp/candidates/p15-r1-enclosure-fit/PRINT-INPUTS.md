# P15 lamp print inputs (2026-11-20)

Current print inputs for the P15 r1 + Board L lamp. Desk and CAD record only: nothing has been printed,
seated or measured. **Physical fit is NOT RUN.** The SHA-256 values are of the tracked Git blobs at this
revision; no tracked output was regenerated.

## Use the tracked STLs

The tracked set in `doc/public/assets/enclosure/stl/` (29 files) and its archive
`doc/public/assets/enclosure/smoke-reversing-stls.zip` (459449 B, SHA-256 `d2ee9e0b2dbd52dc078e4b13a3a0a03773ee88fd268848a70cdb42377420b5c6`)
are the print inputs for the P15 lamp at the default `--board-gap 11.0` and `--post-clearance 0`.
On 2026-11-20 the same `enclosure/generate.py` (SHA-256 `926d5757…`) was re-run in isolated copies with the
historical LED Board P and with zudo-pd P15 r1 (`board-p15-draft.kicad_pcb`, `97acc5f4…`). Both runs passed
their assertions and `check_stack`; P15 has the same three holes and J1 position, and both runs produced
byte-identical STLs. Against the tracked STLs, 25 of 29 differ only in mesh serialization (equal face counts,
volume, bounds and sorted vertex sets). `enclosure/verify_exports.py` passes on the tracked tree. The KiCad
STEP body-clearance check in [README.md](README.md) was not re-run; its 30 recorded source hashes still match.
Do not regenerate unless a coupon or seated-gap measurement selects a new parameter.

| Group | File | Bytes | SHA-256 | Note |
| --- | --- | ---: | --- | --- |
| Shell | `00-base.stl` | 297784 | `29d63763b1ad345cf8bb08f90a390e089c3930d7185ae215bc3573997fa00c3f` |  |
| Shell | `01-band-usb.stl` | 216984 | `15e3687cd60ab9d93d58b4afeb1f2bbe8c2d1f4ad9b18f4980c2ac6aa94424d4` |  |
| Shell | `02-band.stl` | 217984 | `9d8558948059eb3393b23bef09b2a356fa66c0a27b61a961fd2278d06783e54f` |  |
| Shell | `03-band.stl` | 217984 | `9d8558948059eb3393b23bef09b2a356fa66c0a27b61a961fd2278d06783e54f` |  |
| Shell | `04-band.stl` | 217984 | `9d8558948059eb3393b23bef09b2a356fa66c0a27b61a961fd2278d06783e54f` |  |
| Shell | `05-band.stl` | 217984 | `9d8558948059eb3393b23bef09b2a356fa66c0a27b61a961fd2278d06783e54f` |  |
| Shell | `06-band-top.stl` | 91684 | `91c8f1de817670434727e7885c793ec8287bf9d1daf97cd23fdffed6d60528a1` |  |
| PCB spacers | `mount-01-17.6mm.stl` | 42084 | `70442de24bbe6a74fcf36cba3d05128f3028aae9492b310d59ae12ddac8e4efb` |  |
| PCB spacers | `mount-02-17.6mm.stl` | 42084 | `70442de24bbe6a74fcf36cba3d05128f3028aae9492b310d59ae12ddac8e4efb` |  |
| PCB spacers | `mount-06-17.6mm.stl` | 42084 | `70442de24bbe6a74fcf36cba3d05128f3028aae9492b310d59ae12ddac8e4efb` |  |
| PCB spacers | `mount-03-5.0mm.stl` | 42084 | `22f09c25439bcfd56ed060f8f1847a8ae692db854e83de98cf9694289021a894` |  |
| PCB spacers | `mount-04-5.0mm.stl` | 42084 | `22f09c25439bcfd56ed060f8f1847a8ae692db854e83de98cf9694289021a894` |  |
| PCB spacers | `mount-05-5.0mm.stl` | 42084 | `22f09c25439bcfd56ed060f8f1847a8ae692db854e83de98cf9694289021a894` |  |
| PCB spacers | `interboard-01-11.0mm.stl` | 42084 | `ca3a207b38179bc7eede2d73925cda00e6cf2ff321438dd63a8ceadbf1ea8e8a` |  |
| PCB spacers | `interboard-02-11.0mm.stl` | 42084 | `ca3a207b38179bc7eede2d73925cda00e6cf2ff321438dd63a8ceadbf1ea8e8a` |  |
| Posts and feet | `post-01-flat.stl` | 684 | `13ff5ac2291170a8947f9180f1d9a709f05a02a47203d50fe27b56d15bb252ec` |  |
| Posts and feet | `post-02-flat.stl` | 684 | `13ff5ac2291170a8947f9180f1d9a709f05a02a47203d50fe27b56d15bb252ec` |  |
| Posts and feet | `post-03-flat.stl` | 684 | `13ff5ac2291170a8947f9180f1d9a709f05a02a47203d50fe27b56d15bb252ec` |  |
| Posts and feet | `foot-01.stl` | 21884 | `3702871069a4241aa6cc519d205e9fad978a26f062325a7da4aefda4ef3552cb` |  |
| Posts and feet | `foot-02.stl` | 21884 | `3702871069a4241aa6cc519d205e9fad978a26f062325a7da4aefda4ef3552cb` |  |
| Posts and feet | `foot-03.stl` | 21884 | `3702871069a4241aa6cc519d205e9fad978a26f062325a7da4aefda4ef3552cb` |  |
| Fitting coupon (print first) | `test-square-post-flat.stl` | 684 | `36fb46254f7f5b479ba7ec8e0f8efb18e05789f7389501eaaec29d0373e4696c` |  |
| Fitting coupon (print first) | `test-square-hole-4.0.stl` | 1684 | `105985d6d8ce63a23b5eae56a3611a94b9246d497bc226341e5e47958c55a123` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-square-hole-4.2.stl` | 1684 | `20f413f0c91204e9f8d3c1c8bbe44f04aafc0f5e8665025f3f45c8159cbb9c2b` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-square-hole-4.4.stl` | 1684 | `8f847fe72e32e21dfa2af85958766d7c88c2cf5cb39612783e0323a1eba0ed63` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-pin-2.4.stl` | 42784 | `5ed329d449e8188863a366fbfd36a249dc017e97a0a552435878fc831748174b` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-socket-clearance-0.2.stl` | 21684 | `e3ba70ee25957ee38449e97d54528950d7fb1023bac816eb7c048f581831c4c0` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-socket-clearance-0.4.stl` | 21684 | `8e0f81e514c994775a7cc7989494b6fc09b1168acad472da8e68ffe61c00916f` | Not in either `_3dp/*.3mf`; print from this STL |
| Fitting coupon (print first) | `test-socket-clearance-0.6.stl` | 21684 | `8e300afa47b645e243c43666878acd3f4db9a128ea75523d890cf2d7d4a9ac65` | Not in either `_3dp/*.3mf`; print from this STL |

Print and assemble per [`enclosure/README.md`](../../enclosure/README.md) (PETG, 0.4 mm nozzle, 0.2 mm layers,
at least 3 walls). The square-hole coupons select `--post-clearance` 0/0.2/0.4; the pin/socket coupons may change
`socket_diameter`. Measure the seated JOUT1↔J2 header gap before changing `--board-gap`.

## Bambu projects are incomplete

`_3dp/h2d-led-enclosure.3mf` (SHA-256 `8a0aa823af9060680895fafa8cc7b7aa9640781e7ef080ced49c76caa59a7b57`) and
`_3dp/p1s-led-enclosure.3mf` (SHA-256 `be5caf0feeb5ba66b079a6810477d6983625007ef36732f4921d529e9abdf28f`) contain the 21 assembly parts plus
only `test-square-post-flat`. The other 7 coupons are missing; print them from the STLs above. The 3MF meshes
were not compared with the STLs.

## Not run

Printing, coupon fit, seated header gap, USB plug engagement, wheel/slider access, screw fit, retention,
appearance and powered temperatures are all NOT RUN.
