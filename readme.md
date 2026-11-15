# zudo-pd

USB-C PD supplies for modular synthesizers. This is development hardware.

| Stream | Source / purpose |
| --- | --- |
| P15 r1 shared input | `boards/board-p15/board-p15-draft.kicad_pcb`, 15 V / 3 A, LED first then PD15 |
| PD15 | `board-p15 + board-b`, +12 V / 1.2 A, −12 V / 0.8 A, +5 V / 0.5 A targets, not measured ratings |
| PD20 | `board-p + board-b20-draft`, 20 V / 5 A intent, 5 A e-marked cable, no degraded mode |

## Start with the current design

[Current state](doc/src/content/docs/project/current-state.md) owns dated implementation, recorded checks,
order plans, received hardware and remaining work. [Architecture](doc/src/content/docs/architecture/index.mdx)
owns variant responsibilities; [release readiness](doc/src/content/docs/architecture/release-readiness.md) owns gates.
P15 programming acceptance is NOT RUN; PD20 has intent only, no program-ready 20 V binary.

## Documentation

The accepted next step is to bring `zudo-led-lamp` into this repository and maintain
one documentation site and one shared component catalog, using `zudo-circuit-doc`.
The target categories are **Project / Shared P15 / PD15 / PD20 / LED Lamp / Components**.
LED source and its site are still separate; the migration has not started.
See the [super epic #308](https://github.com/Takazudo/zudo-pd/issues/308), [consolidation plan](circuit/orchestration/pd-led-unification.md)
and [Moya + Codex Cloud handoff](circuit/orchestration/moya-codex-cloud.md).

[Documentation site](https://pd.takazudomodular.com) and [current procedures](doc/src/content/docs/project/procedures.mdx).
From the repository root, use the pinned package manager:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

`pnpm b4push` runs the complete guarded repository gate. Software/CAD checks do not qualify hardware.

## Design files

[Board sources](boards/README.md), [manufacturing reference](manufacturing/README.md),
[component catalog](doc/src/content/docs/components/catalog/index.mdx) and
[documentation ownership](circuit/DOCUMENTATION_MAP.md) identify the canonical detail.

Never use Git LFS. Large assembly STEP previews are ignored local derivatives; the
[omission inventory](manufacturing/local-only-assembly-previews.json) records their required hashes.
The fixed P15 package retains historical full-verifier and 151/151 checksum PASS with original STEP;
replay needs matching historical sources and the original local-only file, not later HEAD.

Root v0.4.0, Board A, retired 15 V P r2 and earlier orders remain historical. Received Board B matches the S3 factory
BOM but full physical identity is incomplete; current source has later substitutions. Earlier LED Board P measurements
belong only to those units. See [identity records](manufacturing/as-built-and-controller.md).
