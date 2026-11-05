---
title: Project Brief
sidebar_position: 2
---

zudo-pd develops USB-C PD supplies for modular synthesizers. Two separate products share an adopted STUSB4500
controller direction; P15 is a reusable module, not a third product.

## Electrical targets

| Stream | Input / role | Output demand and evidence boundary |
| --- | --- | --- |
| P15 | 15 V / 3 A shared input, LED first then PD15 | Same population and NVM image; physical acceptance required before either load |
| PD15 | P15 + Board B | +12 V / 1.2 A, −12 V / 0.8 A, +5 V / 0.5 A targets; not measured ratings |
| PD20 | P r3 + B20, 20 V / 5 A with 5 A e-marked cable, no degraded mode | OSC continuous demand 1.7 / 1.6 / 0.3 A; transient and let-through criteria in [PD20](../architecture/pd20.md) |

PD15's 26.5 W target before losses and an adapter's nameplate do not establish startup, ripple, headroom or
thermal capability. PD20 simulation and topology results likewise do not establish measured performance.
Read [current state](./current-state.md) for dated implementation, order and physical evidence, and
[release gates](../architecture/release-readiness.md) for remaining acceptance.

## Renewal decisions

Separate USB-PD input from conversion. Use [P15](../architecture/p15-shared-input.md) for the 15 V path and
[Board P r3](../architecture/pd20.md) for PD20. The common controller and per-unit NVM decisions are adopted;
[separate products](../decisions/index.mdx) supersedes single lineup. Exact component records and executable
connectivity establish current source identity; historical BOMs do not.

## Hardware history

Root combined-board v0.4.0, Board A, retired 15 V P r2 and earlier order/diagnostic records remain history.
Received renewal Board B's factory BOM matches S3; its physical verification is incomplete. The PD-specific P r2
was never built. Earlier LED Board P measurements belong only to those units.
[Board lineage](../architecture/board-p.md) and [current state](./current-state.md) keep these boundaries explicit.
