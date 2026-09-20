import copy
import hashlib
import io
import json
import importlib.util
import re
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("component_spec_validate", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

TEMPLATE_LINE = {
    "line_id": "line-example",
    "mpn": "EXAMPLE-MPN",
    "manufacturer": "Example Manufacturer",
    "lcsc": "C000000",
    "package": "EXAMPLE",
    "owner_skill": "component-example",
    "identity_state": "UNRESOLVED",
    "source_state": "SOURCE UNAVAILABLE",
    "function": "example function",
    "placements": [{"board": "board-a", "refdes": "U1", "dnp": False}],
}
TEMPLATE_CANDIDATE = {
    "candidate_id": "cand-example",
    "mpn": "EXAMPLE-MPN",
    "manufacturer": "Example Manufacturer",
    "lcsc": "C000000",
    "package": "EXAMPLE",
    "function": "example function",
    "owner_skill": "component-example",
    "status": "SHORTLISTED",
    "replaces_line_id": None,
    "rationale": "unit-test candidate",
}


class ComponentSpecValidatorTests(unittest.TestCase):
    def setUp(self):
        self.schema = validator.load(validator.REFS / "schema.json")
        self.synthetic_data = validator.load(validator.SYNTHETIC / "inventory.json")
        self.candidates_data = validator.load(validator.SYNTHETIC / "candidates.json")
        self.lines, self.generated = validator.validate_inventory(
            self.synthetic_data, self.schema, staged=False, root=validator.SYNTHETIC
        )
        self.candidates = validator.validate_candidates(self.candidates_data, self.schema, self.lines, self.generated)

    # --- whole-contract entry points -------------------------------------------------

    def test_full_offline_contract(self):
        summary = validator.validate_all(staged=True)
        inventory = validator.load(validator.REFS / "inventory.json")
        self.assertEqual(summary["lines"], inventory["assertions"]["orderable_lines"])
        self.assertEqual(summary["candidates"], len(validator.load(validator.REFS / "candidates.json")["candidates"]))

    def test_staged_run_reports_every_gate_it_skipped(self):
        summary = validator.validate_all(staged=True)
        if not (validator.ROOT / "scripts/schgen/board_a_spec.py").is_file():
            self.assertTrue(any("generator specs are absent" in note for note in summary["skipped"]))

    def test_template_has_human_component_reference(self):
        validator.validate_template_skill()

    def test_seeded_fixture_suite_is_self_contained(self):
        validator.run_seeded_fixtures(self.schema)

    # --- inventory, placements, and placement-level DNP ------------------------------

    def test_inventory_counts_and_exclusions(self):
        assertions = self.synthetic_data["assertions"]
        placements = [item for line in self.lines for item in line["placements"]]
        self.assertEqual(len(self.lines), assertions["orderable_lines"])
        self.assertEqual(sum(any(not p["dnp"] for p in line["placements"]) for line in self.lines), assertions["fitted_lines"])
        self.assertEqual(sum(any(p["dnp"] for p in line["placements"]) for line in self.lines), assertions["dnp_or_hand_fit_lines"])
        self.assertEqual(sum(not p["dnp"] for p in placements), assertions["fitted_placements"])
        self.assertEqual(sum(p["dnp"] for p in placements), assertions["dnp_placements"])
        self.assertEqual(len(self.synthetic_data["exclusions"]), 1)

    def test_one_orderable_is_dnp_on_one_board_and_fitted_on_the_other(self):
        line = next(line for line in self.lines if line["lcsc"] == "C23186")
        states = {(item["board"], item["refdes"]): item["dnp"] for item in line["placements"]}
        self.assertEqual(states, {("board-a", "R17"): True, ("board-a", "R18"): True, ("board-b", "R3"): False})
        # The line itself carries no DNP state at all; only its placements do.
        self.assertNotIn("dnp", line)

    def test_every_seeded_placement_dnp_mutation_fails_for_expected_reason(self):
        seen = set()
        for path in sorted((validator.FIXTURES / "mutations-inventory").glob("*.json")):
            mutation = validator.load(path)
            if not mutation["mutation"].startswith(("placement", "line-level")):
                continue
            seen.add(mutation["mutation"])
            with self.subTest(mutation=mutation["mutation"]), self.assertRaisesRegex(validator.ContractError, re.escape(mutation["expected_error"])):
                validator.apply_inventory_case(
                    self.schema, self.synthetic_data, self.candidates_data, mutation["base"], mutation["target"], mutation["to"]
                )
        self.assertEqual(seen, {"placement dnp fitted-to-dnp", "placement dnp dnp-to-fitted", "line-level dnp", "placement count assertion"})

    def test_placement_dnp_edit_is_caught_without_generator_specs(self):
        # Staged mode cannot compare against a generator spec, so the reviewed
        # placement counts are what still catches a silent DNP flip.
        changed = copy.deepcopy(self.synthetic_data)
        changed["generator_specs"] = [
            {"board": "board-a", "spec": "absent_board_a_spec.py"},
            {"board": "board-b", "spec": "absent_board_b_spec.py"},
            {"board": "board-p", "spec": "absent_board_p_spec.py"},
        ]
        lines, generated = validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)
        self.assertIsNone(generated)
        self.assertEqual(len(lines), 3)
        # Promoting R17 to fitted leaves both line-granular counts unchanged, because
        # R18 is still DNP and R3 is still fitted. Only the placement counts move.
        validator.set_target(changed, "lines.line-c23186.placements.0.dnp", False)
        with self.assertRaisesRegex(validator.ContractError, "placement count differs from reviewed assertion"):
            validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)

    def test_partially_present_generator_specs_staged_vs_strict(self):
        # While the boards are being built, each board's spec lands in its own
        # worktree, so staged mode validates the present board fully and leaves
        # the absent board's placements unchecked (validate_all prints the
        # STAGED-SKIP). Strict mode still fails closed on a partial pair.
        changed = copy.deepcopy(self.synthetic_data)
        changed["generator_specs"][1] = {"board": "board-b", "spec": "absent_board_b_spec.py"}
        lines, generated = validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)
        self.assertEqual(len(lines), 3)
        # generated covers exactly the lines with a board-a placement; the
        # board-b-only line is not silently invented from the absent spec.
        self.assertEqual(set(generated), {"C23186", "C144397"})
        self.assertTrue(all(item["board"] == "board-a" for entry in generated.values() for item in entry["placements"]))
        with self.assertRaisesRegex(validator.ContractError, "partially present"):
            validator.validate_inventory(changed, self.schema, staged=False, root=validator.SYNTHETIC)

    def test_partially_present_spec_still_catches_present_board_dnp_flip(self):
        # The staged tolerance must not weaken checks on the board that IS
        # present: flipping R17's reviewed DNP still mismatches the generator.
        changed = copy.deepcopy(self.synthetic_data)
        changed["generator_specs"][1] = {"board": "board-b", "spec": "absent_board_b_spec.py"}
        validator.set_target(changed, "lines.line-c23186.placements.0.dnp", False)
        changed["assertions"]["fitted_placements"] += 1
        changed["assertions"]["dnp_placements"] -= 1
        with self.assertRaisesRegex(validator.ContractError, "board/refdes or DNP mismatch"):
            validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)

    def test_generator_specs_must_declare_the_project_boards(self):
        changed = copy.deepcopy(self.synthetic_data)
        changed["generator_specs"][0] = {"board": "board-p", "spec": "board_a_spec.py"}
        with self.assertRaisesRegex(validator.ContractError, "must declare exactly"):
            validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)

    def test_a_hand_written_entry_missing_a_key_reports_a_contract_error(self):
        # These files are written by hand, so a missing key must fail as a contract
        # error the runner prints as FAIL, not as a KeyError traceback.
        for key in ("line_id", "lcsc", "placements"):
            changed = copy.deepcopy(self.synthetic_data)
            del changed["lines"][0][key]
            with self.subTest(key=key), self.assertRaisesRegex(validator.ContractError, "missing keys"):
                validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)
        for key in ("board", "refdes", "reason"):
            changed = copy.deepcopy(self.synthetic_data)
            del changed["exclusions"][0][key]
            with self.subTest(exclusion_key=key), self.assertRaisesRegex(validator.ContractError, "missing keys"):
                validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)
        for key in ("candidate_id", "lcsc", "status"):
            changed = copy.deepcopy(self.candidates_data)
            del changed["candidates"][0][key]
            with self.subTest(candidate_key=key), self.assertRaisesRegex(validator.ContractError, "missing keys"):
                validator.validate_candidates(changed, self.schema, self.lines, self.generated)

    def test_duplicate_placement_across_lines_is_rejected(self):
        changed = copy.deepcopy(self.synthetic_data)
        validator.set_target(changed, "lines.line-c900002.placements.0.refdes", "R3")
        with self.assertRaisesRegex(validator.ContractError, "duplicate placement"):
            validator.validate_inventory(changed, self.schema, staged=True, root=validator.SYNTHETIC)

    # --- replacement candidates ------------------------------------------------------

    def test_every_seeded_candidate_mutation_fails_for_expected_reason(self):
        seen = set()
        for path in sorted((validator.FIXTURES / "mutations-inventory").glob("*.json")):
            mutation = validator.load(path)
            if not mutation["mutation"].startswith("candidate"):
                continue
            seen.add(mutation["mutation"])
            with self.subTest(mutation=mutation["mutation"]), self.assertRaisesRegex(validator.ContractError, re.escape(mutation["expected_error"])):
                validator.apply_inventory_case(
                    self.schema, self.synthetic_data, self.candidates_data, mutation["base"], mutation["target"], mutation["to"]
                )
        self.assertEqual(
            seen,
            {
                "candidate collides with placed line",
                "candidate replaces unknown line",
                "candidate blank rationale",
                "candidate invalid status",
            },
        )

    def test_candidate_placed_by_a_generator_belongs_in_the_inventory(self):
        # Reachable when a generator spec places a part the inventory has not
        # adopted yet: the candidate lane must not absorb a placed orderable.
        with self.assertRaisesRegex(validator.ContractError, "placed by a generator spec"):
            validator.validate_candidates(self.candidates_data, self.schema, [], self.generated | {"C900003": {}})

    def test_candidate_record_keeps_manifest_inventory_parity_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            skill_dir = skills_root / "component-example"
            shutil.copytree(validator.TEMPLATE, skill_dir)
            manifest = json.loads((skill_dir / "manifest.json").read_text())
            manifest["records"][0].update({"line_id": None, "candidate_id": "cand-example"})
            (skill_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            # No inventory line at all, one candidate: strict parity still holds.
            validator.validate_local_skills(self.schema, [], [TEMPLATE_CANDIDATE], staged=False, skills_root=skills_root)
            with self.assertRaisesRegex(validator.ContractError, "claims candidates"):
                validator.validate_local_skills(self.schema, [], [dict(TEMPLATE_CANDIDATE, candidate_id="cand-other")], staged=False, skills_root=skills_root)

    def test_record_sets_exactly_one_of_line_and_candidate(self):
        for line_id, candidate_id in (("line-example", "cand-example"), (None, None)):
            bundle = validator.template_bundle()
            bundle["records"][0].update({"line_id": line_id, "candidate_id": candidate_id})
            with self.subTest(line_id=line_id, candidate_id=candidate_id):
                with self.assertRaisesRegex(validator.ContractError, "exactly one of line_id and candidate_id"):
                    validator.validate_bundle(bundle, self.schema)

    # --- staged vs strict ------------------------------------------------------------

    def test_staged_tolerates_a_missing_owner_directory_and_strict_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            shutil.copytree(validator.TEMPLATE, skills_root / "component-example")
            inventory = [TEMPLATE_LINE, dict(TEMPLATE_LINE, line_id="line-later", lcsc="C000001", owner_skill="component-later")]
            validator.validate_local_skills(self.schema, inventory, staged=True, skills_root=skills_root)
            with self.assertRaisesRegex(validator.ContractError, "expected exact directories"):
                validator.validate_local_skills(self.schema, inventory, staged=False, skills_root=skills_root)

    def test_staged_still_rejects_an_unassigned_component_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            shutil.copytree(validator.TEMPLATE, skills_root / "component-example")
            for staged in (True, False):
                with self.subTest(staged=staged), self.assertRaisesRegex(validator.ContractError, "not assigned any inventory line or candidate"):
                    validator.validate_local_skills(self.schema, [], staged=staged, skills_root=skills_root)

    def test_staged_still_rejects_a_bundle_claiming_a_line_it_does_not_own(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            shutil.copytree(validator.TEMPLATE, skills_root / "component-example")
            foreign = dict(TEMPLATE_LINE, line_id="line-other", owner_skill="component-example")
            with self.assertRaisesRegex(validator.ContractError, "claims inventory lines"):
                validator.validate_local_skills(self.schema, [foreign], staged=True, skills_root=skills_root)

    def test_every_owner_artifact_is_required_in_both_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            shutil.copytree(validator.TEMPLATE, skills_root / "component-example")
            (skills_root / "component-example" / "facts.json").unlink()
            with self.assertRaisesRegex(validator.ContractError, "missing local manifest files"):
                validator.validate_local_skills(self.schema, [TEMPLATE_LINE], staged=True, skills_root=skills_root)

    def test_integration_rules_fail_closed_on_empty_aggregate(self):
        empty = {key: [] for key in ("records", "sources", "facts", "coverage", "routes", "interactions", "pin_maps")}
        if validator.load(validator.INTEGRATION / "references/rules.json")["rules"]:
            with self.assertRaisesRegex(validator.ContractError, "unknown record/fact ID"):
                validator.validate_integration_artifacts(empty, self.schema, staged=True)
        else:
            validator.validate_integration_artifacts(empty, self.schema, staged=True)
            with self.assertRaisesRegex(validator.ContractError, "strict mode requires committed cross-component rules"):
                validator.validate_integration_artifacts(empty, self.schema, staged=False)

    # --- evidence contract -----------------------------------------------------------

    def test_all_routing_cases_are_direct(self):
        fixture = validator.load(validator.SYNTHETIC / "direct-routing.json")
        validator.validate_routing(self.lines, fixture)
        self.assertEqual({case["line_id"] for case in fixture["cases"]}, {line["line_id"] for line in self.lines})
        committed = validator.load(validator.FIXTURES / "direct-routing.json")
        self.assertEqual(len(committed["cases"]), len(validator.load(validator.REFS / "inventory.json")["lines"]))

    def test_every_seeded_mutation_fails_for_expected_reason(self):
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        seen = set()
        for path in sorted((validator.FIXTURES / "mutations").glob("*.json")):
            mutation = validator.load(path)
            seen.add(mutation["mutation"])
            changed = copy.deepcopy(golden)
            validator.set_target(changed, mutation["target"], mutation["to"])
            with self.assertRaisesRegex(validator.ContractError, mutation["expected_error"]):
                validator.validate_golden(changed, self.schema)
        self.assertTrue({"pin", "value", "unit", "condition", "default state", "locator"} <= seen)

    def test_derived_margin_recomputes_and_cycles_fail(self):
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        changed = copy.deepcopy(golden)
        next(f for f in changed["facts"] if f["fact_id"] == "fact-golden-margin")["value"] = 4
        with self.assertRaisesRegex(validator.ContractError, "derived value is stale"):
            validator.validate_golden(changed, self.schema, False)
        changed = copy.deepcopy(golden)
        project = next(f for f in changed["facts"] if f["fact_id"] == "fact-golden-project")
        project.update({"provenance": "CALCULATED", "depends_on": ["fact-golden-margin"], "expression": "fact_golden_margin"})
        with self.assertRaisesRegex(validator.ContractError, "cycle"):
            validator.validate_golden(changed, self.schema, False)

    def test_calculated_expression_dependency_identity_is_exact(self):
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        margin = next(f for f in golden["facts"] if f["fact_id"] == "fact-golden-margin")
        margin["expression"] = "fact_golden_limit"
        with self.assertRaisesRegex(validator.ContractError, "exactly match depends_on"):
            validator.validate_golden(golden, self.schema, False)
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        margin = next(f for f in golden["facts"] if f["fact_id"] == "fact-golden-margin")
        margin["depends_on"] = ["fact-golden-margin"]
        margin["expression"] = "fact_golden_margin"
        with self.assertRaisesRegex(validator.ContractError, "depends on itself"):
            validator.validate_golden(golden, self.schema, False)

    def test_source_unavailable_requires_explicit_state(self):
        bundle = validator.template_bundle()
        bundle["sources"][0]["availability"] = ""
        with self.assertRaisesRegex(validator.ContractError, "availability"):
            validator.validate_bundle(bundle, self.schema)

    def test_primary_and_calculated_pass_require_available_primary_leaves(self):
        bundle = validator.template_bundle()
        primary = bundle["facts"][1]
        primary.update({"provenance": "PRIMARY-SPEC", "verdict": "PASS - primary-source confirmed"})
        with self.assertRaisesRegex(validator.ContractError, "AVAILABLE MANUFACTURER_PRIMARY"):
            validator.validate_bundle(bundle, self.schema)
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        next(f for f in golden["facts"] if f["fact_id"] == "fact-golden-margin")["verdict"] = "PASS - primary-source confirmed"
        with self.assertRaisesRegex(validator.ContractError, "dependency closure"):
            validator.validate_pass_trust(golden["facts"], golden["sources"])
        trusted = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        trusted["sources"][0].update({"availability": "AVAILABLE", "authority_class": "MANUFACTURER_PRIMARY"})
        for fact_id in ("fact-golden-limit", "fact-golden-project"):
            next(f for f in trusted["facts"] if f["fact_id"] == fact_id).update({"provenance": "PRIMARY-SPEC", "verdict": "PASS - primary-source confirmed"})
        next(f for f in trusted["facts"] if f["fact_id"] == "fact-golden-margin")["verdict"] = "PASS - primary-source confirmed"
        validator.validate_pass_trust(trusted["facts"], trusted["sources"])

    def test_stale_online_hash_fails(self):
        with self.assertRaisesRegex(validator.ContractError, "stale online hash"):
            validator.verify_payload(b"fixture", "0" * 64, "src-test")

    def test_subordinate_uses_full_contract(self):
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        validator.validate_bundle(bundle, self.schema)
        next(f for f in bundle["facts"] if f["fact_id"] == "fact-child-pin")["locator"] = ""
        with self.assertRaisesRegex(validator.ContractError, "locator"):
            validator.validate_bundle(bundle, self.schema)

    def test_subordinate_parent_must_be_local_standalone(self):
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        next(r for r in bundle["records"] if r["record_id"] == "rec-child")["parent_record_id"] = "rec-missing"
        with self.assertRaisesRegex(validator.ContractError, "parent must resolve"):
            validator.validate_bundle(bundle, self.schema)
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        parent = next(r for r in bundle["records"] if r["record_id"] == "rec-parent")
        parent.update({"kind": "subordinate", "parent_record_id": "rec-child"})
        with self.assertRaisesRegex(validator.ContractError, "parent must resolve"):
            validator.validate_bundle(bundle, self.schema)

    def test_bundle_exact_parity_and_record_artifacts(self):
        for manifest_key, message in (("source_ids", "source ID parity"), ("fact_ids", "fact ID parity"), ("interaction_ids", "interaction ID parity")):
            bundle = validator.template_bundle()
            bundle["records"][0][manifest_key].pop()
            with self.subTest(manifest_key=manifest_key), self.assertRaisesRegex(validator.ContractError, message):
                validator.validate_bundle(bundle, self.schema)
        bundle = validator.template_bundle()
        bundle["records"][0]["fact_ids"].append(bundle["records"][0]["fact_ids"][0])
        with self.assertRaisesRegex(validator.ContractError, "duplicate fact_ids"):
            validator.validate_bundle(bundle, self.schema)
        for key, message in (("routes", "requires routing"), ("coverage", "requires coverage"), ("pin_maps", "requires pin map")):
            bundle = validator.template_bundle()
            bundle[key] = []
            with self.subTest(key=key), self.assertRaisesRegex(validator.ContractError, message):
                validator.validate_bundle(bundle, self.schema)

    def test_local_routing_fixtures_are_executed(self):
        bundle = validator.template_bundle()
        bundle["routes"][0]["positive"] = ["NOT-A-ROUTE"]
        with self.assertRaisesRegex(validator.ContractError, "positive query"):
            validator.validate_bundle(bundle, self.schema)
        bundle = validator.template_bundle()
        bundle["routes"][0]["negative"] = ["EXAMPLE-MPN"]
        with self.assertRaisesRegex(validator.ContractError, "negative query"):
            validator.validate_bundle(bundle, self.schema)

    def test_open_domains_and_open_coverage_match(self):
        bundle = validator.template_bundle()
        bundle["records"][0]["open_domains"] = ["harness"]
        with self.assertRaisesRegex(validator.ContractError, "open domains"):
            validator.validate_bundle(bundle, self.schema)
        bundle = validator.template_bundle()
        bundle["coverage"][0]["status"] = "COVERED"
        with self.assertRaisesRegex(validator.ContractError, "open domains"):
            validator.validate_bundle(bundle, self.schema)

    def test_open_coverage_blocking_fact_ids_lint_rejects_old_defective_shape(self):
        migrated = validator.template_bundle()
        validator.validate_bundle(migrated, self.schema)

        missing_field = copy.deepcopy(migrated)
        del missing_field["coverage"][0]["blocking_fact_ids"]
        with self.assertRaisesRegex(validator.ContractError, "missing keys"):
            validator.validate_bundle(missing_field, self.schema)

        unverifiable_claim = copy.deepcopy(migrated)
        unverifiable_claim["coverage"][0]["reason"] = (
            "Domain remains open because retained evidence is unavailable, lower-authority, or UNSOURCED."
        )
        unverifiable_claim["coverage"][0]["blocking_fact_ids"] = []
        with self.assertRaisesRegex(validator.ContractError, "blocking_fact_ids is empty"):
            validator.validate_bundle(unverifiable_claim, self.schema)

        non_blocking_member = copy.deepcopy(migrated)
        non_blocking_member["sources"][0]["availability"] = "AVAILABLE"
        non_blocking_member["sources"][0]["sha256"] = hashlib.sha256(b"non-blocking-fixture").hexdigest()
        next(f for f in non_blocking_member["facts"] if f["fact_id"] == "fact-example-pin")["verdict"] = "NOT APPLICABLE"
        with self.assertRaisesRegex(validator.ContractError, "does not carry a blocking verdict"):
            validator.validate_bundle(non_blocking_member, self.schema)

        reworded_bypass = copy.deepcopy(migrated)
        reworded_bypass["coverage"][0]["reason"] = "Domain stays open pending inspection of the assembled board."
        reworded_bypass["coverage"][0]["blocking_fact_ids"] = []
        self.assertFalse(validator.OPEN_UNAVAILABLE_CLAIM.search(reworded_bypass["coverage"][0]["reason"]))
        with self.assertRaisesRegex(validator.ContractError, "blocking-verdict facts"):
            validator.validate_bundle(reworded_bypass, self.schema)

        # Legitimate empty array: the domain's only fact is NOT APPLICABLE on an
        # available source, so nothing addresses the domain in the blocking sense.
        not_applicable_only = copy.deepcopy(reworded_bypass)
        not_applicable_only["sources"][0]["availability"] = "AVAILABLE"
        not_applicable_only["sources"][0]["sha256"] = hashlib.sha256(b"not-applicable-fixture").hexdigest()
        next(f for f in not_applicable_only["facts"] if f["fact_id"] == "fact-example-pin")["verdict"] = "NOT APPLICABLE"
        validator.validate_bundle(not_applicable_only, self.schema)

    def test_available_source_rejects_zero_hash_sentinel(self):
        source = validator.template_bundle()["sources"][0]
        source["availability"] = "AVAILABLE"
        source["sha256"] = validator.ZERO_SHA256
        with self.assertRaisesRegex(validator.ContractError, "all-zero"):
            validator.validate_source(source, self.schema)
        source["availability"] = "SOURCE UNAVAILABLE"
        validator.validate_source(source, self.schema)

    def test_unavailable_source_requires_zero_hash(self):
        source = copy.deepcopy(validator.template_bundle()["sources"][0])
        source["sha256"] = "f" * 64
        with self.assertRaisesRegex(validator.ContractError, "SOURCE UNAVAILABLE must use all-zero"):
            validator.validate_source(source, self.schema)

    def test_calculated_exponent_is_bounded(self):
        self.assertAlmostEqual(validator.arithmetic("value ** 0.5", {"value": 33}), 33 ** 0.5)
        with self.assertRaisesRegex(validator.ContractError, "safety bound"):
            validator.arithmetic("value ** 1000000", {"value": 33})

    def test_coverage_and_interaction_trust_fail_closed(self):
        bundle = validator.template_bundle()
        bundle["coverage"][0]["status"] = "COVERED"
        bundle["records"][0]["open_domains"] = []
        with self.assertRaisesRegex(validator.ContractError, "unavailable or UNSOURCED"):
            validator.validate_bundle(bundle, self.schema)
        for verdict in ("PASS - primary-source confirmed", "BLOCKER - deterministic spec violation"):
            bundle = validator.template_bundle()
            bundle["interactions"][0]["verdict"] = verdict
            with self.subTest(verdict=verdict), self.assertRaisesRegex(validator.ContractError, "not trust-closed"):
                validator.validate_bundle(bundle, self.schema)
        bundle = validator.template_bundle()
        bundle["facts"][0]["verdict"] = "BLOCKER - deterministic spec violation"
        with self.assertRaisesRegex(validator.ContractError, "deterministic BLOCKER"):
            validator.validate_bundle(bundle, self.schema)

    # --- routing ---------------------------------------------------------------------

    def test_routing_fails_closed_on_conflicts_and_filters(self):
        cases = {
            "0603WAF5101T5E": ["line-c23186"],
            "C23186": ["line-c23186"],
            "0603WAF5101T5E C144397": [],
            "B6B-XH-A C23186": [],
            "0603WAF5101T5E C999999": [],
            "JST B6B-XH-A": ["line-c144397"],
            "Vishay B6B-XH-A C144397": [],
            "vishay B6B-XH-A C144397": [],
            "B6B-XH-A from Vishay C144397": [],
            "Vishay C144397": [],
            "board-a 0603WAF5101T5E C23186": ["line-c23186"],
            "board-b FIXTURE-TVS-20A C900002": ["line-c900002"],
            "review the 0603WAF5101T5E placement": ["line-c23186"],
            "JST": [],
            "5.1 kOhm resistor": [],
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(validator.resolve(query, self.lines), expected)

    def test_bundle_routing_uses_the_same_resolver(self):
        routes = validator.template_bundle()["routes"]
        self.assertEqual(validator.resolve_bundle_route("EXAMPLE-MPN", routes), ["rec-example"])
        self.assertEqual(validator.resolve_bundle_route("EXAMPLE-MPN C999999", routes), [])

    def test_external_vendor_qualifier_artifact_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaisesRegex(validator.ContractError, "is required"):
                validator.external_vendor_tokens(missing)

    # --- KiCad asset locks -----------------------------------------------------------

    def test_pin_maps_match_kicad_symbols_and_footprints(self):
        aggregate, inventory, generated = self.kicad_aggregate()
        with tempfile.TemporaryDirectory() as directory:
            symbols, footprints = self.write_kicad_assets(Path(directory))
            validator.validate_pin_assets(aggregate, inventory, generated, self.schema, symbols, footprints)
            changed = copy.deepcopy(aggregate)
            changed["pin_maps"][0]["pins"][0]["footprint_pad"] = "999"
            with self.assertRaisesRegex(validator.ContractError, "differs from KiCad footprint"):
                validator.validate_pin_assets(changed, inventory, generated, self.schema, symbols, footprints)
            for field in ("symbol", "footprint"):
                changed = copy.deepcopy(aggregate)
                changed["pin_maps"][0][field] += "_WRONG"
                with self.subTest(field=field), self.assertRaisesRegex(validator.ContractError, "differs from generator"):
                    validator.validate_pin_assets(changed, inventory, generated, self.schema, symbols, footprints)
            changed = copy.deepcopy(aggregate)
            pins = changed["pin_maps"][0]["pins"]
            pins[0]["footprint_pad"], pins[1]["footprint_pad"] = pins[1]["footprint_pad"], pins[0]["footprint_pad"]
            with self.assertRaisesRegex(validator.ContractError, "symbol-pin to footprint-pad"):
                validator.validate_pin_assets(changed, inventory, generated, self.schema, symbols, footprints)

    def test_pin_assets_skip_unplaced_candidate_records(self):
        aggregate, inventory, generated = self.kicad_aggregate()
        aggregate["records"][0].update({"line_id": None, "candidate_id": "cand-example"})
        with tempfile.TemporaryDirectory() as directory:
            symbols, footprints = self.write_kicad_assets(Path(directory))
            validator.validate_pin_assets(aggregate, inventory, generated, self.schema, symbols, footprints)

    def test_real_pin_locks_reject_deletion_rename_and_swap(self):
        aggregate, _inventory, _generated = self.kicad_aggregate()
        locks = {"locks": [self.pin_lock(aggregate["pin_maps"][0])]}
        validator.validate_real_pin_locks(aggregate, locks, self.schema)
        for mutation in ("delete", "rename", "swap"):
            changed = copy.deepcopy(aggregate)
            mapping = changed["pin_maps"][0]
            if mutation == "delete":
                mapping["pins"].pop()
            elif mutation == "rename":
                mapping["pins"][0]["name"] += "_MUTATED"
            else:
                mapping["pins"][0]["footprint_pad"], mapping["pins"][1]["footprint_pad"] = mapping["pins"][1]["footprint_pad"], mapping["pins"][0]["footprint_pad"]
            with self.subTest(mutation=mutation), self.assertRaisesRegex(validator.ContractError, "canonical pin map changed"):
                validator.validate_real_pin_locks(changed, locks, self.schema)

    def test_pin_lock_trust_status_must_match_its_evidence(self):
        aggregate, _inventory, _generated = self.kicad_aggregate()
        lock = self.pin_lock(aggregate["pin_maps"][0], trust_status="TRUSTED")
        with self.assertRaisesRegex(validator.ContractError, "not primary-source confirmed"):
            validator.validate_real_pin_locks(aggregate, {"locks": [lock]}, self.schema)
        available = copy.deepcopy(aggregate)
        available["sources"][0].update({"availability": "AVAILABLE", "sha256": hashlib.sha256(b"available").hexdigest()})
        for fact in available["facts"]:
            fact.update({"verdict": "NOT APPLICABLE"})
        unsourced = self.pin_lock(available["pin_maps"][0], trust_status="UNSOURCED")
        with self.assertRaisesRegex(validator.ContractError, "non-blocking evidence"):
            validator.validate_real_pin_locks(available, {"locks": [unsourced]}, self.schema)

    # --- generator DSL safety --------------------------------------------------------

    def test_malicious_generator_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "executed"
            malicious = root / "spec.py"
            malicious.write_text(
                "COMPONENTS = {'U1': ('SAFE', 'SAFE', 'C1', 'zudo-pd:PKG', False, (0, 0))}\n"
                f"open({str(marker)!r}, 'w').write('owned')\n"
                "NETS = {}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validator.ContractError, "unsafe generator syntax"):
                validator.parse_components(malicious)
            self.assertFalse(marker.exists())

    def test_generator_dsl_rejects_unsupported_component_syntax(self):
        unsafe = {
            "import": "import os",
            "attribute": "BAD = (1).real",
            "call": "BAD = len([])",
            "comprehension": "BAD = [x for x in []]",
            "lambda": "BAD = lambda: 1",
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, statement in unsafe.items():
                with self.subTest(name=name):
                    path = Path(directory) / f"{name}.py"
                    path.write_text(f"COMPONENTS = {{}}\n{statement}\nNETS = {{}}\n", encoding="utf-8")
                    with self.assertRaisesRegex(validator.ContractError, "unsafe generator syntax"):
                        validator.parse_components(path)

    def test_generator_dsl_rejects_late_component_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "late.py"
            path.write_text("COMPONENTS = {}\nNETS = {}\nCOMPONENTS['U1'] = ('X', 'X', 'C1', 'zudo-pd:P', False, (0, 0))\n", encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "after NETS"):
                validator.parse_components(path)

    def test_generator_footprint_must_use_the_project_library_nickname(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spec.py"
            path.write_text("COMPONENTS = {'U1': ('SYM', 'V', 'C1', 'other-lib:PKG', False, (0, 0))}\nNETS = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "footprint must be zudo-pd"):
                validator.generator_inventory([("board-a", path)], self.schema)
            path.write_text("COMPONENTS = {'U1': ('SYM', 'V', 'C1', 'zudo-pd:PKG', False)}\nNETS = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "generator entry must be"):
                validator.generator_inventory([("board-a", path)], self.schema)

    # --- online refresh --------------------------------------------------------------

    def test_browser_headers_success_and_403_are_explicit(self):
        source = copy.deepcopy(validator.template_bundle()["sources"][0])
        source.update({"availability": "AVAILABLE", "sha256": hashlib.sha256(b"ok").hexdigest()})

        class Response:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self): return b"ok"

        def success(request, timeout):
            self.assertEqual(timeout, validator.HTTP_TIMEOUT_SECONDS)
            self.assertIn("Mozilla/5.0", request.get_header("User-agent"))
            self.assertIn("application/pdf", request.get_header("Accept"))
            return Response()

        self.assertEqual(validator.fetch_source(source, success), b"ok")

        source["request_headers"] = {"Referer": "https://manufacturer.example/product"}

        def referer_success(request, timeout):
            self.assertEqual(timeout, validator.HTTP_TIMEOUT_SECONDS)
            self.assertEqual(request.get_header("Referer"), source["request_headers"]["Referer"])
            return Response()

        self.assertEqual(validator.fetch_source(source, referer_success), b"ok")

        error = urllib.error.HTTPError(source["authoritative_url"], 403, "Forbidden", {}, io.BytesIO(b"forbidden"))

        def forbidden(_request, timeout):
            self.assertEqual(timeout, validator.HTTP_TIMEOUT_SECONDS)
            raise error

        try:
            with self.assertRaises(urllib.error.HTTPError):
                validator.fetch_source(source, forbidden)
        finally:
            error.close()
        source["refresh_policy"] = "VOLATILE-HTML"
        source["refresh_note"] = "live response hash is not deterministic"
        source["authority_class"] = "DISTRIBUTOR_IDENTITY"
        source["identity_extract_sha256"] = "1" * 64
        validator.validate_source(source, self.schema)
        source["authority_class"] = "MANUFACTURER_PRIMARY"
        with self.assertRaisesRegex(validator.ContractError, "limited to canonical distributor identity"):
            validator.validate_source(source, self.schema)

    def test_online_refresh_uses_process_unique_temp_directory(self):
        source = copy.deepcopy(validator.template_bundle()["sources"][0])
        payload = b"stable-refresh-bytes"
        source.update({"availability": "AVAILABLE", "sha256": hashlib.sha256(payload).hexdigest()})

        class Response:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self): return payload

        nested = False

        def outer_opener(_request, timeout):
            nonlocal nested
            self.assertEqual(timeout, validator.HTTP_TIMEOUT_SECONDS)
            if not nested:
                nested = True
                validator.online_sources(self.schema, [source], [source["source_id"]], opener=lambda _request, timeout: Response())
            return Response()

        validator.online_sources(self.schema, [source], [source["source_id"]], opener=outer_opener)

    # --- port hygiene ----------------------------------------------------------------

    def test_no_led_lamp_identifiers_survived_the_port(self):
        forbidden = re.compile(r"board-l\b|zudo-led-lamp|led-lamp|al8860|stm32g031|ap63203|honglitronic", re.I)
        roots = (validator.AUDIT, validator.INTEGRATION)
        offenders = []
        for root in roots:
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path == Path(__file__) or "__pycache__" in path.parts:
                    continue
                match = forbidden.search(path.read_text(encoding="utf-8", errors="ignore"))
                if match:
                    offenders.append(f"{path.relative_to(validator.ROOT)}: {match.group(0)}")
        self.assertEqual(offenders, [])

    # --- helpers ---------------------------------------------------------------------

    def kicad_aggregate(self):
        """Template bundle promoted to a two-pin record with a matching generator entry."""
        aggregate = validator.template_bundle()
        mapping = aggregate["pin_maps"][0]
        mapping.update({"symbol": "FIXTURE-SYM", "footprint": "FIXTURE-PKG"})
        mapping["pins"].append({"symbol_pin": "2", "name": "GND", "footprint_pad": "2", "function": "ground"})
        generated = {"C000000": {"mpn": "EXAMPLE-MPN", "package": "FIXTURE-PKG", "symbols": {"FIXTURE-SYM"}, "placements": []}}
        return aggregate, [TEMPLATE_LINE], generated

    def write_kicad_assets(self, directory):
        symbols = directory / "fixture.kicad_sym"
        symbols.write_text(
            '(kicad_symbol_lib\n  (symbol "FIXTURE-SYM"\n'
            '    (pin passive line (name "IN") (number "1"))\n'
            '    (pin passive line (name "GND") (number "2"))\n  )\n)\n',
            encoding="utf-8",
        )
        footprints = directory / "pretty"
        footprints.mkdir()
        (footprints / "FIXTURE-PKG.kicad_mod").write_text(
            '(footprint "FIXTURE-PKG"\n  (pad "1" smd rect (at 0 0))\n  (pad "2" smd rect (at 1 0))\n)\n',
            encoding="utf-8",
        )
        return symbols, footprints

    def pin_lock(self, mapping, trust_status="UNSOURCED"):
        return {
            "record_id": mapping["record_id"],
            "pin_map_id": mapping["pin_map_id"],
            "canonical_sha256": validator.canonical_pin_map(mapping),
            "evidence_fact_ids": ["fact-example-pin"],
            "trust_status": trust_status,
            "critical_pins": [mapping["pins"][0]],
            "reviewer": "unit-test-reviewer",
        }


if __name__ == "__main__":
    unittest.main()
