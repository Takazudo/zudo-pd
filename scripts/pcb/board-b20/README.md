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
