# V197 — V196 exact-feature contract rebind, UNAPPLIED

Closes the source routing-regression/rebind milestone. Existing V196 PCB, schematic, libraries and project are unchanged. The only contract field changed from retained V165/V167 is board_sha256: V148ec1207594aaf67c510168e95a84886554283ef2409aa33d58decdb5686caa6d1 → V196c191997b3b34856076bc89df435684de5cd15f7636d6e2a216cc7652f4c02ad2. Original_DRC_sha256 deliberately remains V148 provenance; embedded V196-native-numeric-comparison.zip establishes full numerical/location equivalence of all22 diagnostics. No threshold/selector/geometry or acceptance changes.

The corrected V167 UNAPPLIED-rules.kicad_dru.txt, SELECTORS.json, translate.py, proposal.py and geometry helpers are reused unchanged. Rules reproduce identically from the newly bound input. active=false; no .kicad_dru file exists. This is source preparation, not diagnostic activation, an exclusion, native PASS or manufacturing acceptance.

## Checks actually completed on the changed binding

TEST-REBIND.log: exact single-field contract reversal; old contract rejects new PCB/new contract rejects old PCB; modified board/project/old context rejection; all22 complete pad descriptors (UUID/net/shape/placement/size/layers/fullASThash) match; rule text and selectors identical; exact/below-threshold cases and reversed pair identities; modified-net/extra-item rejection; unrelated track width default preserved; no active rule file.

TEST-V196-SELECTORS.log: reused source test against NEW V196 input enumerates all106-pad unordered pairs and matches exactly22;22 reversed pairs;110 identity/type/position mutations;3 stale-input cases including unrelated conductor edit. No native evaluator invoked. These are changed-input tests, not repeated old integrations. No new failure occurred. Prior failures/native receipts remain preserved.

## Existing consumer import/check/commit

Verify member manifest and SOURCE-BINDINGS.json. Keep this whole packet in a separate inert contract/handoff directory; do NOT copy its .txt into any active project .kicad_dru path or modify current project. In that disposable/source directory, the two documented checks are:

    python3 -B test_rebind.py
    python3 -B test_translation.py

No installed KiCad/solver required. Commit only this scoped source/handoff rebind and provenance in the existing repository; no public push/merge, bulk dependencies or project activation. Cloud workspace has no Git ancestry. The V196 import commit ef0178d04fb4e614806702c0b35404fcc57feee2 remains the PCB source identity. No native rerun is authorized/dispatched by this packet. Any later conditional diagnostic run needs this newly reviewed exact-input preflight, honest unchanged-threshold activation diff and a separate coordinator instruction; V167's V148-bound receipt is not transferable.

## Milestone and remaining actual dependencies

1. **Routing-regression milestone closed within scope:** complete connectivity/source checks and actual V196 no-fill DRC show the same22 FULL records as V148 (numeric values and locations), no new short/mask/artwork/unconnected findings. Original22 remain visible:18 U1 .1500/.2000 and4 J1 .1751/.2099 versus.2500. V195 solver strategy stays stopped. No further routing tweak is warranted by these records.
2. **Candidate selection / verification boundary:** V196 remains an isolated unadopted successor. This contract is inert. Conditional diagnostic activation and canonical/manufacturing selection have NOT occurred; a future clean conditional result would still not prove hardware acceptance.
3. **Process assumption already decided, not reopened:** user permits proceeding on feasibility of U1 .150mm copper/.110mm nominal mask web and printed J1 land/NPTH pattern. Preserve order-time questions only, no pre-order outreach. Finished mask/dam, stencil/paste and mixed shell/SMT process remain supplier/assembly qualifications, not grounds to silently alter lands. Two .1751mm GND/NPTH gaps remain below retained .20mm published guidance; working assumption is not confirmed capability/tolerance margin.
4. **Fit evidence:** CC1 via now has .45mm nominal planar separation from retained15-A STEP projection, eliminating dependence on the earlier .125mm vertical gap. ExactGF equivalence, placement/finished-surface tolerances and actual assembled clearance are not measured. ProductionL CAD hole/header alignment and polarity are supported; actual spacer height/backside/plug clearance still need physical assembly evidence. No energizing/physical work authorized here.
5. **Electrical acceptance:** preserve existing RILM1.27k (about2.625A nominal threshold),15V/3A planning contract and oneP→oneL arrangement. Current-sharing/copper/plating/ambient-rise and actual load bounds remain qualified, not implied by geometric checks. V159–V163 startup/hot-SW2 closure assessment remains conditional; AP63203 primary EN/UVLO/startup guarantees remain unavailable after403 and cannot be retrieved by bypass. No part/current-limit changes justified by this rebind.
6. **Delivered BoardL state:** user reported no personal programming/modifications. Release source and retainedV72 firmware behavior support intended ATT/PDOK-open design; factory programming and actual population are not established by that history. Do not redoV71/V72 or claim hardware flashed/functional.

These dependencies do not undo completed source routing. No new user decision is requested by this packet, and no repetitive study or execution is queued.
