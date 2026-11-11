# Agent instructions

Read [circuit/WORKFLOW.md](circuit/WORKFLOW.md) first. It is the canonical workflow for this circuit project; this file only points to it.

- Exact-component evidence lives in the owner bundles under `.claude/skills/component-*/`, indexed by `.claude/skills/component-spec-audit/references/inventory.json`. Cross-component rules live in `.claude/skills/circuit-spec-integration/references/rules.json`.
- Run `pnpm circuit:check` before editing and again after.
- Never hand-edit the generated pages under `doc/src/content/docs/components/`; change the evidence and run `pnpm circuit:generate`.

The project hardware and evidence rules in [CLAUDE.md](CLAUDE.md) remain authoritative.

## Development orchestration

For multi-session work or expensive checks, also read [circuit/ORCHESTRATION.md](circuit/ORCHESTRATION.md), [the current task/environment/model mapping](circuit/orchestration/current-plan.md) and [the bounded task template](circuit/templates/orchestration-task.md). These govern cloud-first coordination, shared resources, recovery and the scoped DNS-incident deferral; they do not replace the hardware/evidence rules above or authorize new physical actions.
