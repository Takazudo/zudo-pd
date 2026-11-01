---
name: component-project-passives
description: Resolve the exact resistor, ceramic-capacitor, electrolytic-capacitor, and LED lines used across zudo-pd board-a and board-b (UNI-ROYAL 0603/0805 resistors, Samsung/Yageo MLCCs, ACMECON/HRK/DMBJ/FOLLON electrolytics, Hubei KENTO Elec 0603 LEDs). Use whenever one of the listed MPNs/LCSC IDs, a passive's electrical limit, voltage-rating-vs-rail margin, DNP/fitted placement, or the C4/C22/C23 470uF canonical-LCSC decision is relevant.
---

# Exact project passives

Run the central validator and read every local JSON record before using these records. Route an exact MPN or LCSC ID directly to its record; do not substitute a nearby value, a generic same-package part, or a same-name cross-vendor listing.

## Coverage

22 standalone records, one per inventory line, covering:

- **9 UNI-ROYAL resistors** (R0603/R0805): C25803 (100k), C23206 (56k), C23179 (470R), C23162 (4.7k), C23186 (5.1k), C21189 (0R jumper), C25804 (10k), C21190 (1k), C17513 (1k, R0805).
- **5 ceramic capacitors**: C13585 (10uF 1206, Samsung), C1711 (100nF 0805, Yageo), C15849 (1uF 0603, Samsung), C1623 (470nF 0603, Samsung), C1729 (22nF 0805, Samsung).
- **5 aluminum electrolytics**: C2983319 (470uF 25V, HRK), C22383803 (470uF, ACMECON -- see canonical-LCSC decision below), C22383804 (100uF 25V, ACMECON), C970687 (100uF 50V, DMBJ), C22387780 (470uF 35V, FOLLON).
- **3 LEDs** (0603): C2289 (yellow-green), C2288 (blue), C2286 (red).

## Evidence use

`sources.json` retains manufacturer datasheets (UNI-ROYAL resistor family sheet, Samsung/Yageo MLCC reference sheets, ACMECON/HRK/DMBJ/FOLLON electrolytic datasheets, Hubei KENTO Elec LED datasheets, all retrieved via LCSC's manufacturer-hosted `datasheet.lcsc.com` PDF host per the ss34-c8678 exemplar's precedent) plus this project's own netlist-derived `board-a-usb-pd-core.md` / `board-b-synth-power.md` design docs for topology and rail-margin facts. `facts.json` separates primary ratings, calculated RCWV/rail-margin/drive-current values, and project topology. Cite exact fact and source IDs with units, locators, and conditions.

Several vendor datasheets for the electrolytics/LEDs are vector-embedded PDFs that resisted clean text extraction; where that happened, the retained PDF is still hash-locked as the manufacturer-primary source, and its specification values are cross-verified against the corresponding LCSC product-detail page's structured (JSON-LD) Specifications data -- each such source's `evidence_extract` says so explicitly.

## Voltage-rating-vs-rail margins

Every electrolytic carries a `voltage-rating-vs-rail` (or equivalent) COVERED coverage entry with a CALCULATED margin fact, using the exact per-refdes net from `board-b-synth-power.md`'s netlist-derived tables where that is more precise than inventory.json's line-level function text (e.g. C22383803's C4/C22 sit on +7.5V while C23 sits on +5V; C22383804's C5/C7 sit on the +15V input bus, not a DC-DC output). **C970687 (C9) is the one exception**: per issue #117's explicit scope, its cross-rail bridging-voltage math (28.5V nominal / 33.5V edge case, from the LM2596S-ADJ inverting buck-boost topology) is owned by `component-lm2596s-adj`; this record carries only C970687's own 50V manufacturer rating.

C11's placement conflict between inventory.json's old function text (+13.5V DC-DC output) and `board-b-synth-power.md`'s U4 net table (C11.2 on -13.5V OUT) is RESOLVED: C11 sits on -13.5V OUT, per `fact-c2983319-c11-net-discrepancy`. The -13.5V output-cap bank is C11 (Honor RVT1E471M0810 C696190, Phi 8 land, adopted 2026-11-01 by `dec-b-stock-gap-substitutions` in place of HRK C2983319, which stays here as a REJECTED candidate) || C24 || C12 (both FOLLON C22387780, Phi 10 land), per decision `neg-rail-cap-bank`. Equal 120 Hz ESR gives each can one third of the ripple (`fact-c696190-c11-ripple-share-3can`).

## C4/C22/C23 canonical-LCSC decision

The schematic's placed symbol for C4/C22/C23 is `RVT1A471M0607_C335982` (Value `470uF 10V`), but each instance's `LCSC Part`/`Datasheet` properties point at C22383803 -- inventory.json (not edited by this bundle) therefore assigns C4/C22/C23 to C22383803/ACMECON. This bundle's `fact-c22383803-canonical-choice` picks **C335982 (ROQANG RVT1A471M0607, 10V) as canonical** for a future schgen-spec update, with **C22383803 (ACMECON RVT1C471M0607, 16V) recorded as the alias**, on dated (2026-08-14) evidence: C335982 shows ~368,560 units in stock at LCSC vs. ~3,790 for C22383803, and C335982's 10V rating matches the design intent and the drawn symbol/Value field, whereas C22383803 is actually 16V-rated -- correcting issue #117's assumption that both listings are 10V. This bundle documents the decision; it does not edit inventory.json or the schematic.

## LED polarity note

All three placed LED symbols number pin1=cathode/pin2=anode: green `KT-0603YG` (C2289), blue `KT-0603B` (C2288) and red `KT-0603R` (C2286). The 2026-09-21 correction (`fact-c2289-polarity-note`) renumbered the unused `YLED0603YG` symbol; the placed `KT-0603YG` symbol kept pin1=A until 2026-10-31, when its numbers were swapped to match the LED2 pin-map lock (copper, CPL and nets unchanged). The cathode=pad 1 mapping rests on the LCSC/EasyEDA library and the JLCPCB preview, not the KENTO datasheet, so check the physical body mark before assuming uniform LED2/LED3/LED4 orientation.

## Human component reference

Human projection of this bundle: [rec-c25803](/docs/components/records/c25803/), [rec-c23206](/docs/components/records/c23206/), [rec-c23179](/docs/components/records/c23179/), [rec-c23162](/docs/components/records/c23162/), [rec-c23186](/docs/components/records/c23186/), [rec-c21189](/docs/components/records/c21189/), [rec-c25804](/docs/components/records/c25804/), [rec-c21190](/docs/components/records/c21190/), [rec-c17513](/docs/components/records/c17513/), [rec-c13585](/docs/components/records/c13585/), [rec-c1711](/docs/components/records/c1711/), [rec-c15849](/docs/components/records/c15849/), [rec-c1623](/docs/components/records/c1623/), [rec-c1729](/docs/components/records/c1729/), [rec-c696190](/docs/components/records/c696190/), [rec-c22383803](/docs/components/records/c22383803/), [rec-c22383804](/docs/components/records/c22383804/), [rec-c970687](/docs/components/records/c970687/), [rec-c22387780](/docs/components/records/c22387780/), [rec-c2289](/docs/components/records/c2289/), [rec-c2288](/docs/components/records/c2288/), [rec-c2286](/docs/components/records/c2286/). Those pages are generated from the JSON files here and add nothing to them -- where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).

Board P additional exact records: [rec-c14663](/docs/components/records/c14663/), [rec-c22807](/docs/components/records/c22807/). rec-c17414 (r2 R21 10 kOhm) is a REJECTED candidate; Board P r3 R21 is a C21189 0 Ohm strap. Board A-specific facts in this bundle remain scoped to Board A.
