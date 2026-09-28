# Authoring templates

These templates are **not published**. Copy one into the documentation tree when the activity it describes actually happens; do not publish empty copies to fill the navigation.

## Project documentation templates

The `project-docs/` tree mirrors the site's sections. To use a template, copy it to the same relative path under `doc/src/content/docs/`, give the copy a topic-specific filename, `title`, `description` and `sidebar_position`, and replace the "Not entered" prompts as facts become known. Links inside a template point at the sibling template locations; after copying, keep a link only if its target page exists in the site.

| Template | Use it when | What to enter |
| --- | --- | --- |
| [project/index.mdx](./project-docs/project/index.mdx) | The brief must be rebuilt from scratch (the live brief is already published at `project/index.mdx`) | Purpose, user behavior, constraints, current design revision |
| [project/next-actions.mdx](./project-docs/project/next-actions.mdx) | Resetting the handoff page (the live page is already published) | Current open questions, the next bounded task, blocked work |
| [project/task-request.mdx](./project-docs/project/task-request.mdx) | Delegating a bounded research or implementation task to an agent | Goal, scope, references, outputs and a definition of done |
| [project/change-impact.mdx](./project-docs/project/change-impact.mdx) | Before applying a change with downstream effects (Workflow G) | Affected components, interfaces, generated assets and tests |
| [architecture/overview.mdx](./project-docs/architecture/overview.mdx) | Resetting the architecture overview (the live page is already published) | Functional blocks, operating states, unconfirmed boundaries |
| [architecture/interfaces.mdx](./project-docs/architecture/interfaces.mdx) | Once blocks or connectors are proposed | Power, signal, mechanical and programming boundaries |
| [research/component-candidate.mdx](./project-docs/research/component-candidate.mdx) | Comparing or researching a component (Workflow A) | Research question, criteria, linked evidence, missing proof |
| [decisions/decision.mdx](./project-docs/decisions/decision.mdx) | Making a consequential choice | Alternatives, chosen direction, tradeoffs, evidence and conditions |
| [decisions/sourcing.mdx](./project-docs/decisions/sourcing.mdx) | Assembly or procurement becomes relevant | Population policy, cost reasoning, dated sourcing observations |
| [verification/bring-up.mdx](./project-docs/verification/bring-up.mdx) | Planning or recording one verification run (Workflow F) | Revision, setup, planned checks, results and limits |

For repeated records, duplicate the relevant template with a topic-specific filename. A decision ID identifies a decision across edits; a verification report identifies one execution against one revision, so never overwrite a failed run with a later successful one.

These pages explain intent, rationale and decisions. Exact component identity, sources, facts, pin maps and coverage belong to the owner evidence bundles under `.claude/skills/component-*/`; the component pages under `/docs/components/` are generated from them. Do not maintain a second rating table, pin table or catalog by hand. When an argument needs a number, cite the canonical fact ID and keep its qualifier and conditions.

## CAD asset receipt

| Template | Use it when |
| --- | --- |
| [cad-asset-receipt.json](./cad-asset-receipt.json) | Recording an acquired symbol, footprint or 3D model (Workflow D); save the copy as `circuit/cad-receipts/ASSET_ID.receipt.json` |
| [cad-asset-receipt.md](./cad-asset-receipt.md) | Explains every receipt field and the fidelity classes; copy it beside the JSON only when a longer explanation is needed |

See [WORKFLOW.md](../WORKFLOW.md) for the workflows that use each template and [agent-task-examples.md](../agent-task-examples.md) for short requests that lead to them.
