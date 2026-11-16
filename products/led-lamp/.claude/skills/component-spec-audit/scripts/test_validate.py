import copy
import hashlib
import io
import json
import importlib.util
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("component_spec_validate", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ComponentSpecValidatorTests(unittest.TestCase):
    def setUp(self):
        self.schema = validator.load(validator.REFS / "schema.json")
        self.inventory_data = validator.load(validator.REFS / "inventory.json")
        self.lines = validator.validate_inventory(self.inventory_data)

    def test_power_switch_identity_is_jlcpcb_and_not_external(self):
        switch = next(line for line in self.lines if line["lcsc"] == "C5446803")
        self.assertEqual(switch["mpn"], "SS-12D01-G020")
        self.assertNotEqual(switch.get("mounting"), "external")
        self.assertEqual(validator.resolve("G-Switch SS-12D01-G020", self.lines), ["line-c5446803"])
        for change in ("blank-lcsc", "wrong-mpn"):
            data = copy.deepcopy(self.inventory_data)
            line = next(line for line in data["lines"] if line["lcsc"] == "C5446803")
            if change == "blank-lcsc": line["lcsc"] = ""
            else: line["mpn"] = "WR11AS"
            with self.assertRaises(validator.ContractError):
                validator.validate_inventory(data)

    def test_power_switch_pin_map_cannot_claim_wrong_pcb_footprint(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        mapping = next(m for m in aggregate["pin_maps"] if m["record_id"] == "rec-c5446803")
        mapping["footprint"] = "R0603"
        with self.assertRaises(validator.ContractError):
            validator.validate_pin_assets(aggregate, self.lines)

    def test_power_switch_rejects_a_fused_rail_bypass(self):
        import sys
        sys.path.insert(0, str(validator.ROOT / "scripts/schgen"))
        import verify_power_switch
        verify_power_switch.check_topology(verify_power_switch.spec.NETS)
        broken = copy.deepcopy(verify_power_switch.spec.NETS)
        broken["V15_FUSED"].remove("F1.2")
        broken["V15"].append("F1.2")
        with self.assertRaises(AssertionError):
            verify_power_switch.check_topology(broken)

    def test_full_offline_contract(self):
        self.assertEqual(validator.validate_all(), self.inventory_data["assertions"]["orderable_lines"])

    def test_template_has_human_component_reference(self):
        validator.validate_template_skill()

    def test_inventory_counts_and_exclusions(self):
        assertions = self.inventory_data["assertions"]
        self.assertEqual(len(self.lines), assertions["orderable_lines"])
        self.assertEqual(sum(not line["dnp"] for line in self.lines), assertions["fitted_lines"])
        self.assertEqual(sum(line["dnp"] for line in self.lines), assertions["dnp_or_hand_fit_lines"])
        self.assertEqual(len(self.inventory_data["exclusions"]), 4)

    def test_all_routing_cases_are_direct(self):
        validator.validate_routing(self.lines)
        fixture = validator.load(validator.FIXTURES / "direct-routing.json")
        self.assertEqual({case["line_id"] for case in fixture["cases"]}, {line["line_id"] for line in self.lines})

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
        project.update({"provenance":"CALCULATED", "depends_on":["fact-golden-margin"], "expression":"fact_golden_margin"})
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
            validator.validate_bundle(bundle, self.schema, True)

    def test_primary_and_calculated_pass_require_available_primary_leaves(self):
        bundle = validator.template_bundle()
        primary = bundle["facts"][1]
        primary.update({"provenance":"PRIMARY-SPEC", "verdict":"PASS - primary-source confirmed"})
        with self.assertRaisesRegex(validator.ContractError, "AVAILABLE MANUFACTURER_PRIMARY"):
            validator.validate_bundle(bundle, self.schema, True)
        golden = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        next(f for f in golden["facts"] if f["fact_id"] == "fact-golden-margin")["verdict"] = "PASS - primary-source confirmed"
        with self.assertRaisesRegex(validator.ContractError, "dependency closure"):
            validator.validate_pass_trust(golden["facts"], golden["sources"])
        trusted = validator.load(validator.FIXTURES / "golden/critical-facts.json")
        trusted["sources"][0].update({"availability":"AVAILABLE", "authority_class":"MANUFACTURER_PRIMARY"})
        for fact_id in ("fact-golden-limit", "fact-golden-project"):
            next(f for f in trusted["facts"] if f["fact_id"] == fact_id).update({"provenance":"PRIMARY-SPEC", "verdict":"PASS - primary-source confirmed"})
        next(f for f in trusted["facts"] if f["fact_id"] == "fact-golden-margin")["verdict"] = "PASS - primary-source confirmed"
        validator.validate_pass_trust(trusted["facts"], trusted["sources"])

    def test_stale_online_hash_fails_and_removes_download(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "source.pdf"
            with self.assertRaisesRegex(validator.ContractError, "stale online hash"):
                validator.store_and_verify(b"fixture", target, "0" * 64, "src-test")
            self.assertFalse(target.exists())

    def test_subordinate_uses_full_contract(self):
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        validator.validate_bundle(bundle, self.schema, True)
        next(f for f in bundle["facts"] if f["fact_id"] == "fact-child-pin")["locator"] = ""
        with self.assertRaisesRegex(validator.ContractError, "locator"):
            validator.validate_bundle(bundle, self.schema, True)

    def test_subordinate_parent_must_be_local_standalone(self):
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        next(r for r in bundle["records"] if r["record_id"] == "rec-child")["parent_record_id"] = "rec-missing"
        with self.assertRaisesRegex(validator.ContractError, "parent must resolve"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.load(validator.FIXTURES / "valid/subordinate-record.json")
        next(r for r in bundle["records"] if r["record_id"] == "rec-parent")["kind"] = "subordinate"
        next(r for r in bundle["records"] if r["record_id"] == "rec-parent")["parent_record_id"] = "rec-child"
        with self.assertRaisesRegex(validator.ContractError, "parent must resolve"):
            validator.validate_bundle(bundle, self.schema, True)

    def test_bundle_exact_parity_and_record_artifacts(self):
        for manifest_key, message in (("source_ids", "source ID parity"), ("fact_ids", "fact ID parity"), ("interaction_ids", "interaction ID parity")):
            bundle = validator.template_bundle()
            bundle["records"][0][manifest_key].pop()
            with self.assertRaisesRegex(validator.ContractError, message):
                validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["records"][0]["fact_ids"].append(bundle["records"][0]["fact_ids"][0])
        with self.assertRaisesRegex(validator.ContractError, "duplicate fact_ids"):
            validator.validate_bundle(bundle, self.schema, True)
        for key, message in (("routes", "requires routing"), ("coverage", "requires coverage"), ("pin_maps", "requires pin map")):
            bundle = validator.template_bundle()
            bundle[key] = []
            with self.assertRaisesRegex(validator.ContractError, message):
                validator.validate_bundle(bundle, self.schema, True)

    def test_local_routing_fixtures_are_executed(self):
        bundle = validator.template_bundle()
        bundle["routes"][0]["positive"] = ["NOT-A-ROUTE"]
        with self.assertRaisesRegex(validator.ContractError, "positive query"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["routes"][0]["negative"] = ["EXAMPLE-MPN"]
        with self.assertRaisesRegex(validator.ContractError, "negative query"):
            validator.validate_bundle(bundle, self.schema, True)

    def test_open_domains_and_open_coverage_match(self):
        bundle = validator.template_bundle()
        bundle["records"][0]["open_domains"] = ["harness"]
        with self.assertRaisesRegex(validator.ContractError, "open domains"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["coverage"][0]["status"] = "COVERED"
        with self.assertRaisesRegex(validator.ContractError, "open domains"):
            validator.validate_bundle(bundle, self.schema, True)

    def test_open_coverage_blocking_fact_ids_lint_rejects_old_defective_shape(self):
        # The migrated template shape (an OPEN reason that claims UNSOURCED
        # evidence and cites the exact blocking fact) passes outright.
        migrated = validator.template_bundle()
        validator.validate_bundle(migrated, self.schema, True)

        # Old defective shape #1: the field is missing entirely (pre-migration).
        missing_field = copy.deepcopy(migrated)
        del missing_field["coverage"][0]["blocking_fact_ids"]
        with self.assertRaisesRegex(validator.ContractError, "missing keys"):
            validator.validate_bundle(missing_field, self.schema, True)

        # Old defective shape #2: the reason claims unavailable/lower-authority/
        # UNSOURCED evidence (the copy-pasted boilerplate bug) but does not cite
        # any blocking fact, so the claim is not machine-checkable.
        unverifiable_claim = copy.deepcopy(migrated)
        unverifiable_claim["coverage"][0]["reason"] = (
            "Domain remains open because retained evidence is unavailable, lower-authority, or UNSOURCED."
        )
        unverifiable_claim["coverage"][0]["blocking_fact_ids"] = []
        with self.assertRaisesRegex(validator.ContractError, "blocking_fact_ids is empty"):
            validator.validate_bundle(unverifiable_claim, self.schema, True)

        # Old defective shape #3: a cited blocking fact does not actually carry
        # a blocking verdict (e.g. it is really PASS/NOT APPLICABLE with
        # available evidence), so it cannot truthfully keep the domain open.
        non_blocking_member = copy.deepcopy(migrated)
        non_blocking_member["sources"][0]["availability"] = "AVAILABLE"
        non_blocking_member["sources"][0]["sha256"] = hashlib.sha256(b"non-blocking-fixture").hexdigest()
        next(f for f in non_blocking_member["facts"] if f["fact_id"] == "fact-example-pin")["verdict"] = "NOT APPLICABLE"
        with self.assertRaisesRegex(validator.ContractError, "does not carry a blocking verdict"):
            validator.validate_bundle(non_blocking_member, self.schema, True)

        # Old defective shape #4: the reason is reworded to dodge the keyword
        # guard entirely while fact_ids still carries a blocking fact. Only the
        # structural rule catches this one.
        reworded_bypass = copy.deepcopy(migrated)
        reworded_bypass["coverage"][0]["reason"] = "Domain stays open pending inspection of the assembled board."
        reworded_bypass["coverage"][0]["blocking_fact_ids"] = []
        self.assertFalse(validator.OPEN_UNAVAILABLE_CLAIM.search(reworded_bypass["coverage"][0]["reason"]))
        with self.assertRaisesRegex(validator.ContractError, "blocking-verdict facts"):
            validator.validate_bundle(reworded_bypass, self.schema, True)

        # Legitimate empty array: the domain's only fact is NOT APPLICABLE on an
        # available source, so nothing addresses the domain in the blocking
        # sense (the shape of component-stm32g031f8p6's cov-c492404-fit).
        not_applicable_only = copy.deepcopy(reworded_bypass)
        not_applicable_only["sources"][0]["availability"] = "AVAILABLE"
        not_applicable_only["sources"][0]["sha256"] = hashlib.sha256(b"not-applicable-fixture").hexdigest()
        next(f for f in not_applicable_only["facts"] if f["fact_id"] == "fact-example-pin")["verdict"] = "NOT APPLICABLE"
        validator.validate_bundle(not_applicable_only, self.schema, True)

    def test_open_coverage_blocking_fact_ids_lint_passes_on_migrated_data(self):
        for owner in sorted({line["owner_skill"] for line in self.lines}):
            bundle = validator.load_skill_bundle(validator.ROOT / ".claude/skills" / owner)
            for item in bundle["coverage"]:
                self.assertIn("blocking_fact_ids", item, f"{owner}/{item['coverage_id']}: missing blocking_fact_ids")
                if item["status"] == "OPEN" and validator.OPEN_UNAVAILABLE_CLAIM.search(item["reason"]):
                    self.assertTrue(item["blocking_fact_ids"], f"{owner}/{item['coverage_id']}: unverifiable OPEN claim")

    def test_every_owner_directory_and_artifact_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            owners = {line["owner_skill"] for line in self.lines}
            for owner in owners:
                shutil.copytree(validator.ROOT / ".claude/skills" / owner, skills_root / owner)
            validator.validate_local_skills(self.schema, self.lines, skills_root)
            shutil.rmtree(skills_root / sorted(owners)[0])
            with self.assertRaisesRegex(validator.ContractError, "expected exact directories"):
                validator.validate_local_skills(self.schema, self.lines, skills_root)

        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            owners = {line["owner_skill"] for line in self.lines}
            for owner in owners:
                shutil.copytree(validator.ROOT / ".claude/skills" / owner, skills_root / owner)
            (skills_root / sorted(owners)[0] / "facts.json").unlink()
            with self.assertRaisesRegex(validator.ContractError, "missing local manifest files"):
                validator.validate_local_skills(self.schema, self.lines, skills_root)

    def test_available_source_rejects_zero_hash_sentinel(self):
        source = validator.template_bundle()["sources"][0]
        source["availability"] = "AVAILABLE"
        source["sha256"] = validator.ZERO_SHA256
        with self.assertRaisesRegex(validator.ContractError, "all-zero"):
            validator.validate_source(source, self.schema)
        source["availability"] = "SOURCE UNAVAILABLE"
        validator.validate_source(source, self.schema)

    def test_calculated_exponent_is_bounded(self):
        self.assertAlmostEqual(validator.arithmetic("value ** 0.5", {"value": 33}), 33 ** 0.5)
        with self.assertRaisesRegex(validator.ContractError, "safety bound"):
            validator.arithmetic("value ** 1000000", {"value": 33})

    def test_routing_fails_closed_on_conflicts_and_filters(self):
        cases = {
            "0603WAF4700T5E C23162": [],
            "UNI-ROYAL 0603WAF1003T5E": ["line-c25803"],
            "CL31A106KBHNNNE C15849": [],
            "Samsung Electro-Mechanics 0603WAF1003T5E": [],
            "100 kOhm resistor 0603WAF1003T5E": ["line-c25803"],
            "RLP25FEER200": ["line-c459674"],
            "C45783": ["line-c45783"],
            "other-vendor SS26 C999019": [],
            "Vishay SS26 C7420363": [],
            "vishay SS26 C7420363": [],
            "FakeCorp AO3401A C347476": [],
            "fakecorp AO3401A C347476": [],
            "AO3401A from Vishay C347476": [],
            "SS26 by vishay C7420363": [],
            "AOS AO3401A C347476": [],
            "Alpha and Omega AO3401A C347476": [],
            "Toshiba AO3401A C347476": [],
            "AOS C347476": [],
            "Vishay C7420363": [],
            "Board-P AL8860MP-13 C500782": ["line-c500782"],
            "review AL8860MP-13 CTRL pin": ["line-c500782"],
            "inspect AL8860MP-13 CTRL pin": ["line-c500782"],
            "new AL8860MP-13 design": ["line-c500782"],
            "UNI-ROYAL": [],
            "100 kOhm resistor": [],
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(validator.resolve(query, self.lines), expected)

        bundle = validator.load_skill_bundle(validator.ROOT / ".claude/skills/component-project-passives")
        self.assertEqual(validator.resolve_bundle_route("0603WAF4700T5E C23162", bundle["routes"]), [])
        self.assertEqual(validator.resolve_bundle_route("UNI-ROYAL 0603WAF1003T5E", bundle["routes"]), ["rec-c25803"])

    def test_external_vendor_qualifier_artifact_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaisesRegex(validator.ContractError, "is required"):
                validator.external_vendor_tokens(missing)

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
        source.update({"availability":"AVAILABLE", "sha256":hashlib.sha256(payload).hexdigest()})

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

    def test_coverage_and_interaction_trust_fail_closed(self):
        bundle = validator.template_bundle()
        bundle["coverage"][0]["status"] = "COVERED"
        bundle["records"][0]["open_domains"] = []
        with self.assertRaisesRegex(validator.ContractError, "unavailable or UNSOURCED"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["interactions"][0]["verdict"] = "PASS - primary-source confirmed"
        with self.assertRaisesRegex(validator.ContractError, "not trust-closed"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["interactions"][0]["verdict"] = "BLOCKER - deterministic spec violation"
        with self.assertRaisesRegex(validator.ContractError, "not trust-closed"):
            validator.validate_bundle(bundle, self.schema, True)
        bundle = validator.template_bundle()
        bundle["facts"][0]["verdict"] = "BLOCKER - deterministic spec violation"
        with self.assertRaisesRegex(validator.ContractError, "deterministic BLOCKER"):
            validator.validate_bundle(bundle, self.schema, True)

    def test_real_pin_locks_reject_deletion_rename_and_swap(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        locks = validator.load(validator.FIXTURES / "golden/real-pin-maps.json")
        validator.validate_real_pin_locks(aggregate, locks)
        for mutation in ("delete", "rename", "swap"):
            changed = copy.deepcopy(aggregate)
            mapping = next(item for item in changed["pin_maps"] if len(item["pins"]) >= 2)
            if mutation == "delete": mapping["pins"].pop()
            elif mutation == "rename": mapping["pins"][0]["name"] += "_MUTATED"
            else:
                mapping["pins"][0]["footprint_pad"], mapping["pins"][1]["footprint_pad"] = mapping["pins"][1]["footprint_pad"], mapping["pins"][0]["footprint_pad"]
            with self.subTest(mutation=mutation), self.assertRaisesRegex(validator.ContractError, "canonical pin map changed"):
                validator.validate_real_pin_locks(changed, locks)

    def test_pin_maps_match_kicad_symbols_and_footprints(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        validator.validate_pin_assets(aggregate, self.lines)
        changed = copy.deepcopy(aggregate)
        changed["pin_maps"][0]["pins"][0]["footprint_pad"] = "999"
        with self.assertRaisesRegex(validator.ContractError, "differs from KiCad footprint"):
            validator.validate_pin_assets(changed, self.lines)
        for field in ("symbol", "footprint"):
            changed = copy.deepcopy(aggregate)
            changed["pin_maps"][0][field] += "_WRONG"
            with self.subTest(field=field), self.assertRaisesRegex(validator.ContractError, "differs from generator"):
                validator.validate_pin_assets(changed, self.lines)

    def test_integration_calculations_recompute_from_raw_facts(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        validator.validate_integration_artifacts(aggregate)
        for fact_id in ("fact-c25803-resistance", "fact-c22807-resistance", "fact-c14663-capacitance", "fact-high-diode-smaj20a-clamp", "fact-stusb-vdd-absolute-max"):
            changed = copy.deepcopy(aggregate)
            next(fact for fact in changed["facts"] if fact["fact_id"] == fact_id)["value"] *= 2
            with self.subTest(fact_id=fact_id), self.assertRaisesRegex(validator.ContractError, "result is stale"):
                validator.validate_integration_artifacts(changed)
        rules_path = validator.ROOT / ".claude/skills/circuit-spec-integration/references/rules.json"
        rules = validator.load(rules_path)
        calculation = next(item for rule in rules["rules"] for item in rule.get("conditioned_calculations", []) if item["calculation_id"] == "calc-q1-steady-vgs")
        changed_result = copy.deepcopy(calculation)
        changed_result["results"][0]["vgs_v"] = -9.6
        with self.assertRaisesRegex(validator.ContractError, "scenario result is stale"):
            fact_values = {fact_id.replace("-", "_"): next(fact for fact in aggregate["facts"] if fact["fact_id"] == fact_id)["value"] for fact_id in calculation["fact_ids"] if isinstance(next(fact for fact in aggregate["facts"] if fact["fact_id"] == fact_id)["value"], (int, float))}
            scenario = changed_result["results"][0]
            validator.require(validator.arithmetic(changed_result["expression"], {**fact_values, "vbus_v": scenario["vbus_v"]}) == scenario["vgs_v"], "scenario result is stale")
        changed = copy.deepcopy(aggregate)
        changed["pin_maps"][0]["pins"][0]["footprint_pad"], changed["pin_maps"][0]["pins"][1]["footprint_pad"] = changed["pin_maps"][0]["pins"][1]["footprint_pad"], changed["pin_maps"][0]["pins"][0]["footprint_pad"]
        with self.assertRaisesRegex(validator.ContractError, "symbol-pin to footprint-pad"):
            validator.validate_pin_assets(changed, self.lines)

    def test_generator_prose_cannot_confirm_exported_netlist(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        rules_path = validator.ROOT / ".claude/skills/circuit-spec-integration/references/rules.json"
        rules = validator.load(rules_path)
        chain = next(rule for rule in rules["rules"] if rule["domain"] == "source-to-bench-chain")
        generated = next(stage for stage in chain["evidence_chain"] if stage["stage"] == "generated-netlist")
        self.assertEqual(generated["status"], "MIXED")
        changed = copy.deepcopy(aggregate)
        next(fact for fact in changed["facts"] if fact["fact_id"] == generated["fact_ids"][0])["value"] = "nonsense free text"
        generated["status"] = "CONFIRMED"
        with self.assertRaisesRegex(validator.ContractError, "generator prose cannot CONFIRM"):
            validator.validate_evidence_chain(chain, changed)

    def test_critical_fact_review_locks_claim_locator_and_conditions(self):
        aggregate = validator.validate_local_skills(self.schema, self.lines)
        review = validator.load(validator.FIXTURES / "golden/critical-fact-review.json")
        validator.validate_critical_fact_review(aggregate, review)
        changed = copy.deepcopy(aggregate)
        fact_id = review["reviews"][0]["fact_id"]
        next(fact for fact in changed["facts"] if fact["fact_id"] == fact_id)["locator"] += " changed"
        with self.assertRaisesRegex(validator.ContractError, "locator/conditions changed"):
            validator.validate_critical_fact_review(changed, review)
        for field, value in (("value", 104), ("unit", "kV")):
            changed = copy.deepcopy(aggregate)
            next(fact for fact in changed["facts"] if fact["fact_id"] == fact_id)[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(validator.ContractError, "value/unit/evidence lock changed"):
                validator.validate_critical_fact_review(changed, review)
        changed = copy.deepcopy(aggregate)
        source_id = review["reviews"][0]["source_id"]
        next(source for source in changed["sources"] if source["source_id"] == source_id)["evidence_extract"] = "arbitrary"
        with self.assertRaisesRegex(validator.ContractError, "value/unit/evidence lock changed"):
            validator.validate_critical_fact_review(changed, review)
        changed_review = copy.deepcopy(review)
        changed_review["independent_review_passes"][0]["review_log"] = "review-artifacts/missing.md"
        with self.assertRaisesRegex(validator.ContractError, "review-log file is missing"):
            validator.validate_critical_fact_review(aggregate, changed_review)
        changed_review = copy.deepcopy(review)
        changed_review["independent_review_passes"][0]["review_log_sha256"] = "f" * 64
        with self.assertRaisesRegex(validator.ContractError, "review-log hash changed"):
            validator.validate_critical_fact_review(aggregate, changed_review)

    def test_unavailable_source_requires_zero_hash(self):
        source = copy.deepcopy(validator.template_bundle()["sources"][0])
        source["sha256"] = "f" * 64
        with self.assertRaisesRegex(validator.ContractError, "SOURCE UNAVAILABLE must use all-zero"):
            validator.validate_source(source, self.schema)

    def test_distributor_identity_lane_cannot_promote_limits(self):
        bundle = validator.load_skill_bundle(validator.ROOT / ".claude/skills/component-type-c-31-m-17")
        fact = next(item for item in bundle["facts"] if item["provenance"] == "DISTRIBUTOR-IDENTITY")
        validator.validate_bundle(bundle, self.schema)
        for field, value in (("class", "ABSOLUTE_MAXIMUM"), ("verdict", "PASS - primary-source confirmed"), ("provenance", "PRIMARY-SPEC")):
            changed = copy.deepcopy(bundle)
            next(item for item in changed["facts"] if item["fact_id"] == fact["fact_id"])[field] = value
            with self.subTest(field=field), self.assertRaises(validator.ContractError):
                validator.validate_bundle(changed, self.schema, True)
        for field in ("lcsc", "manufacturer", "mpn"):
            changed = copy.deepcopy(bundle)
            next(item for item in changed["facts"] if item["fact_id"] == fact["fact_id"])["value"][field] += "-wrong"
            with self.subTest(identity_field=field), self.assertRaisesRegex(validator.ContractError, "differs from owning record"):
                validator.validate_bundle(changed, self.schema, True)
        changed = copy.deepcopy(bundle)
        next(item for item in changed["facts"] if item["fact_id"] == fact["fact_id"])["value"]["voltage_v"] = 20
        with self.assertRaisesRegex(validator.ContractError, "exact structured identity keys"):
            validator.validate_bundle(changed, self.schema, True)
        changed = copy.deepcopy(bundle)
        next(item for item in changed["facts"] if item["fact_id"] == fact["fact_id"])["value"]["variant"] = "mutated identity parser output"
        with self.assertRaisesRegex(validator.ContractError, "canonical distributor identity extract hash changed"):
            validator.validate_bundle(changed, self.schema)

    def test_malicious_generator_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "executed"
            malicious = root / "spec.py"
            malicious.write_text(
                "COMPONENTS = {'U1': ('SAFE', 'SAFE', 'C1', 'lib:PKG', False, (0, 0))}\n"
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
            path.write_text("COMPONENTS = {}\nNETS = {}\nCOMPONENTS['U1'] = ('X', 'X', 'C1', 'lib:P', False, (0, 0))\n", encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "after NETS"):
                validator.parse_components(path)


if __name__ == "__main__":
    unittest.main()
