# Provenance of `firmware/board-l/src/`

| Item | Value |
| --- | --- |
| Packet | `packets/v72-codex-knob-averaging-20261025/source/` (V72 "explicit knob averaging") |
| Archive | `supplemental/LED-source-evidence-cloud-handoff.zip` in handoff `claude-circuit-handoff-20261031`; 4,659,867 bytes, SHA256 `e85faff85af2128f0fdc4cfefcc5703e4d1d798d1e10388aa79b47d1f33c2e47` (Library `libfile_7e2b5bea60088191a2c9a80b3a3c2843`, version 0) |
| Files | 64 files under `src/`, byte-identical. All 64 match the `source/…` entries of the packet manifest (`provenance/packet-manifest.json`, copied unchanged) |
| Lineage | V68 input/app composition → V70 disabled-ADC operation config → V71 latched policy / response budget → V72. Earlier packets and failure histories stay in the archive and are not imported |
| Git history | None. The packet came from a local workspace without Git, so no commits are invented |
| Also copied unchanged | `provenance/KNOB-AVERAGING-CONTRACT.md`, `provenance/host-attempt4-result.json`, `provenance/m0plus-object-attempt1-result.json` (all hash-matched to the manifest) |
| Not committed | `host-attempt4/commands.json` (SHA256 `5fd241c3d31cd6b0221877655ac4b3bd80240188acaa3d047bf841c106c1884b`), because it contains local-machine paths. A sanitized summary with basenames only is in `provenance/host-attempt4-commands.sanitized.json` |

No archived binary or object was imported or executed. The delivered Board Ls' actual
programming state is unknown. The user reported no personal programming, and factory
programming and population are not established.
