"""Per-page current-context notes for the 25 self-contained LED copies.

The source body is retained. These notes prevent dated design and deployment
instructions from being mistaken for the integrated project's active state.
"""

EDITORIAL = {
    "doc/src/content/docs/architecture/board-p.mdx": (
        "This net table describes the historical LED Board P. The integrated LED path uses "
        "[shared P15](/docs/architecture/p15-shared-input/) instead; the old Board P is neither P15 "
        "nor PD20's Board P r3. Do not use this table as the P15 source or a current build instruction."
    ),
    "doc/src/content/docs/architecture/current-state.mdx": (
        "This LED status page records a dated source-repository checkpoint. Read the integrated "
        "[project current state](/docs/project/current-state/) and "
        "[release gates](/docs/architecture/release-readiness/) for subsequent PD/P15 evidence. "
        "Its unprogrammed and unmeasured statements remain historical evidence, not a new test result."
    ),
    "doc/src/content/docs/architecture/index.mdx": (
        "This is the original LED architecture index. Start with the integrated "
        "[LED Lamp section](/docs/led-lamp/) and [shared P15](/docs/architecture/p15-shared-input/) "
        "before following the historical Board P links below."
    ),
    "doc/src/content/docs/architecture/next-steps.mdx": (
        "This is the original handover worklist, not the current integration queue. "
        "Board L, firmware and P15 status must be checked against the dated "
        "[LED checkpoint](./current-state.mdx) and the integrated "
        "[project current state](/docs/project/current-state/) before assigning work."
    ),
    "doc/src/content/docs/architecture/overview.mdx": (
        "The original two-board drawing uses the historical LED Board P. The integrated input "
        "is [P15 r1](/docs/architecture/p15-shared-input/) with Board L as its LED consumer. "
        "Keep the Board P connector and load claims below in their source-era scope."
    ),
    "doc/src/content/docs/architecture/power-switch.mdx": (
        "This Board L switch design is retained for source history. Its electrical and mechanical "
        "behavior is not a measured lamp qualification; use the "
        "[release gates](/docs/architecture/release-readiness/) before treating it as accepted hardware."
    ),
    "doc/src/content/docs/getting-started/index.mdx": (
        "This landing belongs to the original LED repository. For the combined checkout, use the "
        "[repository map](/docs/project/repository-map/) and the six-category site navigation. "
        "The source-repository setup links below are retained as history."
    ),
    "doc/src/content/docs/getting-started/installation.mdx": (
        "The 'create a new project' steps below are scaffold instructions, not installation steps "
        "for this combined repository. Use the root `pnpm install --frozen-lockfile` and `pnpm dev` "
        "commands in the [repository map](/docs/project/repository-map/); review the root Node/pnpm pins."
    ),
    "doc/src/content/docs/getting-started/introduction.mdx": (
        "This page introduces the old documentation scaffold, not the lamp hardware or the "
        "integrated site architecture. Start with the [project brief](/docs/project/project-brief/) "
        "and [LED Lamp section](/docs/led-lamp/) for product context."
    ),
    "doc/src/content/docs/how-to/ci-cloudflare-setup.mdx": (
        "This is the original LED repository's Cloudflare runbook. Its secrets, workflows, "
        "preview aliases and deployment instructions describe the original LED site, not this "
        "combined site, which deploys through the root workflows. No LED-host redirect or "
        "cutover is authorized here."
    ),
    "doc/src/content/docs/how-to/index.mdx": (
        "The how-to entries below come from the original LED site. Their CI and publication "
        "steps are historical; review the integrated [repository map](/docs/project/repository-map/) "
        "before running commands in this checkout."
    ),
    "doc/src/content/docs/power/board-p-front-end.mdx": (
        "This is the historical LED Board P proposal, including statements that predate its "
        "KiCad implementation. The integrated 15 V input is "
        "[P15](/docs/architecture/p15-shared-input/); do not treat this old net table as P15 "
        "or PD20 r3 connectivity."
    ),
    "doc/src/content/docs/power/charger-compatibility.mdx": (
        "The charger observations below were made for the historical LED Board P context. "
        "They do not qualify P15 r1 or prove a safe first attach. Follow the "
        "[P15 provisioning gates](/docs/architecture/release-readiness/) for the current path."
    ),
    "doc/src/content/docs/power/index.mdx": (
        "This is the historical Board P power section. The integrated LED input is "
        "[shared P15](/docs/architecture/p15-shared-input/); retain the earlier topology "
        "and charger evidence below as source-era rationale."
    ),
    "doc/src/content/docs/power/lessons-from-zudo-pd.mdx": (
        "These are source-era design lessons for the historical Board P. Apply current "
        "component evidence and [P15 release gates](/docs/architecture/release-readiness/) "
        "before using them as present-day build or bring-up instructions."
    ),
    "doc/src/content/docs/research/control-knob.mdx": (
        "This compares historical control options. The selected Board L control and its "
        "remaining physical checks belong to the dated "
        "[LED status](../architecture/current-state.mdx), not to a fresh choice on this page."
    ),
    "doc/src/content/docs/research/control-logic-rail.mdx": (
        "This is option screening for Board L's logic rail. It does not replace the "
        "as-designed Board L source or establish measured regulator margin; compare the "
        "[LED status](../architecture/current-state.mdx) and current CAD before a change."
    ),
    "doc/src/content/docs/research/control-safety.mdx": (
        "These default-off and fault-handling sketches are source-era analysis, not proof of "
        "current firmware or measured failsafe behavior. Consult the "
        "[LED status](../architecture/current-state.mdx) before implementation or testing."
    ),
    "doc/src/content/docs/research/driver-ics.mdx": (
        "The driver list is an option comparison. It does not reopen the recorded Board L "
        "selection or qualify its thermal/current behavior; use the "
        "[LED status](../architecture/current-state.mdx) for the source-era decision."
    ),
    "doc/src/content/docs/research/index.mdx": (
        "The entries below are preserved decision research. They are not a current parts "
        "selection or release claim; begin with the "
        "[LED status](../architecture/current-state.mdx) and [release gates](/docs/architecture/release-readiness/)."
    ),
    "doc/src/content/docs/research/led-candidates.mdx": (
        "These LED combinations were screened before the recorded Board L population. "
        "They are not interchangeable with the existing board or a measured optical/thermal "
        "rating; compare the [LED status](../architecture/current-state.mdx)."
    ),
    "doc/src/content/docs/research/led-interconnect.mdx": (
        "The connector candidates below predate the integrated P15 handoff. The actual "
        "[P15 interface](/docs/architecture/p15-shared-input/) and Board L mating/physical "
        "checks govern any current connection claim."
    ),
    "doc/src/content/docs/research/mcu-candidates.mdx": (
        "This is MCU option research. The recorded Board L target and unflashed firmware "
        "candidate are in the [LED status](../architecture/current-state.mdx); candidate "
        "toolchains below are not programming evidence."
    ),
    "doc/src/content/docs/research/modulation-algorithms.mdx": (
        "These are algorithm sketches, not evidence that a physical Board L was flashed or "
        "measured. Check the [LED status](../architecture/current-state.mdx) and firmware "
        "receipt before claiming a running effect."
    ),
    "doc/src/content/docs/research/thermal-budget.mdx": (
        "This first-pass thermal arithmetic is not a measured enclosure or assembled-board "
        "rating. The [release gates](/docs/architecture/release-readiness/) still require "
        "physical thermal evidence for the integrated hardware."
    ),
}

# Titles shown in navigation must not present source-era operational pages as
# instructions for the integrated checkout. The original title remains in Git.
HISTORICAL_TITLES = {
    "doc/src/content/docs/architecture/board-p.mdx": "Historical LED Board P net table",
    "doc/src/content/docs/architecture/overview.mdx": "Historical LED architecture overview",
    "doc/src/content/docs/getting-started/index.mdx": "Historical LED getting started",
    "doc/src/content/docs/getting-started/installation.mdx": "Historical documentation scaffold installation",
    "doc/src/content/docs/getting-started/introduction.mdx": "Historical documentation scaffold",
    "doc/src/content/docs/how-to/ci-cloudflare-setup.mdx": "Historical LED Cloudflare setup",
    "doc/src/content/docs/how-to/index.mdx": "Historical LED how-to",
    "doc/src/content/docs/power/board-p-front-end.mdx": "Historical LED Board P front end",
    "doc/src/content/docs/power/index.mdx": "Historical LED power context",
}
assert set(HISTORICAL_TITLES) <= set(EDITORIAL)
