---
name: pd-schematic-review
description: "Datasheet-aware schematic review for this USB-PD power-supply board. Exports the KiCad schematic to a compact netlist, walks a power-supply checklist (VBUS sense paths, regulator EN/feedback dividers, dropout headroom, polarity, decoupling, abs-max), and writes a review report whose findings are LEADS to verify against the datasheet — never ground truth. Use when the user says 'review the schematic', 'schematic review', 'pd-schematic-review', 'check the design', or 'audit the circuit'. READ-ONLY against all *.kicad_sch / *.kicad_pcb."
argument-hint: "[optional: a stage to focus on, e.g. 'usb-pd' or 'U6']"
allowed-tools: Bash(/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist *), Bash(python3 *), Bash(grep *), Bash(git status --porcelain*), Bash(ls *), Read, WebSearch, WebFetch, Write
---

> **Read-only against the design.** This skill exports and analyzes the schematic; it
> NEVER edits `*.kicad_sch` / `*.kicad_pcb`. It only writes the report under
> `experiments/ai-circuit-design/schematic-review/` and raw exports under `__inbox/`
> (gitignored). Before finishing, confirm `git status --porcelain '*.kicad_sch'
> '*.kicad_pcb'` is empty.

# pd-schematic-review — datasheet-aware power-supply review

Reviews this board's schematic the way a careful second engineer would: export the real
net topology, then check it against each part's datasheet using a power-supply checklist.
The motivating case is the **v3 STUSB4500 pin-18 bug** (`VBUS_VS_DISCH` tied to GND instead
of sensing VBUS) — a datasheet-aware net-by-net review catches that class of error; eyeballing
the schematic by pin position does not (it produced several *false* findings last time — see
`doc/src/content/docs/inbox/v3-pd-failure-diagnosis.md`).

**Core principle — findings are leads, not verdicts.** Every finding is a *lead to verify
against the datasheet*, never ground truth. A static net-topology pass cannot measure voltages,
simulate loops, or judge thermals. State this explicitly in the report and cite the source
behind each finding.

## Steps

### 1. Export the schematic to a compact netlist (read-only)

```bash
mkdir -p __inbox
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist \
  --format kicadxml -o __inbox/zudo-pd-netlist.xml zudo-pd.kicad_sch
```

- `kicadxml` is the easiest to parse (one `<comp>` per part, one `<net>` per node set).
  `kicadsexpr` (`--format kicadsexpr -o __inbox/zudo-pd-netlist.net`) is the alternative.
- A `Fontconfig error: Cannot load default config file` line on stderr is harmless — the
  export still completes (CLI is run headless). Check the output file exists.
- Keep exports in `__inbox/` only — they are gitignored and must NOT be committed.

### 2. Build the pin→net map per part

Parse the XML so you review the *actual* topology, not the symbol's pin positions. Extract,
for each reference designator, every `pin → net` with its `pinfunction`. Example parser:

```bash
python3 - <<'PY'
import re
xml = open('__inbox/zudo-pd-netlist.xml').read()
nets = re.findall(r'<net code="\d+" name="([^"]*)"[^>]*>(.*?)</net>', xml, re.S)
pinmap = {}
for name, body in nets:
    for m in re.finditer(r'<node ref="([^"]+)" pin="([^"]+)"(?:\s+pinfunction="([^"]*)")?', body):
        pinmap[(m.group(1), m.group(2))] = (name, m.group(3) or '')
for r in ['U1','U2','U3','U4','U6','U7','U8']:
    print(f'== {r} ==')
    for (rf,p),(n,pf) in sorted(pinmap.items()):
        if rf==r: print(f'  {r}.{p:3} [{pf:16}] -> {n}')
PY
```

### 3. Establish the datasheet source for each part BEFORE reviewing it

This is what keeps "datasheet-aware" from collapsing into "from memory". For each part, pick
the strongest available source and record it:

- **Local PDFs** — `doc/public/datasheets/*.pdf` (LM2596S, L7812CD2T, L7805ABD2T, CJ7912,
  CH224D, SMAJ, USBLC6, etc.). Prefer these; read them when a number matters.
- **Local repo docs** — `doc/src/content/docs/components/*.md` and
  `doc/src/content/docs/inbox/stusb4500-pinout.md`, `v3-pd-failure-diagnosis.md`. These
  already distill the datasheets and the v3 root cause.
- **STUSB4500 has no local PDF.** Fetch ST's datasheet from the web if possible
  (`https://www.st.com/resource/en/datasheet/stusb4500.pdf`; the direct PDF fetch may time
  out — a WebSearch for `STUSB4500 DS12499 VBUS_VS_DISCH` returns the authoritative content).
  If you cannot reach it, **label every STUSB4500 finding "based on repo docs
  (stusb4500-pinout.md / components/stusb4500.md), verify against ST DS12499"** rather than
  asserting a value from memory.

### 4. Walk the power-supply checklist

Cover the **USB-PD stage** (STUSB4500 `U1`) and the **three regulator stages**
(`U6` +12V LDO, `U7` +5V LDO, `U8` −12V LDO), plus the DC-DC stage (`U2/U3/U4`) feeding them.

- **VBUS sense path** — `U1.18 VBUS_VS_DISCH` must reach the **VBUS rail through a
  current-limiting series R** (≤50 mA discharge), NOT GND. This is the v3 blocker. Trace the
  net end-to-end: `VBUS_IN → R14 → U1.18`?
- **Enable pins** — LM2596 `~ON/OFF` (pin 5): Low/Float = ON, High = shutdown. Confirm each is
  tied to its correct "off-is-not-asserted" level (GND for positive regs; the local negative
  rail for the inverting reg).
- **Feedback dividers** — for each adjustable DC-DC: `Vout = Vref·(1 + Rtop/Rbottom)`,
  Vref = 1.23 V for LM2596-ADJ. Recompute from the *actual* divider resistors and compare to
  the intended rail. Confirm the FB tap is the divider midpoint, not shorted.
- **Dropout headroom** — for each LDO, `Vin − Vout` vs the datasheet dropout. Flag thin
  margins, especially the **~1.5 V intermediate-rail margins** (13.5 V → 12 V is only 1.5 V
  against a ~2 V typical dropout).
- **Polarity** — electrolytic cap orientation on negative rails; negative-LDO pinout
  (IN/GND/OUT differ from positive parts); catch-diode and inductor orientation in the
  inverting DC-DC.
- **Decoupling** — input/output bulk + HF caps present on each regulator and on
  STUSB4500 VDD / VREG_2V7 / VREG_1V2.
- **Abs-max ratings** — VDD ≤ device max (STUSB4500 ~22 V), cap voltage ratings vs rail,
  CC-pin protection.

### 5. Write the report

Write to `experiments/ai-circuit-design/schematic-review/REVIEW-REPORT.md`. For **every
finding** include:

- the net evidence (the actual pins/nets from step 2),
- the **source** backing it (local PDF filename / repo doc path / "verify against ST DS12499"),
- a severity (blocker / marginal / nit / OK-confirmed), framed as a **lead to verify**.

End with an honest **"What this pass can and cannot catch"** section (static topology only:
catches wrong-net / missing-component / divider-math / polarity-by-pin; cannot catch values
under load, thermals, loop stability, layout/parasitics, footprint-to-symbol pin mismatch).

### 6. Production-file guard (verify before finishing)

```bash
git status --porcelain '*.kicad_sch' '*.kicad_pcb'   # MUST be empty
```

Only `.claude/skills/pd-schematic-review/` and
`experiments/ai-circuit-design/schematic-review/` may be added. Raw `__inbox/` exports stay
uncommitted.

## Notes

- **CLI only, no GUI.** Never open KiCad; only `kicad-cli ... export`.
- If a datasheet can't be fetched, label the finding's source per step 3 and review from known
  pin functions — do not hang waiting on a download.
- This board's part map (current): `U1` STUSB4500QTR, `Q1` AO3401A load switch, `U2/U3/U4`
  LM2596S-ADJ DC-DC (U4 is the **inverting** config for the −13.5 V rail — its GND/EN/TAB
  reference to the negative output, not system GND), `U6` L7812 (+12 V), `U7` L7805 (+5 V),
  `U8` CJ7912 (−12 V). Confirm against the export each run — the BOM can change.
