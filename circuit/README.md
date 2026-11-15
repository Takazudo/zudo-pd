# Circuit documentation runtime

This directory holds the zudo-pd-specific configuration, publication choices,
generation checks and project tests for the installed
`@takazudo/zudo-circuit-doc` package. Read [ARCHITECTURE.md](./ARCHITECTURE.md)
before changing the evidence-to-documentation contract.

The root `circuit.config.ts` maps the real evidence bundles, the three schematic
generator specs, KiCad assets and generated site paths into the package. The
package owns the generic validator, projection, renderer, UI and CLI. Project
publication policy and project-specific regressions stay here. Canonical hardware
and evidence rules remain in root [`CLAUDE.md`](../CLAUDE.md) and
[`WORKFLOW.md`](./WORKFLOW.md).

Run commands from the repository root. `pnpm circuit:check` validates the strict
project evidence and the package contract. `pnpm circuit:generate` regenerates the
component pages and preflight report. `pnpm check` checks output, CAD/model parity
and site types. After a build, `pnpm check:site` checks publication, links and
built output. The complete local gate is `pnpm b4push`; it uses one outer heavy
guard and leaves browser smoke as a separately guarded run.

The generated catalog is committed under `doc/src/content/docs/components/` and
must never be hand-edited. The package preflight report is
`circuit/generated/preflight.json`; selected preview assets are generated under
`doc/public/assets/component-previews/`.

## Development orchestration

The [Moya + Codex Cloud workflow](orchestration/moya-codex-cloud.md) provides the
local operating procedure and prompts. Read [ORCHESTRATION.md](ORCHESTRATION.md)
for policy and [current-plan.md](orchestration/current-plan.md) for the current queue.
Use the [campaign/checkpoint](templates/orchestration-campaign.md) and
[task/result/review](templates/orchestration-task.md) templates for execution records.
