# B20 native generation and refill finalization

Run `run.sh` under the machine-wide heavy guard. Do **not** wrap the whole script
in another native lock: each pcbnew process acquires `/tmp/kicad-native.lock`,
and `finalize_refill.py` holds that same host fcntl lock across its two fresh
pinned Docker CLI processes. The host router runs between native stages.

The applicator writes an isolated intermediate PCB. The finalizer copies that
PCB and the exact authored project, schematic and library tables into a local
isolated directory, refills it, then repeats the refill in a fresh process with
the same authored project bytes. It requires byte-identical first/second outputs,
unchanged non-fill manufacturing geometry and item identities, zero native
errors/open connections/parity findings, and only the four specifically reviewed
J6/J7/J10/J11 silk-only library warnings. Source/context/checker files must remain
unchanged. Only then may it replace the requested output PCB. It never saves or
restores the canonical project file. Failed diagnostics stay local under `tmp/`.

`refill-finalization.json` is native reproducibility evidence, not electrical,
thermal, supplier or order acceptance. An initial fill delta must still be
quantified and independently reviewed. The exporter's exact source/staged
geometry guard remains mandatory; no tolerance is introduced by finalization.

Focused host controls:

```sh
python3 -m unittest discover -s scripts/pcb/board-b20 -p 'test_finalize_refill.py'
```

A fixed-route replay may reuse previously validated routing only after fresh
builder pad/rule-area geometry matches its original input exactly. Label such a
proof as a fresh-builder/fixed-route replay, never as another heuristic route.

## Value-only field sync (Actions)

`.github/workflows/b20-field-sync.yml` applies a spec Value/LCSC change to the saved PCB without a native
host. It is dispatched by hand on a branch whose spec, schematic and components projection already carry
the change, with the expected reference designators as input. At the pinned image:

1. `sync-fields.py` sets only those fields. It refuses footprint, set or unexpected-reference changes.
2. `finalize_refill.py` refills twice and checks DRC, including schematic parity.
3. `verify-field-sync.py` proves that everything except the named fields, filled copper included, is
   unchanged against the committed PCB.
4. The hash-bound desk reports are re-derived from the saved native copper: report-input receipt,
   loop, current, thermal and the power reports. Routing-report counts must be unchanged.

It first checks that the components projection and the schematic match the spec. Changed files are
offered only when every step passes (`status.txt` says PASS). The pair assembly preview
(`assembly-preview/verification.json`) and the STEP datum proof (`footprints/kicad/step-datum-verification.json`)
also bind the PCB hash. This job does not refresh them, so a development export of the pair stays blocked
until they are re-run on a native host. The job uploads the changed files for review and pushes nothing. It is not a reroute, re-placement or
footprint change. It establishes no electrical, supplier or order acceptance.

## Part insertion in native KiCad (D12 series resistors)

The scripted incremental route for the four D12 series resistors (R77–R80, 0402 C25741, readiness D12,
[#279](https://github.com/Takazudo/zudo-pd/issues/279)) stopped at its own stop condition. With the repository
courtyard rule, no rule relaxed and no other net touched, the planning search found routes for OV12, OV5 and
UV12 but none for UV5. The search found one free 0402 site near U7, which OV5 and UV5 would both need, and no
route out of U7 pin 6 on the right past the UV5_CMP via at (87.6, 58.1), the F.Cu track at x ≈ 88.35 and CRMP2;
moving that via alone found no valid position either. These are search results, not a proof that no route
exists. The insertion is therefore done interactively in the native Mac pass, together with #262.

`verify-insert-parts.py` bounds that edit after the fact:

```sh
python3 scripts/pcb/board-b20/verify-insert-parts.py BEFORE.kicad_pcb AFTER.kicad_pcb \
  --refs R77,R78,R79,R80 \
  --repin U6.3=OV12_IN --repin U6.6=UV12_IN --repin U7.3=OV5_IN --repin U7.6=UV5_IN \
  [--extra-net NET ...] [--reach-mm 10] --output insert-verification.json
```

Put BEFORE.kicad_pcb and BEFORE.kicad_pro side by side, both from the commit before the edit; each board's
project (and any `.kicad_dru`) is read from beside it and its sha256 is recorded. Confirm each `--repin` against
the regenerated schematic: a series resistor splits its net, so the comparator pin moves from `*_DIV` to `*_IN`.

It requires that every existing footprint is unchanged except the net of each `--repin` pad, which must move
between the two pad nets of one new part to a net that did not exist before, and that exactly `--refs` are added. Copper on any net other than the
new parts' pad nets and each named `--extra-net` must be unchanged, as must non-copper content such as the
outline, legend, setup and zone definitions. Each removed or added segment or via must lie, along its whole length, within
`--reach-mm` (10 mm by default) of a new courtyard or a repinned footprint, so copper on a part net cannot change
elsewhere. The project's design rules (`board.design_settings` and `net_settings` in `.kicad_pro`, plus any
`.kicad_dru`) must be identical. Every filled-area corner that changes, per zone uuid and layer, must lie within 2 mm of a new courtyard or of a changed copper item. KiCad's zero-width fracture slits are removed first, because a hole that changes inside the region can move a slit that ends far outside it. That is a vertex screen, not a connectivity proof;
DRC covers islands and unconnected items. It lists every removed and added copper item for review. An
`--extra-net` that is allowed but not changed fails, so each widening is named exactly once. Any net moved
beyond the part nets, such as UV5_CMP, needs an owner decision and must be stated in the PR.

The Mac pass then runs `finalize_refill.py`, which provides DRC with schematic parity under the unchanged rules,
followed by the verifier and the report re-derivation listed in the field-sync section above.

The *_IN copper from each comparator pin to its resistor is a high-impedance node. D12's input RC assumes a 3 pF
stray PA. A 0.2 mm F.Cu track over the In1 GND plane (0.2 mm dielectric, εr 4.6) is about 0.09 pF/mm as a
microstrip (Hammerstad, CALCULATED). Neighbouring F.Cu pour can raise it toward 0.15 pF/mm. Record the routed
*_IN lengths and the resulting figure in D12. Recompute the threshold error and the input RC if it exceeds 3 pF.
