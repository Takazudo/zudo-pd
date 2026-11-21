#!/usr/bin/env python3
"""Source-bound, non-adopting C3/C5 review dossier for the private site."""

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
C1 = HERE.parent / "pd-led-20261116-c1"
C3 = HERE.parent / "pd-led-20261116-c3"
DOCS = ROOT / "doc/src/content/docs"
OLD_HOST = "https://zudo-led-lamp.takazudomodular.com"
INPUT_SHA256 = {
    "circuit/orchestration/campaigns/pd-led-20261116-c1/route-map.tsv": "e60f2c64b19957f541d36c66db55c7a66528ea1344950451836376a7a8dba527",
    "circuit/orchestration/campaigns/pd-led-20261116-c1/asset-map.tsv": "456f5d08e14e0a5abd1ad4b36757d396cca31e4457824664c89a2338d7369fa1",
    "circuit/orchestration/campaigns/pd-led-20261116-c1/redirect-map.tsv": "3880ee324ae0950c99f9405c5c99837f285827e528664a040a4e73f0bb158799",
    "circuit/orchestration/campaigns/pd-led-20261116-c3/reconciliation.json": "bc86a479339ed5158609875602b58ef3226ba6141da71a821f79dbf421772195",
    "circuit/orchestration/campaigns/pd-led-20261116-c3/route-contract/result.json": "2921a0d1bce6ab3df261e16d825ed2d6460f769ac69d64b93080735831d795c7",
    "circuit/orchestration/campaigns/pd-led-20261117-integration/c5-link-audit.json": "992b2ad5acf5e8a14f707a844bd72e5cc96c4dc16f0c31e7a2458fd61ae329e8",
    "doc/public/_redirects": "b15d15c5be4c199b8bf20cca6b2ff6b31aa900727d408f3e1b2a2945a5a76f93",
    "products/led-lamp/doc/public/_redirects": "f339b3049300d76937832bea6beff12f0458a51387806c4ecfb198999f88c461",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tsv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def route_exists(route):
    stem = DOCS / route.removeprefix("/docs/").strip("/")
    return any(path.is_file() for path in (
        stem.with_suffix(".md"), stem.with_suffix(".mdx"),
        stem / "index.md", stem / "index.mdx",
    ))


def verify_inputs():
    for name, expected in INPUT_SHA256.items():
        assert sha256(ROOT / name) == expected, f"Locked decision input changed: {name}"
    reconciliation = json.loads((C3 / "reconciliation.json").read_text())
    rebind = json.loads((HERE / "c3-input-rebind.json").read_text())
    for name, expected in reconciliation["source_locks_sha256"].items():
        actual = sha256(ROOT / name)
        if actual == expected:
            continue
        entry = rebind["files"].get(name)
        assert entry and entry["reconciled_sha256"] == expected and entry["current_sha256"] == actual, \
            f"C3 source input changed: {name}"
    verify_rebind_semantics(reconciliation, rebind)
    subprocess.run(["python3", str(HERE / "c5_link_audit.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, check=True)
    accepted = json.loads((C3 / "route-contract/result.json").read_text())
    current = json.loads(subprocess.check_output(
        ["node", str(C3 / "route-contract/check.mjs")], cwd=ROOT, text=True))
    accepted_inspected = accepted.pop("inspected_file_sha256")
    current_inspected = current.pop("inspected_file_sha256")
    # The accepted C3e result stays the baseline; only the delta named in the rebind record may differ.
    delta = rebind["route_contract_delta"]
    for key, change in delta["fields"].items():
        assert accepted[key] == change["accepted"] and current[key] == change["current"], \
            f"C3 route contract delta changed: {key}"
        accepted[key] = change["current"]
    assert current == accepted, "C3 route proposal semantics changed"
    for key, change in delta["inspected_file_sha256"].items():
        assert accepted_inspected[key] == change["accepted"] and current_inspected[key] == change["current"], \
            f"C3 route or installed provider input changed: {key}"
        accepted_inspected[key] = change["current"]
    assert {key for key in current_inspected if current_inspected[key] != accepted_inspected[key]} == {
        "pnpm-lock.yaml"}, "C3 route or installed provider input changed"
    return reconciliation, current_inspected["pnpm-lock.yaml"]


def evidence_ids(value, out):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("id", "record_id", "source_id") and isinstance(item, str):
                out.add(item)
            evidence_ids(item, out)
    elif isinstance(value, list):
        for item in value:
            evidence_ids(item, out)
    return out


def verify_rebind_semantics(reconciliation, rebind):
    """The reconciled LED/PD relationship must survive a rebound PD input unchanged."""
    inventory = json.loads((ROOT / ".claude/skills/component-spec-audit/references/inventory.json").read_text())
    lines = {line["line_id"]: line for line in inventory["lines"]}
    for row in reconciliation["line_reconciliation"]:
        overlap = row["pd_overlap"]
        if overlap is None:
            assert row["led_line_id"] not in lines, f"LED-only line now in PD: {row['led_line_id']}"
            continue
        line = lines.get(overlap["line_id"])
        assert line is not None, f"Reconciled PD line missing: {overlap['line_id']}"
        assert {key: line.get(key) for key in overlap["identity"]} == overlap["identity"], \
            f"Reconciled PD identity changed: {overlap['line_id']}"
        placements = [{"board": p["board"], "refdes": p["refdes"], "dnp": p["dnp"]} for p in line["placements"]]
        assert sorted(placements, key=json.dumps) == sorted(overlap["pd_placements"], key=json.dumps), \
            f"Reconciled PD placements changed: {overlap['line_id']}"
    selection = json.loads((ROOT / "circuit/publication/selection.json").read_text())
    for item in reconciliation["shared_record_evidence_collisions"]:
        assert item["record_id"] in selection["recordIds"], f"Shared record left selection: {item['record_id']}"
    led = set()
    for path in sorted((ROOT / "products/led-lamp/.claude/skills").glob("*/*.json")):
        evidence_ids(json.loads(path.read_text()), led)
    changed = set().union(*(rebind[key] for key in ("pd_record_ids_added", "pd_record_ids_removed",
                                                    "pd_source_ids_added", "pd_source_ids_removed")))
    assert set(selection["recordIds"]) >= set(rebind["pd_record_ids_added"])
    assert not set(selection["recordIds"]) & set(rebind["pd_record_ids_removed"])
    assert not changed & led, f"Rebound PD evidence IDs collide with LED evidence: {sorted(changed & led)}"


def check_redirect_source(row, repository):
    path = ROOT / ("doc/public/_redirects" if repository == "pd"
                   else "products/led-lamp/doc/public/_redirects")
    parts = path.read_text().splitlines()[int(row["line"]) - 1].split()
    assert parts == [row["old_pattern"], row["target"], row["status"]], row


def create():
    c3, current_lock_sha256 = verify_inputs()
    routes = tsv(C1 / "route-map.tsv")
    assets = tsv(C1 / "asset-map.tsv")
    redirects = tsv(C1 / "redirect-map.tsv")
    link_audit = json.loads((HERE / "c5-link-audit.json").read_text())
    route_contract = json.loads((C3 / "route-contract/result.json").read_text())
    proposed_records = {item["legacy_led_route"].rstrip("/"): item["proposed_route"]
                        for item in route_contract["legacy_led_route_map"]}
    assert len(proposed_records) == 35

    identity_conflicts = []
    same_text_overlap = []
    led_only = []
    dnp_placements = []
    for line in c3["line_reconciliation"]:
        overlap = line["pd_overlap"]
        item = {
            "led_line_id": line["led_line_id"],
            "led_mpn": line["identity"]["mpn"],
            "led_record_id": line["led_record_id"],
            "led_identity_state": line["identity"]["identity_state"],
            "led_source_state": line["identity"]["source_state"],
        }
        if overlap is None:
            led_only.append(item)
        elif overlap["identity_field_differences"]:
            item["pd_line_id"] = overlap["line_id"]
            item["different_fields"] = overlap["identity_field_differences"]
            item["led_identity"] = {key: line["identity"][key] for key in item["different_fields"]}
            item["pd_identity"] = {key: overlap["identity"][key] for key in item["different_fields"]}
            identity_conflicts.append(item)
        else:
            same_text_overlap.append(item)
        if line["led_line_dnp"]:
            for placement in line["placements"]:
                assert placement["proposed_dnp"] is True
                dnp_placements.append({
                    "led_line_id": line["led_line_id"],
                    "board_namespace": placement["board_namespace"],
                    "refdes": placement["refdes"],
                    "status": "line flag projected; source BOM/CPL, CAD and assembled fit not accepted",
                })
    assert (len(identity_conflicts), len(same_text_overlap), len(led_only), len(dnp_placements)) == (4, 13, 18, 7)
    cad = [{"relative_path": row["relative_path"], "same_bytes": row["same_bytes"],
            "pd_blob": row["pd_blob"], "led_blob": row["led_blob"],
            "candidate": "preserve separate product CAD roots; pad/pin/model review pending"}
           for row in c3["cad_path_collisions"]]
    assert len(cad) == 21 and sum(not row["same_bytes"] for row in cad) == 20

    route_rows = []
    for row in routes:
        old = row["old_route"].rstrip("/")
        kind = row["class"]
        if kind == "authored":
            assert route_exists(row["proposed_route"]), row
            target = row["proposed_route"]
            status = "development page exists; editorial/fragment/publication review held"
        elif kind == "generated":
            target = proposed_records.get(old)
            if target:
                assert not route_exists(target), ("proposed C3 route became active", target)
            status = ("proposed translated record route; active C3 catalog absent" if target
                      else "generated section route; semantic mapping held")
        else:
            target = None
            assert not route_exists(row["old_route"]), ("raw route became active", row["old_route"])
            status = "raw agent-resource route withheld under PD policy"
        route_rows.append({"old_route": row["old_route"], "class": kind,
                           "candidate_target": target,
                           "pd_route_collision": old in {x.rstrip("/") for x in link_audit["old_routes_colliding_with_pd"]},
                           "status": status})
    assert Counter(row["class"] for row in route_rows) == {"authored": 34, "generated": 39, "raw-resource": 24}
    assert sum(row["class"] == "generated" and row["candidate_target"] is not None for row in route_rows) == 35

    used_assets = Counter(row["asset_source"] for row in link_audit["asset_links"])
    asset_by_source = {row["source_path"]: row for row in assets}
    assert len(assets) == 101 and len(asset_by_source) == 101 and sum(used_assets.values()) == 12 and len(used_assets) == 11
    referenced_assets = []
    for source, references in sorted(used_assets.items()):
        row = asset_by_source[source]
        assert not row["pd_same_relative_path"]
        assert not (ROOT / "doc/public" / row["proposed_public_path"].lstrip("/")).exists(), source
        referenced_assets.append({"source_path": source,
                                  "old_host_url": OLD_HOST + source.removeprefix("doc/public"),
                                  "candidate_public_path": row["proposed_public_path"],
                                  "references": references,
                                  "status": "retain old-host link; per-asset PD publication decision held"})
    asset_classes = Counter("redirect-file" if row["source_path"] == "doc/public/_redirects" else
                            "generated-preview" if "held generated snapshot" in row["publication_decision"] else
                            "manual-held" for row in assets)
    assert asset_classes == {"redirect-file": 1, "generated-preview": 51, "manual-held": 49}
    assert all(not (ROOT / "doc/public" / row["proposed_public_path"].lstrip("/")).exists()
               for row in assets if row["proposed_public_path"].startswith("/assets/led-lamp/"))

    aliases = []
    for row in redirects:
        check_redirect_source(row, row["repository"])
        if row["repository"] != "led":
            continue
        old = row["old_pattern"].rstrip("/")
        assert not route_exists(row["old_pattern"]), row
        target = proposed_records.get(row["target"].rstrip("/"))
        aliases.append({"old_pattern": row["old_pattern"], "legacy_target": row["target"],
                        "candidate_target": target,
                        "status": ("generated record target held until C3 active catalog" if target else
                                   "raw resource target held from automatic publication")})
    assert len(redirects) == 52 and len(aliases) == 12
    assert sum(row["candidate_target"] is not None for row in aliases) == 6

    return {
        "schema": "private-c3-c5-review-v1",
        "source_locks_sha256": INPUT_SHA256,
        "c3_source_locks_verified": len(c3["source_locks_sha256"]),
        "current_pnpm_lock_sha256": current_lock_sha256,
        "counts": {
            "identity_conflicts": 4, "same_text_overlap_unverified": 13, "led_only_candidates": 18,
            "led_line_dnp_placement_projections": 7,
            "cad_path_collisions": 21, "cad_different_bytes": 20,
            "authored_development_routes": 34, "authored_pd_old_route_collisions": 3,
            "generated_routes_held": 39, "generated_record_route_candidates_held": 35,
            "raw_resource_routes_held": 24,
            "referenced_asset_links_held": 12, "distinct_referenced_assets_held": 11,
            "manual_assets_held": 49, "generated_preview_assets_held": 51,
            "pd_redirects_retained": 40, "led_aliases_held": 12,
            "led_record_aliases_with_candidate_target": 6, "led_raw_resource_aliases_held": 6,
        },
        "identity_conflicts": identity_conflicts,
        "same_text_overlap": same_text_overlap,
        "led_only": led_only,
        "dnp_placements": dnp_placements,
        "cad_path_collisions": cad,
        "routes": route_rows,
        "referenced_assets": referenced_assets,
        "asset_classes": dict(sorted(asset_classes.items())),
        "led_aliases": aliases,
        "decision": "candidate dispositions only; no identity, CAD, DNP fit, route, redirect, asset or publication adoption",
    }


def md_cell(value):
    text = str(value)
    assert "|" not in text and "\n" not in text
    return text


def markdown(result):
    out = [
        "---", "title: C3 and C5 decision review", "sidebar_position: 4", "---", "",
        "# C3 and C5 decision review", "",
        "> **Source-bound review record.** These rows identify proposed translations and held decisions; they are not a shared part/CAD approval, an assembled-fit finding or a publication selection.",
        "", "## Exact component identity", "",
        "The 17 overlapping LED line IDs include 13 equal-text identity candidates that still need source, pin, CAD and use review. Four have the following field conflicts. The 18 LED-only lines remain product-scoped candidates.",
        "", "| LED line / part | Different field(s) | LED text | PD text | Recommendation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result["identity_conflicts"]:
        out.append("| " + " | ".join(map(md_cell, (
            f'{row["led_line_id"]} / {row["led_mpn"]}', ", ".join(row["different_fields"]),
            "; ".join(f'{k}={v}' for k, v in row["led_identity"].items()),
            "; ".join(f'{k}={v}' for k, v in row["pd_identity"].items()),
            "Keep distinct; require owner evidence",
        ))) + " |")
    out += [
        "", "## LED line DNP projection", "",
        "Seven placement rows inherit four historical LED line DNP flags. The dated export check shows four Board P exclusions and three requested Board L/SWD connector placements; see the [item evidence review](./item-evidence.mdx). Current design and physical fit remain held.",
        "", "| LED line | Product CAD namespace | Refdes | Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in result["dnp_placements"]:
        out.append("| " + " | ".join(map(md_cell, (row["led_line_id"], row["board_namespace"],
                                                  row["refdes"], "DNP flag projected; fit unverified"))) + " |")
    out += [
        "", "## CAD namespace", "",
        "Twenty-one relative CAD paths collide across PD and LED; 20 have different bytes. Even the one equal-byte project file does not prove package or board equivalence. Keep both roots until pad, symbol pin, body, courtyard and model-locator review.",
        "", "| Relative path | Bytes | Candidate disposition |",
        "| --- | --- | --- |",
    ]
    for row in result["cad_path_collisions"]:
        out.append("| " + " | ".join(map(md_cell, (row["relative_path"],
                                                  "equal" if row["same_bytes"] else "different",
                                                  "Separate PD and LED roots"))) + " |")
    out += [
        "", "## Routes and redirects", "",
        "All 34 historical LED page copies exist. Thirty-five generated record targets have source-bound proposed syntax but no active combined catalog; four generated section routes need semantic review. Twenty-four raw-resource routes stay withheld. Three old authored routes collide with PD and cannot receive blanket redirects on the PD host.",
        "", "| Old LED route already used by PD | Historical copy route |",
        "| --- | --- |",
    ]
    for row in result["routes"]:
        if row["pd_route_collision"]:
            out.append(f'| {md_cell(row["old_route"])} | {md_cell(row["candidate_target"])} |')
    out += [
        "", "The 40 mapped PD redirect lines still match their source positions. All 12 LED aliases stay held: six point to proposed generated record routes and six point to raw resources. Their old-host behavior must be preserved until an approved cutover.",
        "", "| Old LED alias | Proposed target or hold |",
        "| --- | --- |",
    ]
    for row in result["led_aliases"]:
        out.append(f'| {md_cell(row["old_pattern"])} | {md_cell(row["candidate_target"] or "Raw-resource route held")} |')
    out += [
        "", "## Assets referenced by copied authored pages", "",
        "Twelve links refer to 11 distinct LED assets. They stay on the original LED host. A namespaced PD path is only a candidate; none is approved by PD's asset allowlist. The full C1 inventory also holds 49 manual assets and 51 generated previews.",
        "", "| Original LED asset | Candidate PD path | References |",
        "| --- | --- | ---: |",
    ]
    for row in result["referenced_assets"]:
        out.append("| " + " | ".join(map(md_cell, (row["source_path"],
                                                  row["candidate_public_path"], row["references"]))) + " |")
    out += [
        "", "## Choices that still need an owner decision", "",
        "| Target | Options | Recommended next action and impact |",
        "| --- | --- | --- |",
        "| Four conflicting part identities and 13 same-text overlaps | Share identities now; or retain product-scoped records | Retain scoped records until primary source, pin and use evidence is reviewed. This delays one active LED-inclusive generated catalog. |",
        "| Seven DNP placements and 21 CAD path collisions | Adopt common fit/packages now; or keep source namespaces | Keep separate roots and historical line flags; verify BOM/CPL, pads, symbols and models before fitted/package claims. No manufacturing conclusion follows. |",
        "| 34 pages, 39 generated routes, 24 raw routes, 49 manual assets and 12 aliases | Publish all; or approve exact entries | Approve exact pages/assets/redirects under PD's restricted policy. Until then, retain old-host links; the 34 copies are published as historical pages. |",
        "", "The [C3 reconciliation source](https://github.com/Takazudo/zudo-pd/blob/codex/c3-c5-decision-review-20261117-01/circuit/orchestration/campaigns/pd-led-20261116-c3/c3a-reconciliation.md), [C1 maps](https://github.com/Takazudo/zudo-pd/tree/codex/c3-c5-decision-review-20261117-01/circuit/orchestration/campaigns/pd-led-20261116-c1) and [machine-readable review bundle](https://github.com/Takazudo/zudo-pd/blob/codex/c3-c5-decision-review-20261117-01/circuit/orchestration/campaigns/pd-led-20261117-integration/c3-c5-candidates.json) retain exact input paths and hashes. No private vendor documents or local-only STEP are included.", "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = create()
    outputs = {
        HERE / "c3-c5-candidates.json": json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        DOCS / "catalog/review.mdx": markdown(result),
    }
    for path, content in outputs.items():
        if args.write:
            path.write_text(content)
        else:
            assert path.read_text() == content, f"Decision review drift: {path}"
    print(json.dumps(result["counts"], sort_keys=True))
