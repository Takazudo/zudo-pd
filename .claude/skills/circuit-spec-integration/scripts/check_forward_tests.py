#!/usr/bin/env python3
"""Execute cross-component routing and refusal-policy forward tests.

Staged by default like the component validator: it exits 0 on the empty scaffold and
says so. `--strict` requires committed cases and full component-spec parity.

Every check reports through the component validator's require()/ContractError,
so a failure names the exact field that differed (and the checks cannot be
stripped by `python3 -O`, which silently disables bare asserts).
"""

from __future__ import annotations

import argparse
import importlib.util
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / ".claude/skills/component-spec-audit/scripts/validate.py"
RULES = ROOT / ".claude/skills/circuit-spec-integration/references/rules.json"
CASES = ROOT / ".claude/skills/circuit-spec-integration/references/forward-tests.json"
OBSERVED = ROOT / ".claude/skills/circuit-spec-integration/references/observed-runs.json"

FROZEN_INVOCATION = {
    "skill": "/circuit-spec-integration",
    "tools": "disabled",
    "session_persistence": False,
    "evidence_packet": "frozen",
}


# An independent Codex agent may assess only a supplied frozen packet in an
# existing session. Preserve this provenance rather than claiming a fresh CLI run.
FROZEN_MESSAGE_INVOCATION = {
    "skill": "circuit-spec-integration",
    "tools": "not used for assessment",
    "session_persistence": True,
    "evidence_packet": "frozen-message",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_validator():
    spec = importlib.util.spec_from_file_location("component_spec_validate", VALIDATOR)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    return validator


def validate_observed_run(validator, case, run):
    require = validator.require
    case_id = case["case_id"]
    prompt_bytes = case["prompt"].encode()
    response_bytes = json.dumps(run["response"], sort_keys=True, separators=(",", ":")).encode()
    require(run["case_id"] == case_id, f"{case_id}: observed run carries case_id {run['case_id']!r}")
    require(run["prompt"] == case["prompt"], f"{case_id}: observed run prompt differs from the case prompt")
    require(run["prompt_sha256"] == hashlib.sha256(prompt_bytes).hexdigest(), f"{case_id}: prompt_sha256 does not match the case prompt")
    require(run["response_sha256"] == hashlib.sha256(response_bytes).hexdigest(), f"{case_id}: response_sha256 does not match the canonicalized response")
    require(run["response_sha256"] != "0" * 64, f"{case_id}: response_sha256 is the zero placeholder")
    require(run["runner"].strip(), f"{case_id}: runner is blank")
    require(run["model"].strip(), f"{case_id}: model is blank")
    require(run["run_date"].strip(), f"{case_id}: run_date is blank")
    require(run["invocation"] in (FROZEN_INVOCATION, FROZEN_MESSAGE_INVOCATION), f"{case_id}: invocation is not a supported frozen no-tools assessment")
    if run["invocation"] == FROZEN_MESSAGE_INVOCATION:
        require(run.get("independent_assessor") is True and run.get("assessment_scope") == "supplied packet only; no tool inspection", f"{case_id}: message assessment needs explicit independent-assessor provenance")
    response = run["response"]
    require(response["trigger_skill"] == case["expected_trigger_skill"], f"{case_id}: trigger_skill {response['trigger_skill']!r} != expected {case['expected_trigger_skill']!r}")
    require(response["loaded_skills"] == case["expected_loaded_skills"], f"{case_id}: loaded_skills differ from expected_loaded_skills")
    require(response["loaded_skills"], f"{case_id}: loaded_skills is empty")
    require(response["source_ids"] == case["required_source_ids"], f"{case_id}: source_ids differ from required_source_ids")
    require(response["source_ids"], f"{case_id}: source_ids is empty")
    require(response["fact_ids"] == case["required_fact_ids"], f"{case_id}: fact_ids differ from required_fact_ids")
    require(response["fact_ids"], f"{case_id}: fact_ids is empty")
    require(response["conditions"] == case["expected_observed_conditions"], f"{case_id}: conditions differ from expected_observed_conditions")
    require(response["conditions"], f"{case_id}: conditions is empty")
    require(response["calculation_ids"] == case["required_calculation_ids"], f"{case_id}: calculation_ids differ from required_calculation_ids")
    require(response["verdicts"] == case["expected_verdicts"], f"{case_id}: verdicts differ from expected_verdicts")
    require(response["refused"] is case["must_refuse"], f"{case_id}: refused flag does not equal must_refuse")
    require(isinstance(response["refusal"], str) and len(response["refusal"].split()) >= 8, f"{case_id}: refusal must be a sentence of at least 8 words")


def run_checks(validator, staged):
    require = validator.require
    schema, inventory, candidates, generated = validator.load_contract(staged=staged)
    aggregate = validator.validate_local_skills(schema, inventory, candidates, staged=staged)
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    sources = {source["source_id"] for source in aggregate["sources"]}
    records = {record["record_id"]: record for record in aggregate["records"]}
    rules = {rule["rule_id"]: rule for rule in load(RULES)["rules"]}
    tests = load(CASES)
    observed_data = load(OBSERVED)
    observed_runs = {run["run_id"]: run for run in observed_data["runs"]}
    require(len(observed_runs) == len(observed_data["runs"]), "observed-runs: duplicate run_id")
    require(len(observed_data["runs"]) == len(tests["cases"]), f"observed-runs: {len(observed_data['runs'])} runs != {len(tests['cases'])} cases (exact case parity)")
    require(tests["cases"] or staged, "strict mode requires committed forward-test cases")

    for case in tests["cases"]:
        case_id = case["case_id"]
        selected = [rules[rule_id] for rule_id in case["rule_ids"]]
        run = observed_runs[case["observed_run_id"]]
        selected_record_ids = set().union(*(set(rule["record_ids"]) for rule in selected))
        selected_fact_ids = set().union(*(set(rule["fact_ids"]) for rule in selected))
        selected_calculation_ids = {item["calculation_id"] for rule in selected for item in rule.get("conditioned_calculations", [])}
        require(len(case["prompt"].split()) >= 18, f"{case_id}: prompt must be at least 18 words")
        validate_observed_run(validator, case, run)
        if run["invocation"] == FROZEN_MESSAGE_INVOCATION:
            incomplete_provenance = copy.deepcopy(run)
            incomplete_provenance["independent_assessor"] = False
            try:
                validate_observed_run(validator, case, incomplete_provenance)
            except validator.ContractError:
                pass
            else:
                raise validator.ContractError(f"{case_id}: missing independent provenance passed")
        require(case["expected_trigger_skill"] == "circuit-spec-integration", f"{case_id}: expected_trigger_skill must be circuit-spec-integration")
        require([rule["verdict"] for rule in selected] == case["expected_verdicts"], f"{case_id}: selected rules' verdicts differ from expected_verdicts")
        require(set(case["direct_record_ids"]) == selected_record_ids, f"{case_id}: direct_record_ids differ from the union of the selected rules' record_ids")
        require(set(case["subordinate_record_ids"]) <= set(case["direct_record_ids"]), f"{case_id}: subordinate_record_ids must be a subset of direct_record_ids")
        require(all(records[record_id]["kind"] == "subordinate" for record_id in case["subordinate_record_ids"]), f"{case_id}: every subordinate_record_id must name a subordinate-kind record")
        require(set(case["required_source_ids"]) <= sources, f"{case_id}: required_source_ids contains unknown source IDs")
        require(set(case["required_fact_ids"]) <= selected_fact_ids, f"{case_id}: required_fact_ids not all selected by the case's rules")
        require(selected_fact_ids <= set(facts), f"{case_id}: the selected rules reference unknown fact IDs")
        require(all(facts[fact_id]["source_id"] in case["required_source_ids"] for fact_id in case["required_fact_ids"]), f"{case_id}: a required fact's source_id is missing from required_source_ids")
        require(all(facts[fact_id]["conditions"].strip() and facts[fact_id]["locator"].strip() for fact_id in case["required_fact_ids"]), f"{case_id}: a required fact lacks conditions or a locator")
        require(set(case["required_calculation_ids"]) <= selected_calculation_ids, f"{case_id}: required_calculation_ids not selected by the case's rules")
        require(all(bool(rule["refusal"].strip()) == case["must_refuse"] for rule in selected), f"{case_id}: rule refusal-text presence must match must_refuse")
        for query in case["routing_queries"]:
            require(validator.resolve(query["query"], inventory) == query["expected_line_ids"], f"{case_id}: routing query {query['query']!r} did not resolve to expected_line_ids")
    for case in tests["negative_routes"]:
        require(validator.resolve(case["query"], inventory) == case["expected_line_ids"], f"negative route {case['query']!r}: resolution differs from expected_line_ids")
    if tests["cases"]:
        first_case, first_run = tests["cases"][0], observed_runs[tests["cases"][0]["observed_run_id"]]
        for mutation in ("gardening", "empty-evidence", "missing-skill", "fake-hash"):
            changed_case, changed_run = copy.deepcopy(first_case), copy.deepcopy(first_run)
            if mutation == "gardening":
                changed_case["prompt"] = "Please water the garden and prune the roses before lunch today."
            elif mutation == "empty-evidence":
                changed_run["response"]["source_ids"] = []
            elif mutation == "missing-skill":
                changed_run["response"]["loaded_skills"] = []
            else:
                changed_run["response_sha256"] = "f" * 64
            try:
                validate_observed_run(validator, changed_case, changed_run)
            except validator.ContractError:
                pass
            else:
                raise validator.ContractError(f"observed-run mutation unexpectedly passed: {mutation}")
    else:
        print("STAGED-SKIP: no forward-test case is committed; this run proves nothing about cross-component behavior")
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true", help="tolerate the empty scaffold and absent owner skills (default)")
    parser.add_argument("--strict", action="store_true", help="require committed forward tests and full component-spec parity")
    args = parser.parse_args()
    if args.staged and args.strict:
        parser.error("choose --staged or --strict, not both")
    staged = not args.strict

    validator = load_validator()
    try:
        tests = run_checks(validator, staged)
    except (validator.ContractError, json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    mode = "strict" if args.strict else "staged"
    print(f"PASS: mode={mode}; {len(tests['cases'])} integration cases; {len(tests['negative_routes'])} negative routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
