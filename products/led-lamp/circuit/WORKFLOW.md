# Circuit workflow entry

This entry connects the existing project-owned procedures; it does not replace them.

1. Read [CLAUDE.md](../CLAUDE.md), the [current-state owner](../doc/src/content/docs/architecture/current-state.mdx), the relevant active issue and later owner decisions.
2. For component, schematic, PCB, BOM, firmware, bring-up or related evidence work, read `.claude/skills/component-spec-audit/SKILL.md`, run its offline validator and resolve each exact MPN/LCSC/function through its inventory. Load every matching owner bundle and the integration rules required by CLAUDE.md. Missing evidence stays missing.
3. Run applicable baseline checks, including `pnpm circuit:check`, before and after edits. Read current package scripts and the relevant firmware/native/check procedure; never report unavailable or unrun checks as passed. Do not hand-edit generated component pages, previews or receipts.
4. For multi-session work or expensive computation, follow [ORCHESTRATION.md](ORCHESTRATION.md), maintain [the current mapping](orchestration/current-plan.md), and fill [a bounded task brief](templates/orchestration-task.md) before admission.
5. Review actual source changes and required test/native evidence before integration. Current-state, firmware receipts, manufacturing handoff and physical checklists retain their existing ownership and scope. Routine work already covered by the request needs no repeated generic approval; unresolved product choices and new external/physical actions do.

The 2026-11-12 known DNS incident has the narrow prioritization rule in ORCHESTRATION, not a blanket verification waiver. This workflow entry starts no task and changes no design, tool pin or CI gate.
