# Board P r3 native rebuild

The committed `boards/board-p/r3-draft/search-two-sided.json` is the placement
owner. Ordinary rebuilds must not enable `R3_SEARCH=1`. The builder runs focused
native filled-polygon contact regressions (including wrong-layer, gap and hole
negative cases) and the host routing fixed-group and evidence-coverage/freshness regressions before routing.
Missing native dependencies fail the workflow; a skipped check is not acceptance.
The ordinary host unit suite does not need `pcbnew`.

On the selected Mac, run the pinned Docker image under the machine-wide heavy
queue and the shared BSD native lock. For example, with `uv` and Docker available:

```sh
DOCKER_DEFAULT_PLATFORM=linux/amd64 bash "$HOME/.codex/scripts/heavy-guard.sh" --max-run 0 -- \
  uv run --python 3.13 --with numpy python -c \
  'import fcntl,subprocess,sys; lock=open("/tmp/kicad-native.lock","a"); fcntl.flock(lock.fileno(),fcntl.LOCK_EX); raise SystemExit(subprocess.call(sys.argv[1:]))' \
  bash scripts/pcb/board-p-r3-draft/run.sh
```

The host-only regression can also run independently:

```sh
uv run --python 3.13 --with numpy python scripts/pcb/board-p-r3-draft/test-routing-fixed-groups.py
```

After a complete rebuild, run native DRC with schematic parity against the
canonical Board P project, classify every warning, and run
`verify-corrections.py <output.json>` using the same pinned `pcbnew` under the
native lock. This verifies local R1–R4 geometry, actual routed supply paths,
local return paths, connected copper area and conditioned loss arithmetic.
Keep source hashes and native reports together. Save `native-drc-receipt.json`
and its hashed report in the r3 report directory, binding the PCB, schematic
and project bytes and the exact parity/all-severity command. Rerun
`annotate-fit.py boards/board-p/r3-draft` after this receipt exists; absent or
stale evidence is reported as NOT RUN, never copied from the historical review. A completed routing process or
local geometry report alone does not establish DRC, electrical acceptance,
supplier stencil/via-process approval or a measured 5 A thermal rating.

For a cheaper reproducibility check after a successful run, retain its temporary
`placed.kicad_pcb`, copy it into an ignored replay directory, apply the final
`routes.json` with `apply-tracks.py`, and refill with `route-power.py` plus the
same `pours.json` under the same native lock/toolchain. Then run
`verify-replay.py <canonical PCB> <replay PCB> <report.json>`. It compares the
entire serialization while ignoring only generated UUID values. Do not describe
this as byte-for-byte regeneration or as a new heuristic placement search.

The builder and copper owners assign stable UUIDv5 identities to newly created
objects, and `run.sh` copies the canonical project settings to both native load
basenames. Random identities and missing project context were observed to change
filled copper. The final reproducibility receipt therefore includes two fresh
placement builds from the spec/library/committed placement, validated route reuse,
and a native-geometry comparison against the completed default routing input.
It does not claim that a new heuristic search was performed. The replay check
rejects duplicate UUIDs as well as any serialized difference beyond UUID values.

## Final probe artwork stage

`finish_details.py INPUT OUTPUT` applies only the reviewed J2/J3 contact
ordinals, reverse-side role maps and two inset edge guides. It checks actual
pad nets (including J3.4 VBUS_IN and J3.5 GND), conservative mask-opening
clearance, the retained supplier text constraints, and exact serialization
identity outside 34 approved artwork objects. It never refills copper.
`run.sh` runs the native `test-finish-details.py INPUT` regression before this
stage: twin byte equality, idempotence, byte-preserved source/destination
project sidecars and deliberately wrong J3.4/D5.1 nets. The same stage keeps Q3/D13 reference
fields on Fab and gives D5 one printable pin1 cue after explicit body/mask checks. The artwork save uses the
pinned API `SaveBoard(path, board, True)` and checks its return value; no project
settings are written by this stage.
Native DRC/parity and supplier preview remain separate acceptance gates.
