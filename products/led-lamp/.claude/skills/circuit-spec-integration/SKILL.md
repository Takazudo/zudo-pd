---
name: circuit-spec-integration
description: Audit cross-component circuit behavior, evidence chains, substitutions, startup, rails, protection, sensing, firmware assumptions, thermal limits, and as-built state. Use whenever a question spans multiple exact component skills or changes USB-PD/NVM, either converter stage, MCU/LED/NTC behavior, harnesses, PCB/BOM/CPL identity, or bench claims.
---

# Circuit specification integration

Run `python3 .claude/skills/component-spec-audit/scripts/validate.py`, then read `references/rules.json` and load every exact owner skill named by all matching rules.

Resolve MPN and LCSC identifiers independently. Reject conflicts, same-name wrong-vendor parts, and ambiguous bare aliases. Directly load subordinate records; never answer only from their parent.

Use the listed fact IDs with their exact conditions and locators. `UNSOURCED` evidence cannot close a domain, and project connectivity cannot prove programmed, assembled, or bench state. For substitutions or design changes, report the affected rule, raw facts, recalculated margins, missing evidence stages, and one honest verdict. Do not silently change design files.

Run `python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py` after editing rules, routes, facts, or evidence-chain state. Deterministic fixtures prove routing and discovery; the hash-locked `references/observed-runs.json` records explicit-skill policy rendering/refusal against frozen evidence and does not claim independent model discovery of IDs.

## Human component reference

Human projection of this bundle: [the cross-component rules](/docs/components/integration/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [component records](/docs/components/records/).
