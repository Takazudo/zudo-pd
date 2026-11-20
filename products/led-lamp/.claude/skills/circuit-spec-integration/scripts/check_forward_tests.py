#!/usr/bin/env python3
"""Execute cross-component routing and refusal-policy forward tests."""

from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / ".claude/skills/component-spec-audit/scripts/validate.py"
RULES = ROOT / ".claude/skills/circuit-spec-integration/references/rules.json"
CASES = ROOT / ".claude/skills/circuit-spec-integration/references/forward-tests.json"
OBSERVED = ROOT / ".claude/skills/circuit-spec-integration/references/observed-runs.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_observed_run(case, run):
    prompt_bytes = case["prompt"].encode()
    response_bytes = json.dumps(run["response"], sort_keys=True, separators=(",", ":")).encode()
    assert run["case_id"] == case["case_id"] and run["prompt"] == case["prompt"], case["case_id"]
    assert run["prompt_sha256"] == hashlib.sha256(prompt_bytes).hexdigest(), case["case_id"]
    assert run["response_sha256"] == hashlib.sha256(response_bytes).hexdigest() and run["response_sha256"] != "0" * 64, case["case_id"]
    assert run["runner"].strip() and run["model"].strip() and run["run_date"].strip(), case["case_id"]
    assert run["invocation"] == {"skill":"/circuit-spec-integration","tools":"disabled","session_persistence":False,"evidence_packet":"frozen"}, case["case_id"]
    response = run["response"]
    assert response["trigger_skill"] == case["expected_trigger_skill"], case["case_id"]
    assert response["loaded_skills"] == case["expected_loaded_skills"] and response["loaded_skills"], case["case_id"]
    assert response["source_ids"] == case["required_source_ids"] and response["source_ids"], case["case_id"]
    assert response["fact_ids"] == case["required_fact_ids"] and response["fact_ids"], case["case_id"]
    assert response["conditions"] == case["expected_observed_conditions"] and response["conditions"], case["case_id"]
    assert response["calculation_ids"] == case["required_calculation_ids"], case["case_id"]
    assert response["verdicts"] == case["expected_verdicts"] and response["refused"] is case["must_refuse"], case["case_id"]
    assert isinstance(response["refusal"], str) and len(response["refusal"].split()) >= 8, case["case_id"]


def main():
    spec = importlib.util.spec_from_file_location("component_spec_validate", VALIDATOR)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    schema = validator.load(validator.REFS / "schema.json")
    inventory = validator.validate_inventory(validator.load(validator.REFS / "inventory.json"))
    aggregate = validator.validate_local_skills(schema, inventory)
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    sources = {source["source_id"] for source in aggregate["sources"]}
    records = {record["record_id"]: record for record in aggregate["records"]}
    rules = {rule["rule_id"]: rule for rule in load(RULES)["rules"]}
    tests = load(CASES)
    observed_data = load(OBSERVED)
    observed_runs = {run["run_id"]: run for run in observed_data["runs"]}
    assert len(observed_runs) == len(observed_data["runs"]) == len(tests["cases"]), "observed-run exact case parity"

    for case in tests["cases"]:
        selected = [rules[rule_id] for rule_id in case["rule_ids"]]
        run = observed_runs[case["observed_run_id"]]
        selected_record_ids = set().union(*(set(rule["record_ids"]) for rule in selected))
        selected_fact_ids = set().union(*(set(rule["fact_ids"]) for rule in selected))
        selected_calculation_ids = {item["calculation_id"] for rule in selected for item in rule.get("conditioned_calculations", [])}
        assert len(case["prompt"].split()) >= 18, case["case_id"]
        validate_observed_run(case, run)
        response = run["response"]
        assert case["expected_trigger_skill"] == "circuit-spec-integration", case["case_id"]
        assert [rule["verdict"] for rule in selected] == case["expected_verdicts"], case["case_id"]
        assert set(case["direct_record_ids"]) == selected_record_ids, case["case_id"]
        assert set(case["subordinate_record_ids"]) <= set(case["direct_record_ids"]), case["case_id"]
        assert all(records[record_id]["kind"] == "subordinate" for record_id in case["subordinate_record_ids"]), case["case_id"]
        assert set(case["required_source_ids"]) <= sources, case["case_id"]
        assert set(case["required_fact_ids"]) <= selected_fact_ids <= set(facts), case["case_id"]
        assert all(facts[fact_id]["source_id"] in case["required_source_ids"] for fact_id in case["required_fact_ids"]), case["case_id"]
        assert all(facts[fact_id]["conditions"].strip() and facts[fact_id]["locator"].strip() for fact_id in case["required_fact_ids"]), case["case_id"]
        assert set(case["required_calculation_ids"]) <= selected_calculation_ids, case["case_id"]
        assert all(bool(rule["refusal"].strip()) == case["must_refuse"] for rule in selected), case["case_id"]
        for query in case["routing_queries"]:
            assert validator.resolve(query["query"], inventory) == query["expected_line_ids"], case["case_id"]
    for case in tests["negative_routes"]:
        assert validator.resolve(case["query"], inventory) == case["expected_line_ids"], case["query"]
    first_case, first_run = tests["cases"][0], observed_runs[tests["cases"][0]["observed_run_id"]]
    for mutation in ("gardening", "empty-evidence", "missing-skill", "fake-hash"):
        changed_case, changed_run = copy.deepcopy(first_case), copy.deepcopy(first_run)
        if mutation == "gardening": changed_case["prompt"] = "Please water the garden and prune the roses before lunch today."
        elif mutation == "empty-evidence": changed_run["response"]["source_ids"] = []
        elif mutation == "missing-skill": changed_run["response"]["loaded_skills"] = []
        else: changed_run["response_sha256"] = "f" * 64
        try:
            validate_observed_run(changed_case, changed_run)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"observed-run mutation unexpectedly passed: {mutation}")
    print(f"PASS: {len(tests['cases'])} integration cases; {len(tests['negative_routes'])} negative routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
