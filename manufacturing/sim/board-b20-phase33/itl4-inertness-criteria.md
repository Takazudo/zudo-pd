# itl4 inertness diagnostic — criterion stated before the dispatch

**This is a solver-setting diagnostic, not a verdict run.** It judges no candidate, changes no verdict, and does not
admit itl4 as a variant. The owner authorised one dispatch on 2026-11-12. Remedy S1 is described in the independent
abort check, `/mnt/project-files/d1/t2-rev2-abort-check-and-stiffness-remedies-20261112.md`. Whether itl4 may then be
used, and how a matched-variant row may count, are separate owner decisions.

## What runs
- **The decks.** These are the 35 pinned decks of T2 rev 2 run 43187732133: the nom/adv baseline pair plus the 33
  rev 2 decks (baselines, corners, control, sourced and extra cases). They are rebuilt by the merged code. Each must
  hash-equal its recorded deck, or `prepare` refuses.
- **The one change.** `itl4=200` becomes `itl4=1000` in the `.options` line, and nothing else changes. `prepare` checks
  that reverting the edit gives the recorded deck byte for byte.
- **How it runs.** Each deck runs once with the pinned runner (`--original-only`). An abort is recorded with its
  parsed ngspice line and is not retried.
- **Alongside.** The workflow's usual nom/adv identity control runs first, at pinned settings, and must reproduce.
  No other option, deck or model changes in the dispatch. The workflow refuses to combine this input with any other
  opt-in.
- **The reference.** `itl4-pinned-reference-20261112.json` holds each deck's recorded status, deck hash and output
  hashes (`.dat` and every wrdata file; logs excluded), taken from artifact 13933777144. It records 13 decks that
  completed and 22 that aborted.

## Criterion
- **INERT** only if every deck that completed pinned (13) also completes with `itl4=1000`, and every compared output
  file is **byte-identical** to its recorded pinned hash.
- **NOT INERT** if any compared output differs, any output is missing, or any of those decks aborts. The option is
  then dropped.
- **NOT DETERMINED** if any deck neither completes nor aborts (a run failure). Nothing is concluded from such a run.

## Reported beside the verdict (information only)
- **The 22 decks that aborted pinned.** Each is listed as *rescued* (completes with `itl4=1000`) or *still aborting*.
  A still-aborting deck gets its abort time, its timestep, and the node ngspice named, or "unrecorded (ngspice named
  no node)".
- **Rescued decks are only a list.** Their waveforms are not judged against any rule here.

## Expectation (stated before the run, not a criterion)
itl4 bounds Newton iterations per timepoint, and ngspice names a node when Newton fails there. So itl4 can only help
the node-named aborts. The 9 "cause unrecorded" aborts most likely come from the step-rejection path, and I expect them
to keep aborting.
