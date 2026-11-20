#!/usr/bin/env bash
set -euo pipefail

# Gate a captured `zfb build` log on link warnings.
#
# ## Why this exists instead of `failOnBroken: true`
#
# zfb's `linkValidation` resolves `#fragment` targets against HEADING-derived
# anchors only. Every anchor the zudo-circuit-doc generator emits is an
# `<EvidenceAnchor>` component id, and all three markup forms were probed
# directly: a heading anchor validates, a raw-HTML `id` warns, an MDX component
# id warns. No markup this generator can emit satisfies the checker, so every
# one of those warnings is false — the links do resolve in the built HTML.
#
# That leaves two obvious options, and both are wrong:
#
#   `failOnBroken: true`   fails every build on thousands of false positives;
#   ignore the log         means a genuinely broken HAND-AUTHORED link never
#                          surfaces, which is the failure mode that matters.
#
# What already covers the generated pages is the package's link-integrity
# assertion, which runs on the VIEW MODEL inside generation and is fatal there — it does not care
# what markup the renderers emit. That independence is also why the warning
# COUNT carries no signal: wrapping the evidence tables in a component dropped
# it from 4324 to 2536 with no change in link health, because zfb does not
# descend into JSX flow elements. Nothing here gates on a count, or on any
# expected number.
#
# ## What this suppresses, and what it refuses to
#
# Two classes are suppressed:
#
# 1. A same-page `#fragment` reported against a file in the generated tree.
#
# 2. The three progress messages printed by `doc-history-server` through the
#    plugin host (`[plugin-host stdout] ` on zfb 2.x, `ZB006 plugin-host:stdout: `
#    on zfb 5): resolved content directory, processing count, and generated
#    history count/timing. Plugin stderr is never suppressed. zfb labels all plugin stdout as warnings even though
#    these lines are informational. Match only those complete message shapes;
#    any other plugin stdout remains unexpected and fails this gate.
#
# Everything else fails — including a `zfb warn:` line whose SHAPE is not
# recognised. That last part is deliberate: if zfb changes its warning format,
# an unrecognised line has to turn CI red rather than silently switch this gate
# off.
#
# Known unrecognised shape, deliberately NOT suppressed: @takazudo/zfb >=2.14.0
# prints ``zfb warn: plain CSS import `<path>` was dropped: ...``. If that
# appears, a stylesheet really was dropped from the build — fix the import,
# don't add it here.
#
# ## Liveness, not a count (#127)
#
# The gate must not go silently green when zfb changes how it prints warnings.
# ANSI colour sequences are stripped and `zfb warn:` is matched anywhere on the
# line, so a colourised, timestamped or otherwise prefixed line is still seen.
# zfb >= 5 inserts a diagnostic code (`zfb warn: ZB001 <path>: broken link: ...`);
# only that one code shape is accepted for the generated-anchor class.
#
# Two presence checks then refuse a log this gate cannot have read correctly:
#
#   - the log must contain zfb's build-complete line (`N pages built`), so an
#     empty, truncated or wrong file never passes;
#   - while the generated component tree holds pages, at least one
#     generated-anchor warning must have been recognised. Those warnings are
#     produced by construction today, so seeing none means the warning format
#     or zfb's link validation changed, and the gate needs review rather than
#     a pass.
#
# Neither check compares against an expected number: one recognised line is as
# good as 4492. Set ZFB_LINK_GATE_EXPECT_GENERATED=0 only for a build whose
# generated tree is genuinely empty.
#
# Usage: bash check-zfb-link-warnings.sh <build-log>
#   Locally:  pnpm build 2>&1 | tee /tmp/doc-build.log
#             bash doc/scripts/check-zfb-link-warnings.sh /tmp/doc-build.log

LOG="${1:-}"
if [ -z "$LOG" ] || [ ! -f "$LOG" ]; then
  echo "usage: check-zfb-link-warnings.sh <build-log>" >&2
  exit 2
fi

# The generated tree, as it appears in zfb's absolute warning paths.
GENERATED_TREE='/src/content/docs/components/'

WORK="$(mktemp -d "${TMPDIR:-/tmp}/zfb-link-warnings-XXXXXX")"
cleanup() {
  case "$WORK" in
    */zfb-link-warnings-*) rm -rf "$WORK" ;;
    *) echo "refusing to clean an unexpected work path: $WORK" >&2 ;;
  esac
}
trap cleanup EXIT

KNOWN="$WORK/known-false.txt"
KNOWN_PLUGIN_INFO="$WORK/known-false-plugin-info.txt"
UNEXPECTED="$WORK/unexpected.txt"
: >"$KNOWN"
: >"$KNOWN_PLUGIN_INFO"
: >"$UNEXPECTED"

if ! grep -Eq '[0-9]+ pages built' "$LOG"; then
  echo "build log has no zfb 'pages built' line; refusing to treat it as a checked build: $LOG" >&2
  exit 1
fi

awk -v known="$KNOWN" -v known_plugin_info="$KNOWN_PLUGIN_INFO" \
    -v unexpected="$UNEXPECTED" -v tree="$GENERATED_TREE" '
  BEGIN { prefix = "zfb warn: "; sep = ": broken link: "; esc = sprintf("%c", 27) }
  {
    line = $0
    gsub(esc "\\[[0-9;]*[A-Za-z]", "", line)
    gsub("\r", "", line)
    at_prefix = index(line, prefix)
    if (at_prefix == 0) next
    rest = substr(line, at_prefix + length(prefix))
    # zfb >= 5 diagnostic codes: ZB001 only in front of a broken-link report,
    # ZB006 only in front of plugin-host stdout (checked against the exact
    # doc-history progress messages below). Plugin stderr is never accepted.
    coded = 0
    plugin_stdout = 0
    if (match(rest, /^ZB001 /)) { rest = substr(rest, RLENGTH + 1); coded = 1 }
    else if (match(rest, /^ZB006 plugin-host:stdout: /)) { rest = substr(rest, RLENGTH + 1); plugin_stdout = 1 }
    at = index(rest, sep)
    # Only a legacy absolute path or the stripped ZB001 shape is a link
    # diagnostic. Never interpret plugin payloads or unknown codes as paths.
    if (!plugin_stdout && substr(rest, 1, 1) == "/" && at > 0) {
      path = substr(rest, 1, at - 1)
      target = substr(rest, at + length(sep))
      if (index(path, tree) > 0 && substr(target, 1, 1) == "#") {
        print line > known
        next
      }
    }

    if (coded) { print line > unexpected; next }

    # zfb 2.x labelled plugin stdout `[plugin-host stdout] `; zfb 5 uses the
    # ZB006 code stripped above. Either way only these three messages pass.
    msg = rest
    if (!plugin_stdout) {
      if (index(msg, "[plugin-host stdout] ") != 1) { print line > unexpected; next }
      msg = substr(msg, length("[plugin-host stdout] ") + 1)
    }
    plugin_info = \
      msg ~ /^doc-history-server: content-dir resolved to \/.*\/src\/content\/docs$/ || \
      msg ~ /^Processing default: [0-9]+ files in \/.*\/src\/content\/docs$/ || \
      msg ~ /^Generated [0-9]+ history files in [0-9]+([.][0-9]+)?s$/
    if (plugin_info) {
      print line > known_plugin_info
      next
    }

    print line > unexpected
  }
' "$LOG"

known_count=$(wc -l <"$KNOWN")
known_plugin_info_count=$(wc -l <"$KNOWN_PLUGIN_INFO")
unexpected_count=$(wc -l <"$UNEXPECTED")

if [ "$unexpected_count" -ne 0 ]; then
  echo "$unexpected_count zfb warning(s) outside the known-false class:" >&2
  cat "$UNEXPECTED" >&2
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::error::${unexpected_count} zfb warning(s) are not a known-false class (generated-anchor link or doc-history progress) — a hand-authored link is broken, plugin output changed, or zfb changed its warning format."
  fi
  exit 1
fi

GENERATED_DIR="${ZFB_LINK_GATE_GENERATED_DIR:-$(cd "$(dirname "$0")/.." && pwd)/src/content/docs/components}"
EXPECT_GENERATED="${ZFB_LINK_GATE_EXPECT_GENERATED:-auto}"
if [ "$EXPECT_GENERATED" = "auto" ]; then
  if [ -d "$GENERATED_DIR" ] && find "$GENERATED_DIR" -name '*.mdx' -print -quit | grep -q .; then
    EXPECT_GENERATED=1
  else
    EXPECT_GENERATED=0
  fi
fi
if [ "$EXPECT_GENERATED" = "1" ] && [ "$known_count" -eq 0 ]; then
  echo "no generated-anchor link warning was recognised although generated component pages exist." >&2
  echo "zfb's warning format or link validation changed; review this gate before trusting the build log." >&2
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::error::check-zfb-link-warnings.sh recognised no generated-anchor warning; the zfb warning format may have changed (#127)."
  fi
  exit 1
fi

echo "link check: no zfb warning outside the known-false generated-anchor class"
echo "  suppressed  $known_count same-page fragment warning(s) in $GENERATED_TREE"
echo "              (false by construction — zfb resolves fragments against heading"
echo "               anchors only; the package link-integrity check proves these on the"
echo "               view model. The count tracks markup choices, not link health.)"
echo "  suppressed  $known_plugin_info_count doc-history progress warning(s)"
echo "              (informational plugin stdout that zfb labels as warnings; only"
echo "               the three complete known message shapes are accepted.)"
if [ "$known_count" -gt 0 ]; then
  echo "  sample:"
  head -5 "$KNOWN" | sed 's/^/    /'
fi
if [ "$known_plugin_info_count" -gt 0 ]; then
  echo "  plugin info sample:"
  head -5 "$KNOWN_PLUGIN_INFO" | sed 's/^/    /'
fi
