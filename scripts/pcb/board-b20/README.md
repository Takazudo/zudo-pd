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
