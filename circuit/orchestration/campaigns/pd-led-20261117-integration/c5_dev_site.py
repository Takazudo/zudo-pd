#!/usr/bin/env python3
"""Build the private C5 LED page and catalog candidate from locked source.

This does not change canonical evidence, selection, assets or generated records.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DOCS = ROOT / "doc/src/content/docs"
LED = ROOT / "products/led-lamp"
OLD_HOST = "https://zudo-led-lamp.takazudomodular.com"
LINK = re.compile(r"(?:\]\(|\b(?:href|src)=[\"'])(/(?:docs|assets)/[^\s)\"']+)")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
NAV = re.compile(r'<CategoryNav category="[^"]+"\s*/>')
EXTERNAL_URL = re.compile(r"https?://[^\s)\"'<>]+")
# These two legacy LED citations equal PD denied-only alternate-source values.
# Keep the original citation on the historical source page instead of widening
# PD's publication scan allowance or duplicating the URL in this dev site.
HELD_CITATION_SHA256 = {
    "1f57a875abd66c1777cee0b78de591207dc5a5e8e1e9f36e88ae8970b85e8958",
    "ec3a04f1d355445fed808a86e1af02b602b186e8f63bc0d69838a3cb947a7c03",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_rows():
    with (HERE.parent / "pd-led-20261116-c1/route-map.tsv").open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def split_suffix(url):
    match = re.match(r"([^?#]*)(.*)", url)
    assert match
    return match.groups()


def transform_page(source, routes, old_route):
    content = source.read_text()
    assert content.startswith("---\n") and "\n---\n" in content[4:], source
    fence = None
    output = []
    for line in content.splitlines(keepends=True):
        marker = FENCE.match(line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run[0], len(run)
            elif run[0] == fence[0] and len(run) >= fence[1]:
                fence = None
        elif fence is None:
            def replace(match):
                url = match.group(1)
                path, suffix = split_suffix(url)
                if path.startswith("/assets/"):
                    new = OLD_HOST + path
                else:
                    mapped = routes.get(path.rstrip("/"))
                    assert mapped is not None, (source, url)
                    new = (mapped["proposed_route"] if mapped["class"] == "authored"
                           else OLD_HOST + path)  # Held generated/raw routes stay on the old host.
                return match.group(0).replace(url, new + suffix, 1)
            line = LINK.sub(replace, line)
            line = NAV.sub('<CategoryNav category="led-lamp" />', line)
            line = EXTERNAL_URL.sub(
                lambda match: OLD_HOST + old_route if hashlib.sha256(match.group().encode()).hexdigest()
                in HELD_CITATION_SHA256 else match.group(), line)
        output.append(line)
    content = "".join(output)
    boundary = content.index("\n---\n", 4) + len("\n---\n")
    metadata = content[:boundary]
    description = "description: Development migration candidate; historical LED text awaiting unified-site review."
    if re.search(r"^description:", metadata, flags=re.MULTILINE):
        metadata = re.sub(r"^description:.*$", description, metadata, count=1, flags=re.MULTILINE)
    else:
        metadata = metadata.replace("---\n", "---\n" + description + "\n", 1)
    original = source.relative_to(LED).as_posix()
    notice = (
        "\n> **Development migration candidate.** This page preserves historical LED text; "
        "its status and decisions need review before publication. Held legacy citation links "
        "open the original LED page for their exact source. "
        f"[Maintained source](https://github.com/Takazudo/zudo-pd/blob/codex/c5-private-six-category-site-20261117-01/products/led-lamp/{original}) "
        f"and [existing LED site]({OLD_HOST}/docs/).\n"
    )
    return metadata + notice + content[boundary:]


def candidate_catalog(pd, led):
    pd_by_id = {line["line_id"]: line for line in pd["lines"]}
    assert len(pd_by_id) == 129 and len(led["lines"]) == 35
    shared = [line for line in led["lines"] if line["line_id"] in pd_by_id]
    conflicts = [line for line in shared if any(line.get(key) != pd_by_id[line["line_id"]].get(key)
                                               for key in ("manufacturer", "mpn", "package", "lcsc"))]
    assert len(shared) == 17 and len(conflicts) == 4
    lines = [
        "---", "title: LED component candidates", "sidebar_position: 2", "---", "",
        "# LED component candidates", "",
        "> **Development candidate only.** The 35 LED inventory lines below are historical input, not adopted into the PD component evidence or publication selection. Matching IDs do not establish matching parts, packages, pins, source facts or fitted state.",
        "",
        "[PD's reviewed generated records](/docs/components/records/) remain the active catalog. This single catalog entry point keeps LED candidates visible for reconciliation without merging their identities or publishing raw sources.",
        "",
        f"Source inputs: `products/led-lamp/.claude/skills/component-spec-audit/references/inventory.json` (SHA-256 `{digest(LED / '.claude/skills/component-spec-audit/references/inventory.json')}`) and PD inventory (SHA-256 `{digest(ROOT / '.claude/skills/component-spec-audit/references/inventory.json')}`).",
        "",
        "| LED line | Manufacturer / full MPN | Package / LCSC | PD line with same ID | LED fit flag |",
        "| --- | --- | --- | --- | --- |",
    ]
    for line in led["lines"]:
        peer = pd_by_id.get(line["line_id"])
        if peer is None:
            relation = "New candidate; source, pin and CAD review"
        else:
            fields = ("manufacturer", "mpn", "package", "lcsc")
            relation = ("Text conflict; identity unresolved" if any(line.get(k) != peer.get(k) for k in fields)
                        else "Same text; equivalence unverified")
        fit = "Line DNP; placement mapping pending" if line["dnp"] else "Line not DNP; fit unverified"
        cells = (line["line_id"], f'{line["manufacturer"]} / {line["mpn"]}',
                 f'{line["package"]} / {line["lcsc"]}', relation, fit)
        assert all("|" not in str(x) and "\n" not in str(x) for x in cells)
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    lines += [
        "", "The four text conflicts include STUSB4500QTR manufacturer spelling, AO3401A maker identity, SMAJ20A footprint, and PESD24VS1UB suffix and use conditions. The other shared IDs still need evidence, pin and use review. The 18 LED-only lines need full identity and source review. The four LED line DNP flags cover seven placements; this table does not assert assembled fit.",
        "", "[C3 reconciliation](https://github.com/Takazudo/zudo-pd/blob/codex/c5-private-six-category-site-20261117-01/circuit/orchestration/campaigns/pd-led-20261116-c3/c3a-reconciliation.md) records the unresolved obligations. Separate CAD roots and PD's restricted publication selection remain in force.", "",
    ]
    return "\n".join(lines)


def unified_line_catalog(pd, led):
    lines = [
        "---", "title: Unified line review", "sidebar_position: 2", "---", "",
        "# Unified line review", "",
        "> **Private development comparison.** This table shows 129 PD lines and 35 LED source lines together, using product-scoped keys. It is not a shared exact-part decision, active LED selection or manufacturing BOM.",
        "",
        "PD's [generated exact records](/docs/components/records/) retain active authority. [LED candidate details](./led-candidates.mdx) explain the 17 overlapping line IDs and four text conflicts. Matching IDs in this table stay separate rows.",
        "",
        "| Scoped line key | Manufacturer / full MPN | Package / LCSC | Review status | Recorded fit input |",
        "| --- | --- | --- | --- | --- |",
    ]
    for scope, inventory in (("PD", pd), ("LED", led)):
        for line in inventory["lines"]:
            if scope == "PD":
                dnp = sum(bool(placement["dnp"]) for placement in line["placements"])
                non_dnp = len(line["placements"]) - dnp
                fit = f"{non_dnp} non-DNP / {dnp} DNP placement declarations; assembled fit unverified"
                status = "PD active evidence; see generated record"
            else:
                fit = ("Historical line DNP; placement mapping pending" if line["dnp"]
                       else "Historical line not DNP; physical fit unverified")
                status = "LED candidate; identity and source review pending"
            cells = (f'{scope}:{line["line_id"]}', f'{line["manufacturer"]} / {line["mpn"]}',
                     f'{line["package"]} / {line["lcsc"]}', status, fit)
            assert all("|" not in str(value) and "\n" not in str(value) for value in cells)
            lines.append("| " + " | ".join(map(str, cells)) + " |")
    assert len(lines) - 13 == 164, len(lines)
    lines += [
        "", "Both source inventories are unchanged. This table is generated from the same source bytes as the LED detail table; candidate replay fails on source or output drift. CAD roots, record facts, public assets and publication selections are outside this comparison.", "",
    ]
    return "\n".join(lines)


def outputs():
    # The preceding lexical audit is the source-lock and discovered-page gate.
    import subprocess
    subprocess.run(["python3", str(HERE / "c5_link_audit.py")], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    rows = source_rows()
    by_old = {row["old_route"].rstrip("/"): row for row in rows}
    result = {}
    for row in rows:
        if row["class"] != "authored":
            continue
        old = LED / row["source_path"]
        route = row["proposed_route"].removeprefix("/docs/").strip("/")
        # The C1 route stores the filename stem; non-index routes are flat MDX.
        dest = DOCS / route / "index.mdx" if old.name == "index.mdx" else DOCS / (route + ".mdx")
        assert dest not in result, dest
        result[dest] = transform_page(old, by_old, row["old_route"])
    pd = json.loads((ROOT / ".claude/skills/component-spec-audit/references/inventory.json").read_text())
    led = json.loads((LED / ".claude/skills/component-spec-audit/references/inventory.json").read_text())
    result[DOCS / "catalog/led-candidates.mdx"] = candidate_catalog(pd, led)
    result[DOCS / "catalog/lines.mdx"] = unified_line_catalog(pd, led)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    for path, content in generated.items():
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        else:
            assert path.read_text() == content, f"Candidate drift: {path}"
    expected_led = {path for path in generated if path.is_relative_to(DOCS / "led-lamp")}
    expected_led.add(DOCS / "led-lamp/index.mdx")  # Authored development landing.
    actual_led = set((DOCS / "led-lamp").rglob("*.mdx")) | set((DOCS / "led-lamp").rglob("*.md"))
    assert actual_led == expected_led, "Unexpected or missing development LED page"
    print(f"C5 development candidate: {len(generated) - 2} LED pages, 2 catalog tables; {'written' if args.write else 'matched'}")
