# circuit-synth spike — FINDINGS

**Issue:** #75 (Approach B of epic #68 — "does the AI → schematic handoff actually work?")
**Sheet modeled:** `linear-regulation` (the three LDO output stages).
**Date:** 2026-06-17 · **Host:** macOS arm64 · **KiCad:** 10.0.0 · **python3:** 3.14.4

> **Verdict in one line:** circuit-synth **works end-to-end on Python 3.14** and
> produces a **structurally valid, KiCad-v10-parseable hierarchical project** —
> but the output has **no drawn wires** (connectivity is 100% hierarchical-label
> stubs) and an **older file-format token (v9)**, so for this repo it is a
> **net-correctness generator, not a drop-in schematic**. Useful as a
> connectivity/netlist authoring aid; **not** worth adopting to replace
> hand-drawing these ~27 parts.

---

## 1. Did install work? (on py3.14)

**Yes — clean install on Python 3.14.4, first try, no rabbit-hole.**

- Only `python3.14` was on PATH (no 3.11/3.12/3.13). The issue warned 3.14 might
  be unsupported, but `pip install circuit-synth` into a fresh venv **succeeded**:
  `circuit-synth 0.12.1` + `kicad-sch-api 0.5.6` + ~120 deps.
- Every dependency (numpy 2.4.6, scipy 1.17.1, lxml 6.1.1, matplotlib, fastmcp,
  openai, pydantic, sexpdata, …) shipped a **cp314 or pure-python wheel**, so
  **nothing compiled from source**. Install took ~1 minute. No pyenv, no
  Homebrew Python, no compile. Timebox never threatened.
- venv lives in repo-root `__inbox/cs-venv` (gitignored) — never committed.

## 2. Did it generate a valid `.kicad_sch`? (kicad-cli parsed it?)

**Yes.** `generate_kicad_project()` returned without raising and wrote a full
**hierarchical** project:

| File | Role |
|------|------|
| `linear_regulation.kicad_sch` | root sheet (3 sub-sheet refs) |
| `pos_12v_stage.kicad_sch` | U6 L7812 stage — 9 parts |
| `pos_5v_stage.kicad_sch` | U7 L7805 stage — 9 parts |
| `neg_12v_stage.kicad_sch` | U8 7912 stage — 9 parts |
| `linear_regulation.net` / `.json` / `.kicad_pro` | netlist / IR / project |

Headless validation (no GUI), **`kicad-cli` v10**:

```
kicad-cli sch export netlist --output … linear_regulation.kicad_sch   → exit 0
kicad-cli sch export netlist --output … pos_12v_stage.kicad_sch        → parsed
   unique refs: C1 C2 C3 C4 D1 F1 LED1 R1 U6   (the 9-part +12V stage)
```

KiCad v10 read the circuit-synth s-expressions cleanly. (One cosmetic
`Fontconfig error` line on stderr — does not affect the parse; exit 0.)

> One caveat: `kicad-cli sch export netlist` on the **root** sheet emitted an
> empty component list (it did not auto-descend the hierarchy in this invocation);
> exporting each **sub-sheet** directly yields the full 9-part netlist. So
> "valid" = each sheet parses and the parts/nets are correct; full-project
> netlist flattening would be done inside Eeschema, which we deliberately did not open.

## 3. File-format version — compatible with the repo's KiCad v10?

- **Generated:** `(version 20250114)`, `(generator "circuit_synth")` — a
  **KiCad v9-era** token (circuit-synth targets v8/v9).
- **Repo production:** `(version 20260306)`, `(generator_version "10.0")` — **v10**.

There **is a version gap (v9 → v10)**, but it is **forward-compatible on read**:
KiCad v10 / `kicad-cli` v10 parsed the v9-token files without error. KiCad
silently upgrades older formats on open. So you *can* import circuit-synth output
into this v10 project; it would be re-saved in the v10 format the moment Eeschema
touches it. No GUI was opened to confirm the re-save (per guardrails) — the
compatibility claim rests on the clean `kicad-cli` v10 parse, not a GUI open.

## 4. How good is the auto-placement?

**Mechanically valid, logically poor.** From the s-expr coordinates + the
generator's own log:

- circuit-synth ran a **"TEXT-FLOW PLACEMENT"** pass: it sorts parts largest-first
  and lays them out in a **left-to-right row** ("All components fit on A4"). In the
  +12V sheet every symbol sits at y ≈ 25–36 mm with x marching 38 → 262 mm.
- **There are ZERO drawn wires and ZERO junctions.** Connectivity is expressed
  **entirely through 22 `hierarchical_label` stubs per sheet** — one attached at
  each pin — *including auto-promoted internal nets* (`U6_OUT_LOCAL`, `U6_LED`).
  `grep -c '(wire'` = 0, `'(label'` = 0, `'(hierarchical_label'` = 22.
- Result: each sheet is a **flat row of symbols surrounded by net-name labels** —
  a "label rats-nest." It is netlist-correct but conveys **no signal flow**:
  no IN→reg→OUT left-to-right story, no GND rail, no grouped decoupling.
  A human opening it learns the connections only by reading label text, not by
  following lines.

(Side note: it also promotes every internal net I named — `U6_OUT_LOCAL` — to a
visible hierarchical label, which clutters the sheet further. Naming internal
nets in the Python is a footgun for the visual output.)

## 5. Tidy-up time vs. hand-drawing ~27 parts

The three stages are **27 parts total** (9 × 3), nearly identical topology.

- **Hand-drawing from scratch in Eeschema:** these are textbook LDO stages and
  highly repeatable (draw one, copy ×3, swap values/symbols). Estimate
  **~1.5–3 h** for a tidy, readable sheet by someone who knows the parts.
- **Tidy-up of the circuit-synth output to repo quality:** because there are **no
  wires at all**, "tidy-up" means **drawing essentially all the wiring by hand**,
  deleting/hiding the auto-promoted internal labels, re-laying the row into a
  signal-flow layout, and swapping the generic `Regulator_Linear:*` / `Device:*`
  symbols for the repo's real `zudo-pd:` library parts (correct footprints,
  LCSC part numbers, pin maps). That is **roughly the same effort as hand-drawing
  (~2–3 h), plus the re-symbol/footprint chore** — so **no net time saving** on
  the schematic, and the placement/wiring (the slow part) isn't actually done for you.

  What you *do* get for free is a **correct netlist / connectivity spec** — which
  has value as a checklist or for an ERC cross-check, but not as a finished drawing.

## 6. Verdict for this repo

**Do not adopt circuit-synth to author/replace these schematics.**

- Install + generation + headless validation all work on the current toolchain
  (py3.14, KiCad v10) — the *pipeline* is real and low-friction.
- Output is electrically correct and v10-parseable; good as a **netlist /
  connectivity generator** or an ERC sanity reference.
- The drawing itself is unusable as-is: **no wires**, internal nets leaked as
  labels, flat text-flow placement, generic symbols (not the repo's `zudo-pd:`
  library with the real LCSC parts/footprints), and an older format token.
- For ~27 highly-repetitive LDO parts, the human still draws all the wiring and
  re-symbols everything, so there is **no time win** over hand-drawing — and the
  result would be lower quality than the existing hand-drawn sheet.

**Where it *could* pay off** (not this task): large, irregular, copy-pasta-heavy
nets where getting the *connectivity* right by hand is the bottleneck and the
visual layout matters less — or as a programmatic ERC/netlist double-check against
a hand-drawn sheet. For zudo-pd's small, tidy, custom-symbol boards, hand-drawing
in Eeschema remains the better path.

---

### Reproduce

```bash
python3 -m venv __inbox/cs-venv                       # repo-root, gitignored
__inbox/cs-venv/bin/pip install circuit-synth
__inbox/cs-venv/bin/python experiments/ai-circuit-design/circuit-synth-spike/linear_regulation.py
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist \
  --output /tmp/n.net \
  experiments/ai-circuit-design/circuit-synth-spike/generated_linear_regulation/pos_12v_stage.kicad_sch
```

See `command-log.txt` for the exact commands and their output.
