---
title: Versioning Scheme (X.Y.Z)
sidebar_position: 2
---

<Note title="Historical reference">

This page is retained from the previous design documentation. Parts, geometry,
status and numerical claims may be superseded. Start with the
[current architecture](/docs/architecture/) and verify exact components in the
[catalog](/docs/components/catalog/). See the [archive guide](/docs/archive/) for context.

</Note>

This project uses a custom `X.Y.Z` version, **not** standard semver. The numbers track this
hardware project's real-world milestones rather than software API compatibility.

The current version is stored in the [`VERSION`](https://github.com/Takazudo/zudo-pd/blob/main/VERSION)
file at the repo root. Bumps are done with the project skills `/l-bump-version-x`,
`/l-bump-version-y`, `/l-bump-version-z`.

## What each digit means

| Digit | Name | Meaning | Bump skill |
| --- | --- | --- | --- |
| **X** | Product release | The product's own release version. We haven't shipped a real product yet, so this stays **0**. | `/l-bump-version-x` |
| **Y** | JLCPCB order number | How many times we've ordered a PCBA run from JLCPCB. Lifetime counter — it only ever goes up. | `/l-bump-version-y` |
| **Z** | Local tag | An ad-hoc local checkpoint, tagged whenever we feel a point in the work is worth marking. | `/l-bump-version-z` |

## Bump rules

- **X bump** (`/l-bump-version-x`): a real product release. Sets `Z = 0`. **Keeps Y** (Y is a
  lifetime JLCPCB-order counter, so it does not reset). Creates a git tag **and a GitHub release**.
- **Y bump** (`/l-bump-version-y`): a new JLCPCB order. Sets `Z = 0`. Creates a git tag **and a
  GitHub release**. Do this when placing the next order.
- **Z bump** (`/l-bump-version-z`): a local checkpoint. Creates a **git tag only** (no GitHub
  release).

<Note title="Non-standard: Y is a lifetime counter">

In real semver, the major bump (X) would reset the minor (Y). Here it does **not** — Y is
defined as "Nth JLCPCB order ever," which keeps climbing across product releases. This is
intentional. If you'd rather Y reset on an X bump, change `l-bump-version-x`.

</Note>

## Mapping from the old v1 / v2 / v3 / v4 labels

The project previously called PCBA runs "v1, v2, v3, v4." Those map directly onto **Y**:

| Old label | New version | What it was |
| --- | --- | --- |
| v1 | 0.1.0 | 1st JLCPCB order (powered up; STUSB4500 PD failed — pin 18 NC, pin 22 issues) |
| v2 | 0.2.0 | 2nd JLCPCB order (CC1DB chip-internal short; led to the external-Rd redesign) |
| v3 | 0.3.0 | 3rd JLCPCB order (CC fix worked, but pin 18 VBUS_VS_DISCH tied to GND → PD still failed) |
| **v4** | **0.4.0** | **4th JLCPCB order — current.** pin 18 fixed (`VBUS_IN → R14 470 Ω → pin 18`) |

Older docs that say "v2 / v3 / v4" refer to these JLCPCB orders, i.e. the **Y** digit. New
work should use the `0.Y.Z` form.

## Examples

| Situation | Command | Result |
| --- | --- | --- |
| Placing the 5th JLCPCB order | `/l-bump-version-y` | `0.4.0 → 0.5.0`, tag + GitHub release |
| Marking a local milestone mid-order | `/l-bump-version-z` | `0.4.0 → 0.4.1`, tag only |
| First real product ship | `/l-bump-version-x` | `0.5.2 → 1.5.0`, tag + GitHub release (Y kept) |

## 2-board era: one Y bump per JLCPCB order **event**

Starting with the [2-board split](./board-split-decision.md) (epic #86), the project no
longer orders a single PCBA — each JLCPCB order event now covers **both** Board A
(USB-PD core) and Board B (synth power) at once. This does **not** change the meaning of
Y.

<Note title="One order event = one Y bump, regardless of board count">

**Y counts order events, not physical PCBs.** Ordering Board A and Board B together at
JLCPCB is still a single "Nth JLCPCB order" from this project's point of view, so it gets
**one** `/l-bump-version-y` bump, not two. Bumping Y once per board would double-count
and desync Y from the JLCPCB order history the versioning scheme is meant to track.

</Note>

So placing the 5th JLCPCB order under the 2-board split (Board A + Board B submitted
together) is still `0.4.0 → 0.5.0` — the same single bump as the old single-board flow.

### `jlcpcb-order-snapshots/` naming for a 2-board order

The existing convention is one directory per order — `jlcpcb-order-snapshots/v0_Y_Z/`
(e.g. `v0_4_0/`) — each containing `used-for-order/` (files actually submitted) and
`from-order-detail/` (recovered post-order confirmation artifacts).

For a 2-board order, Board A and Board B are physically separate PCBs with separate
BOM/CPL/Gerber sets, so the snapshot splits into **two sibling directories sharing the
same version prefix**, distinguished by a `-board-a` / `-board-b` suffix:

```
jlcpcb-order-snapshots/
├── v0_5_0-board-a/
│   ├── used-for-order/       ← Board A gerbers/BOM/CPL as submitted
│   └── from-order-detail/    ← Board A recovered order-confirmation artifacts
└── v0_5_0-board-b/
    ├── used-for-order/       ← Board B gerbers/BOM/CPL as submitted
    └── from-order-detail/    ← Board B recovered order-confirmation artifacts
```

Both directories share the `v0_5_0` prefix — same Y, because it is the same order event
— with the `-board-a` / `-board-b` suffix carrying the per-board distinction. This keeps
"Y = Nth JLCPCB order event" intact while giving each board's manufacturing files their
own home, since Board A and Board B never share a BOM, CPL, or Gerber set.
