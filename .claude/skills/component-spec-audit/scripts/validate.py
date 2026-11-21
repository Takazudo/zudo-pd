#!/usr/bin/env python3
"""Offline-first component skill contract validator (Python standard library only).

Runs staged by default: while board-a and board-b are being built, an inventory owner
whose skill directory does not exist yet and absent generator specs are tolerated, and
every gate that is skipped is printed. `--strict` restores full parity.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = ROOT / ".claude/skills/component-spec-audit"
REFS = AUDIT / "references"
FIXTURES = AUDIT / "fixtures"
SYNTHETIC = FIXTURES / "synthetic"
TEMPLATE = AUDIT / "assets/component-skill-template"
INTEGRATION = ROOT / ".claude/skills/circuit-spec-integration"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z][a-z0-9-]*$")
LCSC = re.compile(r"^C\d+$")
OWNER_SKILL = re.compile(r"^component-[a-z0-9][a-z0-9-]*$")
LOCATOR_DETAIL = re.compile(r"(section|table|figure|row|pin|title block|calculated)", re.I)
OPEN_UNAVAILABLE_CLAIM = re.compile(r"unavailable|lower-authority|UNSOURCED", re.I)
ZERO_SHA256 = "0" * 64

# The surface other scripts may depend on (circuit-spec-integration's
# check_forward_tests.py imports these); renaming anything here is a
# cross-skill breaking change.
__all__ = [
    "ROOT", "REFS", "ContractError", "load", "require", "load_contract",
    "validate_inventory", "validate_candidates", "validate_local_skills",
    "resolve", "validate_all", "verify_payload",
]

HTTP_TIMEOUT_SECONDS = 20
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; zudo-pd-component-spec/1.0)",
    "Accept": "application/pdf,text/plain,text/html;q=0.9,*/*;q=0.8",
}


class ContractError(ValueError):
    pass


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition, message):
    if not condition:
        raise ContractError(message)


def required_keys(obj, keys, context):
    missing = [key for key in keys if key not in obj]
    require(not missing, f"{context}: missing keys {missing}")


def project(schema, key):
    settings = schema["project"]
    require(key in settings, f"schema project settings: missing {key}")
    return settings[key]


def frontmatter(path: Path, expected_name: str):
    require(path.name == "SKILL.md", f"{path}: skill filename must be uppercase SKILL.md")
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"{path}: missing YAML frontmatter")
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ContractError(f"{path}: unterminated frontmatter") from exc
    fields = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    require(fields.get("name") == expected_name, f"{path}: name must equal directory {expected_name}")
    description = fields.get("description", "")
    require(len(description) >= 80 and "use" in description.lower(), f"{path}: description lacks trigger quality")
    require("triggers" not in fields, f"{path}: undocumented triggers key")
    require(fields.get("disable-model-invocation") != "true", f"{path}: model invocation disabled")


class ComponentDsl:
    """Interpret only the declarative COMPONENTS prefix of a generator spec."""

    def __init__(self, path):
        self.path = path
        self.env = {}

    def error(self, node, message):
        line = getattr(node, "lineno", "?")
        raise ContractError(f"{self.path}:{line}: unsafe generator syntax: {message}")

    def value(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            self.error(node, f"unknown name {node.id}")
        if isinstance(node, (ast.Tuple, ast.List)):
            result = []
            for item in node.elts:
                if isinstance(item, ast.Starred):
                    expanded = self.value(item.value)
                    require(isinstance(expanded, (tuple, list)), f"{self.path}:{item.lineno}: starred value must be tuple/list")
                    result.extend(expanded)
                else:
                    result.append(self.value(item))
            return tuple(result) if isinstance(node, ast.Tuple) else result
        if isinstance(node, ast.Dict):
            require(all(key is not None for key in node.keys), f"{self.path}:{node.lineno}: dict unpacking is not allowed")
            return {self.value(key): self.value(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = self.value(node.operand)
            require(isinstance(operand, (int, float)), f"{self.path}:{node.lineno}: unary operand must be numeric")
            return operand if isinstance(node.op, ast.UAdd) else -operand
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv)):
            left, right = self.value(node.left), self.value(node.right)
            require(isinstance(left, (int, float)) and isinstance(right, (int, float)), f"{self.path}:{node.lineno}: arithmetic operands must be numeric")
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            return left // right
        if isinstance(node, ast.JoinedStr):
            parts = []
            for item in node.values:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    parts.append(item.value)
                elif isinstance(item, ast.FormattedValue) and item.conversion == -1 and item.format_spec is None:
                    parts.append(str(self.value(item.value)))
                else:
                    self.error(item, "unsupported f-string field")
            return "".join(parts)
        self.error(node, type(node).__name__)

    def assign(self, target, value):
        if isinstance(target, ast.Name):
            self.env[target.id] = value
            return
        if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == "COMPONENTS":
            require("COMPONENTS" in self.env and isinstance(self.env["COMPONENTS"], dict), f"{self.path}:{target.lineno}: COMPONENTS not initialized")
            self.env["COMPONENTS"][self.value(target.slice)] = value
            return
        self.error(target, "assignment target")

    def statement(self, statement):
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            self.assign(statement.targets[0], self.value(statement.value))
            return
        if isinstance(statement, ast.For):
            require(isinstance(statement.target, ast.Name), f"{self.path}:{statement.lineno}: range target must be a name")
            call = statement.iter
            require(isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "range" and not call.keywords, f"{self.path}:{statement.lineno}: only range loops are allowed")
            args = [self.value(arg) for arg in call.args]
            require(1 <= len(args) <= 3 and all(isinstance(arg, int) for arg in args), f"{self.path}:{statement.lineno}: range args must be integers")
            require(not statement.orelse, f"{self.path}:{statement.lineno}: for-else is not allowed")
            iterations = range(*args)
            require(len(iterations) <= 10_000, f"{self.path}:{statement.lineno}: range loop exceeds safety limit")
            for item in iterations:
                self.env[statement.target.id] = item
                for child in statement.body:
                    self.statement(child)
            return
        self.error(statement, type(statement).__name__)

    def parse(self):
        try:
            tree = ast.parse(self.path.read_text(encoding="utf-8"), filename=str(self.path))
        except SyntaxError as exc:
            raise ContractError(f"{self.path}:{exc.lineno}: unsafe generator syntax: invalid Python") from exc
        for index, statement in enumerate(tree.body):
            if index == 0 and isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                continue
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == "NETS":
                for node in ast.walk(statement.value):
                    if isinstance(node, (ast.Attribute, ast.Lambda, ast.NamedExpr)) or (isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id == "range")):
                        self.error(node, "unsupported executable syntax in ignored NETS declaration")
                for tail in tree.body[index + 1:]:
                    require(not any(((isinstance(node, ast.Name) and node.id == "COMPONENTS") or (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "COMPONENTS")) and isinstance(node.ctx, ast.Store) for node in ast.walk(tail)), f"{self.path}:{getattr(tail, 'lineno', '?')}: COMPONENTS mutation after NETS is not allowed")
                    if isinstance(tail, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.While, ast.If, ast.With, ast.AsyncWith, ast.Try, ast.Expr)):
                        self.error(tail, "unsupported statement after NETS")
                    for node in ast.walk(tail):
                        if isinstance(node, (ast.Attribute, ast.Lambda, ast.NamedExpr, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                            self.error(node, "unsupported syntax after NETS")
                        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id == "range"):
                            self.error(node, "arbitrary call after NETS")
                break
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                self.error(statement, "imports are not allowed")
            self.statement(statement)
        require(isinstance(self.env.get("COMPONENTS"), dict), f"{self.path}: COMPONENTS dictionary missing")
        return self.env["COMPONENTS"]


def parse_components(path):
    return ComponentDsl(Path(path)).parse()


def expected_mpn(symbol, value, lcsc, mpn_from_value):
    if lcsc in mpn_from_value:
        return value
    if re.search(r"_C\d+$", symbol):
        return re.sub(r"_C\d+$", "", symbol)
    return symbol


def generator_specs(data, schema, root, *, staged=True):
    """Resolve the declared board/spec pairs that exist on disk, or None when no
    spec file exists yet. While the boards are being built, staged mode tolerates
    a per-board absence (the caller restricts every generator-derived check to the
    present boards and prints a STAGED-SKIP); strict mode still fails closed on a
    partially present pair."""
    declared = data["generator_specs"]
    require(isinstance(declared, list) and declared, "inventory: generator_specs must be a nonempty list")
    boards = project(schema, "boards")
    for item in declared:
        required_keys(item, ("board", "spec"), "inventory generator spec")
    require([item["board"] for item in declared] == boards, f"inventory: generator_specs must declare exactly {boards} in order")
    pairs = [(item["board"], root / item["spec"]) for item in declared]
    present_pairs = [(board, path) for board, path in pairs if path.is_file()]
    absent = [str(path) for _board, path in pairs if not path.is_file()]
    if not present_pairs:
        return None
    require(not absent or staged, f"inventory: generator specs partially present {absent}")
    return present_pairs


def generator_inventory(pairs, schema):
    grouped, excluded = {}, []
    nickname = project(schema, "library_nickname")
    mpn_from_value = project(schema, "mpn_from_value_lcsc")
    for board, path in pairs:
        components = parse_components(path)
        for refdes, item in components.items():
            require(isinstance(item, (tuple, list)) and len(item) == 6, f"{board}/{refdes}: generator entry must be (symbol, value, lcsc, footprint, dnp, position)")
            symbol, value, lcsc, footprint, dnp, _position = item
            # nickname check runs before the blank-LCSC exclusion so bare-copper
            # entries (test pads, pogo pads) cannot smuggle in an undeclared
            # footprint library
            library, _, package = footprint.partition(":")
            require(package and library == nickname, f"{board}/{refdes}: footprint must be {nickname}:<package>, got {footprint!r}")
            if not lcsc:
                excluded.append((board, refdes))
                continue
            mpn = expected_mpn(symbol, value, lcsc, mpn_from_value)
            entry = grouped.setdefault(lcsc, {"mpn": mpn, "package": package, "symbols": set(), "placements": []})
            require(entry["mpn"] == mpn and entry["package"] == package, f"generator LCSC {lcsc}: conflicting identity")
            entry["symbols"].add(symbol)
            entry["placements"].append({"board": board, "refdes": refdes, "dnp": bool(dnp)})
    return grouped, excluded


def validate_inventory(data, schema, *, staged=True, root=None):
    """Return (lines, generated) where generated is None when no generator spec exists yet."""
    root = root or ROOT
    required_keys(data, ("schema_version", "generator_specs", "assertions", "exclusions", "lines"), "inventory")
    boards = project(schema, "boards")
    pairs = generator_specs(data, schema, root, staged=staged)
    require(pairs is not None or staged, "inventory: strict mode requires the generator specs")
    present_boards = boards if pairs is None else [board for board, _path in pairs]
    assertions = data["assertions"]
    required_keys(assertions, schema["inventory_assertions"], "inventory assertions")
    require(all(isinstance(assertions[key], int) and assertions[key] >= 0 for key in assertions), "inventory assertions: counts must be non-negative integers")
    lines = data["lines"]

    # Structural checks run before every cross-entry check, so a hand-written line with
    # a missing key reports its own contract failure instead of a KeyError traceback.
    for item in data["exclusions"]:
        required_keys(item, ("board", "refdes", "reason"), "inventory exclusion")
        require(item["board"] in boards, f"exclusion {item['refdes']}: unknown board {item['board']}")
        require(isinstance(item["reason"], str) and item["reason"].strip(), f"exclusion {item['refdes']}: blank reason")
    seen_placements = {(item["board"], item["refdes"]) for item in data["exclusions"]}
    for line in lines:
        context = line.get("line_id", "line")
        required_keys(line, schema["line_required"], context)
        require("dnp" not in line, f"{context}: line-level dnp is invalid; every placement carries its own dnp flag")
        require(all(isinstance(line[key], str) and line[key].strip() for key in ("line_id", "mpn", "manufacturer", "lcsc", "package", "owner_skill", "function")), f"{context}: blank identity field")
        require(ID.fullmatch(line["line_id"]), f"{context}: invalid line ID")
        require(LCSC.fullmatch(line["lcsc"]), f"{context}: invalid LCSC identifier")
        require(OWNER_SKILL.fullmatch(line["owner_skill"]) and line["owner_skill"] != "component-spec-audit", f"{context}: invalid owner skill {line['owner_skill']}")
        require(line["source_state"] in ("AVAILABLE", "SOURCE UNAVAILABLE"), f"{context}: source availability state")
        require(line["identity_state"] in ("VERIFIED", "UNRESOLVED"), f"{context}: identity state")
        require(isinstance(line["placements"], list) and line["placements"], f"{context}: at least one placement is required")
        for placement in line["placements"]:
            required_keys(placement, schema["placement_required"], f"{context} placement")
            require(placement["board"] in boards, f"{context}: unknown board {placement['board']}")
            require(isinstance(placement["refdes"], str) and placement["refdes"].strip(), f"{context}: blank refdes")
            require(isinstance(placement["dnp"], bool), f"{context}: placement dnp must be a boolean")
            key = (placement["board"], placement["refdes"])
            require(key not in seen_placements, f"{context}: duplicate placement {key[0]}/{key[1]}")
            seen_placements.add(key)
    require(len(lines) == assertions["orderable_lines"], "inventory: orderable line count differs from reviewed assertion")
    require(len({line["line_id"] for line in lines}) == len(lines), "inventory: duplicate line_id ownership")
    require(len({line["lcsc"] for line in lines}) == len(lines), "inventory: duplicate LCSC ownership")

    if pairs is not None:
        # All generator-derived parity is restricted to the boards whose spec is
        # present; with every spec on disk this is the full board list and the
        # checks below are exhaustive.
        generated, blank = generator_inventory(pairs, schema)
        expected_lcsc = {
            line["lcsc"] for line in lines
            if any(item["board"] in present_boards for item in line["placements"])
        }
        require(set(generated) == expected_lcsc, "inventory: LCSC identity differs from generator specs")
        for line in lines:
            if line["lcsc"] not in generated:
                continue
            expected = generated[line["lcsc"]]
            require(line["mpn"] == expected["mpn"], f"{line['line_id']}: wrong MPN against generator")
            require(line["package"] == expected["package"], f"{line['line_id']}: wrong package against generator")
            want = {(item["board"], item["refdes"], item["dnp"]) for item in expected["placements"]}
            got = {(item["board"], item["refdes"], item["dnp"]) for item in line["placements"] if item["board"] in present_boards}
            require(got == want, f"{line['line_id']}: board/refdes or DNP mismatch")
        exclusions = {(item["board"], item["refdes"]) for item in data["exclusions"] if item["board"] in present_boards}
        require(exclusions == set(blank), "inventory: bare-copper exclusions differ from blank-LCSC generator entries")
    else:
        generated = None

    fitted_lines = sum(any(not item["dnp"] for item in line["placements"]) for line in lines)
    dnp_lines = sum(any(item["dnp"] for item in line["placements"]) for line in lines)
    placements = [item for line in lines for item in line["placements"]]
    require(fitted_lines == assertions["fitted_lines"], "inventory: fitted line count differs from reviewed assertion")
    require(dnp_lines == assertions["dnp_or_hand_fit_lines"], "inventory: DNP/hand-fit line count differs from reviewed assertion")
    require(sum(not item["dnp"] for item in placements) == assertions["fitted_placements"], "inventory: fitted placement count differs from reviewed assertion")
    require(sum(item["dnp"] for item in placements) == assertions["dnp_placements"], "inventory: DNP placement count differs from reviewed assertion")
    return lines, generated


def validate_candidates(data, schema, lines, generated):
    """Unplaced replacement research: evidence-bearing, but never an inventory line."""
    required_keys(data, ("schema_version", "candidates"), "candidates")
    candidates = data["candidates"]
    require(isinstance(candidates, list), "candidates: candidates must be a list")
    line_ids = {line["line_id"] for line in lines}
    placed = {line["lcsc"] for line in lines}
    for candidate in candidates:
        context = candidate.get("candidate_id", "candidate")
        required_keys(candidate, schema["candidate_required"], context)
        require(all(isinstance(candidate[key], str) and candidate[key].strip() for key in ("candidate_id", "mpn", "manufacturer", "lcsc", "package", "function", "owner_skill", "rationale")), f"{context}: blank candidate field")
        require(ID.fullmatch(candidate["candidate_id"]), f"{context}: invalid candidate ID")
        require(LCSC.fullmatch(candidate["lcsc"]), f"{context}: invalid LCSC identifier")
        require(OWNER_SKILL.fullmatch(candidate["owner_skill"]) and candidate["owner_skill"] != "component-spec-audit", f"{context}: invalid owner skill {candidate['owner_skill']}")
        require(candidate["status"] in schema["candidate_states"], f"{context}: candidate status")
        require(candidate["lcsc"] not in placed, f"{context}: candidate LCSC duplicates a placed inventory line")
        require(generated is None or candidate["lcsc"] not in generated, f"{context}: candidate LCSC is placed by a generator spec and belongs in the inventory")
        replaces = candidate["replaces_line_id"]
        require(replaces is None or replaces in line_ids, f"{context}: unknown replaces_line_id {replaces}")
    require(len({item["candidate_id"] for item in candidates}) == len(candidates), "candidates: duplicate candidate_id")
    require(len({item["lcsc"] for item in candidates}) == len(candidates), "candidates: duplicate candidate LCSC")
    return candidates


def contains_alias(query, alias):
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", query, re.I) is not None


def alias_spans(query, alias):
    return [m.span() for m in re.finditer(rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])", query, re.I)]


def alias_subsumed(query, alias, aliases):
    # A shorter exact MPN (JSCJ "BZT52C11") inside a longer one ("BZT52C11-7-F") is not a separate mention;
    # any standalone occurrence still counts, so a query naming both stays ambiguous and fails closed.
    longer = [span for other in aliases if other != alias and alias in other for span in alias_spans(query, other)]
    return bool(longer) and all(any(s >= ls and e <= le for ls, le in longer) for s, e in alias_spans(query, alias))


def looks_like_vendor_hint(token, known_vendor_tokens, boards):
    folded = token.casefold()
    if folded in {board.casefold() for board in boards}:
        return False
    return (
        folded in known_vendor_tokens
        or re.search(r"(?:corp|inc|ltd|semi|semiconductor|electronics?|vendor)$", folded) is not None
        or (any(char.isupper() for char in token[1:]) and any(char.islower() for char in token))
    )


def external_vendor_tokens(path=None):
    path = path or (REFS / "external-vendor-qualifiers.json")
    require(path.is_file(), "routing: external-vendor-qualifiers.json is required")
    data = load(path)
    required_keys(data, ("schema_version", "vendor_names"), "external vendor qualifiers")
    names = data["vendor_names"]
    require(names and all(isinstance(name, str) and name.strip() for name in names), "routing: external vendor names must be nonblank")
    require(len({name.casefold() for name in names}) == len(names), "routing: duplicate external vendor name")
    return {
        token.casefold() for name in names
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", name, re.I)
    }


def resolve_identities(query, entries, *, id_key, boards=("board-a", "board-b")):
    lcsc_tokens = {token.upper() for token in re.findall(r"\bC\d+\b", query, re.I)}
    known_lcsc = {entry["lcsc"] for entry in entries}
    mentioned_lcsc = lcsc_tokens & known_lcsc
    unknown_lcsc = lcsc_tokens - known_lcsc
    mentioned_mpn = {entry["mpn"].casefold() for entry in entries if contains_alias(query, entry["mpn"])}
    mentioned_mpn = {mpn for mpn in mentioned_mpn if not alias_subsumed(query, mpn, mentioned_mpn)}
    mpn_matches = {entry[id_key] for entry in entries if entry["mpn"].casefold() in mentioned_mpn}
    lcsc_matches = {entry[id_key] for entry in entries if entry["lcsc"] in mentioned_lcsc}

    # Exact identifiers are resolved independently. Any conflict or unknown explicit
    # LCSC token fails closed instead of allowing one identifier to override another.
    if unknown_lcsc or len(mentioned_lcsc) > 1 or len(mpn_matches) > 1:
        return []
    if lcsc_matches and mpn_matches and lcsc_matches != mpn_matches:
        return []
    candidates = lcsc_matches or mpn_matches
    if not candidates:
        return []

    known_vendor_tokens = {
        token.casefold() for item in entries
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", item["manufacturer"], re.I)
    }
    known_vendor_tokens.update(external_vendor_tokens())
    function_tokens = {
        token.casefold() for item in entries
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", item["function"], re.I)
    }
    known_vendor_tokens -= function_tokens
    # Only vendor-like qualifiers use the prefix grammar. Ordinary verbs and
    # adjectives before an MPN remain valid natural-language routing prompts.
    for entry in entries:
        if entry[id_key] not in candidates or not contains_alias(query, entry["mpn"]):
            continue
        qualifier = re.search(rf"\b([A-Za-z][A-Za-z0-9+&.-]*)\s+{re.escape(entry['mpn'])}(?![A-Za-z0-9])", query, re.I)
        if qualifier and looks_like_vendor_hint(qualifier.group(1), known_vendor_tokens, boards):
            manufacturer_tokens = {
                token for item in entries if item[id_key] == entry[id_key]
                for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", item["manufacturer"], re.I)
            }
            if qualifier.group(1).casefold() not in {token.casefold() for token in manufacturer_tokens}:
                return []
        suffix = re.search(rf"{re.escape(entry['mpn'])}(?![A-Za-z0-9])\s+(?:from|by)\s+([A-Za-z][A-Za-z0-9+&.-]*)", query, re.I)
        if suffix:
            manufacturer_tokens = {
                token for item in entries if item[id_key] == entry[id_key]
                for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", item["manufacturer"], re.I)
            }
            if suffix.group(1).casefold() not in {token.casefold() for token in manufacturer_tokens}:
                return []

    # An explicit vendor immediately before an exact LCSC identifier is also a
    # binding claim. Reject a mismatched claim instead of silently accepting the
    # LCSC token alone; board names remain ordinary project qualifiers.
    for entry in entries:
        if entry[id_key] not in candidates or entry["lcsc"] not in mentioned_lcsc:
            continue
        qualifier = re.search(rf"\b([A-Za-z][A-Za-z0-9+&.-]*)\s+{re.escape(entry['lcsc'])}(?![A-Za-z0-9])", query, re.I)
        if qualifier and looks_like_vendor_hint(qualifier.group(1), known_vendor_tokens, boards):
            manufacturer_tokens = {
                token.casefold() for item in entries if item[id_key] == entry[id_key]
                for token in re.findall(r"[A-Za-z][A-Za-z0-9+&.-]*", item["manufacturer"], re.I)
            }
            if qualifier.group(1).casefold() not in manufacturer_tokens:
                return []

    # Manufacturer/function text narrows an exact identity; it never unions sibling
    # records or selects a record by a bare ambiguous alias.
    manufacturer_matches = {entry[id_key] for entry in entries if contains_alias(query, entry["manufacturer"])}
    function_matches = {entry[id_key] for entry in entries if contains_alias(query, entry["function"])}
    filtered = {
        entry[id_key] for entry in entries
        if entry[id_key] in candidates
        and (not manufacturer_matches or entry[id_key] in manufacturer_matches)
        and (not function_matches or entry[id_key] in function_matches)
    }
    return sorted(filtered)


def resolve(query, lines):
    return resolve_identities(query, lines, id_key="line_id")


def validate_routing(lines, fixtures=None):
    fixtures = fixtures if fixtures is not None else load(FIXTURES / "direct-routing.json")
    cases = fixtures["cases"]
    require(len(cases) == len(lines) and {x["line_id"] for x in cases} == {x["line_id"] for x in lines}, "routing: every inventory line needs one fixture")
    by_id = {line["line_id"]: line for line in lines}
    for case in cases:
        line = by_id[case["line_id"]]
        queries = (line["mpn"], line["lcsc"], f"{line['manufacturer']} {line['mpn']}", f"{line['function']} {line['mpn']}")
        for query in queries:
            require(resolve(query, lines) == [line["line_id"]], f"routing {line['line_id']}: positive query is not direct and unique: {query}")
        require(resolve(case["negative"], lines) == [], f"routing {line['line_id']}: negative query unexpectedly resolves")


def validate_source(source, schema):
    required_keys(source, schema["source_required"], source.get("source_id", "source"))
    require(ID.fullmatch(source["source_id"]), f"{source['source_id']}: invalid source ID")
    require(source["availability"] in schema["source_availability"], f"{source['source_id']}: invalid availability")
    require(source["authority_class"] in schema["authority_classes"], f"{source['source_id']}: authority class")
    require(HEX64.fullmatch(source["sha256"]), f"{source['source_id']}: SHA-256 must be 64 lowercase hex digits")
    if source["availability"] == "AVAILABLE":
        require(source["sha256"] != ZERO_SHA256, f"{source['source_id']}: AVAILABLE source cannot use all-zero SHA-256 sentinel")
    else:
        require(source["sha256"] == ZERO_SHA256, f"{source['source_id']}: SOURCE UNAVAILABLE must use all-zero SHA-256 sentinel")
    require(isinstance(source["physical_pdf_page_index"], int) and source["physical_pdf_page_index"] >= 0, f"{source['source_id']}: PDF page index")
    for key in ("document_title", "document_number", "revision", "document_date", "authoritative_url", "retrieval_date", "printed_page_label", "locator", "evidence_extract"):
        require(isinstance(source[key], str) and source[key].strip(), f"{source['source_id']}: blank {key}")
    request_headers = source.get("request_headers", {})
    require(isinstance(request_headers, dict) and set(request_headers) <= {"Referer"}, f"{source['source_id']}: only a per-source Referer header is allowed")
    require(all(isinstance(value, str) and value.startswith("https://") for value in request_headers.values()), f"{source['source_id']}: invalid per-source request header")
    refresh_policy = source.get("refresh_policy", "HASH-LOCKED")
    require(refresh_policy in ("HASH-LOCKED", "VOLATILE-HTML"), f"{source['source_id']}: invalid refresh policy")
    if refresh_policy == "VOLATILE-HTML":
        require(isinstance(source.get("refresh_note"), str) and "not deterministic" in source["refresh_note"], f"{source['source_id']}: volatile refresh needs an explicit note")
        require(source["availability"] == "AVAILABLE" and source["authority_class"] == "DISTRIBUTOR_IDENTITY" and HEX64.fullmatch(source.get("identity_extract_sha256", "")), f"{source['source_id']}: volatile refresh is limited to canonical distributor identity web evidence")
    require(LOCATOR_DETAIL.search(source["locator"]), f"{source['source_id']}: locator lacks section/table/figure/row detail")


def graph_cycles(facts):
    graph = {fact["fact_id"]: fact.get("depends_on", []) for fact in facts}
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            raise ContractError(f"facts: derived dependency cycle at {node}")
        if node in done:
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            require(dep in graph, f"{node}: missing dependency {dep}")
            visit(dep)
        visiting.remove(node)
        done.add(node)
    for node in graph:
        visit(node)


def arithmetic(expression, values):
    tree = ast.parse(expression, mode="eval")
    def ev(node):
        if isinstance(node, ast.Expression): return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
        if isinstance(node, ast.Name) and node.id in values: return values[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = ev(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Pow):
                require(abs(left) <= 1e12 and -10 <= right <= 10, "calculated exponent exceeds safety bound")
                return left ** right
            return left / right
        raise ContractError(f"unsafe or unknown expression: {expression}")
    return ev(tree)


def expression_names(expression):
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ContractError(f"invalid calculated expression: {expression}") from exc
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def validate_facts(facts, sources, schema):
    source_ids = {source["source_id"] for source in sources}
    sources_by_id = {source["source_id"]: source for source in sources}
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    require(len({fact["fact_id"] for fact in facts}) == len(facts), "facts: duplicate fact ID")
    for fact in facts:
        required_keys(fact, schema["fact_required"], fact.get("fact_id", "fact"))
        require(ID.fullmatch(fact["fact_id"]), f"{fact['fact_id']}: invalid fact ID")
        require(fact["source_id"] in source_ids, f"{fact['fact_id']}: unknown source ID")
        require(fact["class"] in schema["fact_classes"], f"{fact['fact_id']}: fact class")
        require(fact["provenance"] in schema["provenance"], f"{fact['fact_id']}: provenance")
        require(fact["verdict"] in schema["verdicts"], f"{fact['fact_id']}: verdict")
        if fact["provenance"] == "DISTRIBUTOR-IDENTITY" or fact["verdict"] == "CONFIRMED - distributor identity only":
            source = sources_by_id[fact["source_id"]]
            require(fact["provenance"] == "DISTRIBUTOR-IDENTITY" and fact["verdict"] == "CONFIRMED - distributor identity only", f"{fact['fact_id']}: distributor identity provenance/verdict must be paired")
            require(fact["class"] == "PROJECT_STATE" and source["availability"] == "AVAILABLE" and source["authority_class"] == "DISTRIBUTOR_IDENTITY", f"{fact['fact_id']}: distributor identity lane requires AVAILABLE DISTRIBUTOR_IDENTITY PROJECT_STATE evidence")
        for key in ("unit", "conditions", "locator"):
            require(isinstance(fact[key], str) and fact[key].strip(), f"{fact['fact_id']}: missing {key}")
        require(LOCATOR_DETAIL.search(fact["locator"]), f"{fact['fact_id']}: locator lacks exact detail")
        if fact["provenance"] == "CALCULATED":
            require(fact["depends_on"] and fact["expression"], f"{fact['fact_id']}: calculated fact lacks dependencies/expression")
            require(fact["fact_id"] not in fact["depends_on"], f"{fact['fact_id']}: calculated fact depends on itself")
            expected_names = {dependency.replace("-", "_") for dependency in fact["depends_on"]}
            actual_names = expression_names(fact["expression"])
            require(actual_names == expected_names, f"{fact['fact_id']}: expression variables must exactly match depends_on fact IDs")
        else:
            require(not fact["depends_on"] and not fact["expression"], f"{fact['fact_id']}: raw fact cannot declare derived dependencies/expression")
    graph_cycles(facts)
    values = {fact["fact_id"]: fact["value"] for fact in facts}
    for fact in facts:
        if fact["provenance"] == "CALCULATED":
            require(all(facts_by_id[dependency]["provenance"] != "DISTRIBUTOR-IDENTITY" for dependency in fact["depends_on"]), f"{fact['fact_id']}: calculations cannot depend on distributor identity evidence")
            dependency_values = {key.replace("-", "_"): values[key] for key in fact["depends_on"]}
            require(arithmetic(fact["expression"], dependency_values) == fact["value"], f"{fact['fact_id']}: derived value is stale")


def validate_pin_maps(pin_maps):
    for mapping in pin_maps:
        required_keys(mapping, ("pin_map_id", "record_id", "symbol", "footprint", "pins", "reviewed_by"), "pin map")
        require(mapping["pins"], f"{mapping['pin_map_id']}: empty pin map")
        symbol_pins = [pin["symbol_pin"] for pin in mapping["pins"]]
        pads = [pin["footprint_pad"] for pin in mapping["pins"]]
        require(len(set(symbol_pins)) == len(symbol_pins), f"{mapping['pin_map_id']}: duplicate symbol pin")
        require(len(set(pads)) == len(pads), f"{mapping['pin_map_id']}: duplicate footprint pad")
        for pin in mapping["pins"]:
            required_keys(pin, ("symbol_pin", "name", "footprint_pad", "function"), mapping["pin_map_id"])


def resolve_bundle_route(query, routes):
    # Reject an unknown attached numeric order suffix before bare-MPN or LCSC
    # fallback. Only bundles declaring comma-qualified MPN aliases are affected;
    # a comma followed by ordinary prose still acts as punctuation.
    for route in routes:
        order_codes = {}
        for alias in route["aliases"]["mpn"]:
            if "," in alias:
                base, suffix = alias.split(",", 1)
                if suffix and suffix[0].isdigit():
                    order_codes.setdefault(base.casefold(), set()).add(suffix.casefold())
        for base, allowed in order_codes.items():
            pattern = rf"(?<![A-Za-z0-9]){re.escape(base)}\s*,\s*([0-9][A-Za-z0-9_-]*)"
            if any(match.group(1).casefold() not in allowed for match in re.finditer(pattern, query, re.I)):
                return []
            # Use the declared alias spelling for the ordinary manufacturer
            # checks too; otherwise spacing after the comma bypasses from/by.
            query = re.sub(pattern, lambda match: f"{base},{match.group(1)}", query, flags=re.I)
    entries = []
    for route in routes:
        for mpn in route["aliases"]["mpn"]:
            for lcsc in route["aliases"]["lcsc"]:
                for manufacturer in route["aliases"]["manufacturer"]:
                    for function in route["aliases"]["function"]:
                        entries.append({"record_id": route["record_id"], "mpn": mpn, "lcsc": lcsc, "manufacturer": manufacturer, "function": function})
    return resolve_identities(query, entries, id_key="record_id")


def validate_pass_trust(facts, sources):
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    sources_by_id = {source["source_id"]: source for source in sources}

    def trusted(fact_id, trail):
        require(fact_id not in trail, f"{fact_id}: trust dependency cycle")
        fact = facts_by_id[fact_id]
        if fact["provenance"] == "CALCULATED":
            require(fact["verdict"] == "PASS - primary-source confirmed", f"{fact_id}: calculated PASS dependency is not PASS")
            require(fact["depends_on"], f"{fact_id}: calculated PASS has no dependencies")
            return all(trusted(dependency, trail | {fact_id}) for dependency in fact["depends_on"])
        source = sources_by_id[fact["source_id"]]
        return fact["provenance"] == "PRIMARY-SPEC" and fact["verdict"] == "PASS - primary-source confirmed" and source["availability"] == "AVAILABLE" and source["authority_class"] == "MANUFACTURER_PRIMARY"

    for fact in facts:
        if fact["provenance"] == "PRIMARY-SPEC" and fact["verdict"] == "PASS - primary-source confirmed":
            source = sources_by_id[fact["source_id"]]
            require(source["availability"] == "AVAILABLE" and source["authority_class"] == "MANUFACTURER_PRIMARY", f"{fact['fact_id']}: PRIMARY-SPEC PASS requires AVAILABLE MANUFACTURER_PRIMARY")
        if fact["verdict"] == "PASS - primary-source confirmed":
            require(fact["provenance"] in ("PRIMARY-SPEC", "CALCULATED"), f"{fact['fact_id']}: PASS lacks primary/calculated provenance")
            if fact["provenance"] == "CALCULATED":
                require(trusted(fact["fact_id"], set()), f"{fact['fact_id']}: calculated PASS dependency closure is not fully trusted")
        if fact["verdict"] == "BLOCKER - deterministic spec violation":
            if fact["provenance"] == "CALCULATED":
                require(fact["depends_on"] and all(trusted(dependency, set()) for dependency in fact["depends_on"]), f"{fact['fact_id']}: deterministic BLOCKER dependency closure is not fully trusted")
            else:
                source = sources_by_id[fact["source_id"]]
                require(fact["provenance"] == "PRIMARY-SPEC" and source["availability"] == "AVAILABLE" and source["authority_class"] == "MANUFACTURER_PRIMARY", f"{fact['fact_id']}: deterministic BLOCKER requires available manufacturer-primary evidence")


def fact_blocks_domain(fact_id, facts_by_id, sources_by_id):
    # contract.md: a NOT APPLICABLE fact does not address the domain, so it never blocks.
    fact = facts_by_id[fact_id]
    return fact["verdict"] in ("UNSOURCED", "NEEDS BENCH") or sources_by_id[fact["source_id"]]["availability"] == "SOURCE UNAVAILABLE"


def fact_evidence_available(fact_id, facts_by_id, sources_by_id, trail=None):
    trail = trail or set()
    require(fact_id not in trail, f"{fact_id}: evidence dependency cycle")
    fact = facts_by_id[fact_id]
    source = sources_by_id[fact["source_id"]]
    if source["availability"] != "AVAILABLE" or fact["verdict"] == "UNSOURCED":
        return False
    if fact["provenance"] == "CALCULATED":
        return bool(fact["depends_on"]) and all(
            fact_evidence_available(dependency, facts_by_id, sources_by_id, trail | {fact_id})
            for dependency in fact["depends_on"]
        )
    return True


def fact_primary_trusted(fact_id, facts_by_id, sources_by_id, trail=None):
    trail = trail or set()
    require(fact_id not in trail, f"{fact_id}: trust dependency cycle")
    fact = facts_by_id[fact_id]
    if fact["provenance"] == "CALCULATED":
        return fact["verdict"] == "PASS - primary-source confirmed" and bool(fact["depends_on"]) and all(
            fact_primary_trusted(dependency, facts_by_id, sources_by_id, trail | {fact_id})
            for dependency in fact["depends_on"]
        )
    source = sources_by_id[fact["source_id"]]
    return (
        fact["provenance"] == "PRIMARY-SPEC"
        and fact["verdict"] == "PASS - primary-source confirmed"
        and source["availability"] == "AVAILABLE"
        and source["authority_class"] == "MANUFACTURER_PRIMARY"
    )


def validate_bundle(bundle, schema):
    records, sources, facts = bundle["records"], bundle["sources"], bundle["facts"]
    coverage, routes = bundle["coverage"], bundle["routes"]
    interactions, pin_maps = bundle["interactions"], bundle["pin_maps"]
    for source in sources:
        validate_source(source, schema)
    validate_facts(facts, sources, schema)
    validate_pass_trust(facts, sources)
    validate_pin_maps(pin_maps)
    record_ids = {record["record_id"] for record in records}
    require(len(record_ids) == len(records), "duplicate record ID")
    records_by_id = {record["record_id"]: record for record in records}
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    sources_by_id = {source["source_id"]: source for source in sources}
    id_groups = {
        "source": [item["source_id"] for item in sources], "fact": [item["fact_id"] for item in facts],
        "interaction": [item["interaction_id"] for item in interactions], "coverage": [item["coverage_id"] for item in coverage],
        "route": [item["route_id"] for item in routes], "pin map": [item["pin_map_id"] for item in pin_maps],
    }
    for label, values in id_groups.items():
        require(len(set(values)) == len(values), f"duplicate {label} ID")
    for record in records:
        required_keys(record, schema["record_required"], record.get("record_id", "record"))
        line_id, candidate_id = record["line_id"], record["candidate_id"]
        require(bool(line_id) != bool(candidate_id), f"{record['record_id']}: a record sets exactly one of line_id and candidate_id")
        require(line_id is None or (isinstance(line_id, str) and ID.fullmatch(line_id)), f"{record['record_id']}: invalid line ID")
        require(candidate_id is None or (isinstance(candidate_id, str) and ID.fullmatch(candidate_id)), f"{record['record_id']}: invalid candidate ID")
        require(record["kind"] in ("standalone", "subordinate"), f"{record['record_id']}: record kind")
        if record["kind"] == "subordinate":
            parent = records_by_id.get(record["parent_record_id"])
            require(parent is not None and parent["kind"] == "standalone", f"{record['record_id']}: subordinate parent must resolve to a standalone record in this bundle")
        else:
            require(record["parent_record_id"] is None, f"{record['record_id']}: standalone parent_record_id must be null")
        assigned_sources = {item["source_id"] for item in sources if item.get("record_id") == record["record_id"]}
        assigned_facts = {item["fact_id"] for item in facts if item.get("record_id") == record["record_id"]}
        assigned_interactions = {item["interaction_id"] for item in interactions if record["record_id"] in item.get("record_ids", [])}
        for key in ("source_ids", "fact_ids", "interaction_ids"):
            require(len(record[key]) == len(set(record[key])), f"{record['record_id']}: duplicate {key}")
        require(set(record["source_ids"]) == assigned_sources, f"{record['record_id']}: source ID parity/orphan failure")
        require(set(record["fact_ids"]) == assigned_facts, f"{record['record_id']}: fact ID parity/orphan failure")
        require(set(record["interaction_ids"]) == assigned_interactions, f"{record['record_id']}: interaction ID parity/orphan failure")
        manufacturer_facts = [fact for fact in facts if fact["record_id"] == record["record_id"] and fact["fact_id"].endswith("-manufacturer")]
        require(manufacturer_facts, f"{record['record_id']}: unsourced manufacturer fact")
        for fact in manufacturer_facts:
            require(fact["value"] == record["manufacturer"] and fact["provenance"] in ("PRIMARY-SPEC", "UNVERIFIED"), f"{record['record_id']}: manufacturer evidence invalid")
        record_coverage = [item for item in coverage if item.get("record_id") == record["record_id"]]
        require(record_coverage, f"{record['record_id']}: requires coverage")
        require(any(item.get("record_id") == record["record_id"] for item in routes), f"{record['record_id']}: requires routing fixture")
        require(any(item.get("record_id") == record["record_id"] for item in pin_maps), f"{record['record_id']}: requires pin map")
        domains = record["open_domains"]
        require(isinstance(domains, list) and all(isinstance(domain, str) and domain.strip() for domain in domains), f"{record['record_id']}: open_domains must be nonblank strings")
        require(len(domains) == len(set(domains)), f"{record['record_id']}: duplicate open domain")
        open_coverage = {item["domain"] for item in record_coverage if item.get("status") == "OPEN"}
        require(open_coverage == set(domains), f"{record['record_id']}: open domains and OPEN coverage must match exactly")
    for source in sources:
        require(source.get("record_id") in record_ids, f"{source['source_id']}: orphan source/unknown record ID")
    for fact in facts:
        require(fact["record_id"] in record_ids, f"{fact['fact_id']}: orphan fact/unknown record ID")
        source = next(item for item in sources if item["source_id"] == fact["source_id"])
        require(source["record_id"] == fact["record_id"], f"{fact['fact_id']}: source belongs to a different record")
        if fact["provenance"] == "DISTRIBUTOR-IDENTITY":
            record = records_by_id[fact["record_id"]]
            require(isinstance(fact["value"], dict) and set(fact["value"]) == {"lcsc", "manufacturer", "mpn", "variant"}, f"{fact['fact_id']}: distributor identity value must use exact structured identity keys")
            require(fact["value"]["lcsc"] == record["lcsc"] and fact["value"]["manufacturer"] == record["manufacturer"] and fact["value"]["mpn"] == record["mpn"], f"{fact['fact_id']}: distributor identity differs from owning record")
            require(isinstance(fact["value"]["variant"], str) and fact["value"]["variant"].strip() and fact["unit"] == "NONE" and not fact["depends_on"] and not fact["expression"], f"{fact['fact_id']}: invalid distributor identity variant/units/dependencies")
            extract_hash = source.get("identity_extract_sha256", "")
            actual_extract_hash = hashlib.sha256(json.dumps(fact["value"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            require(HEX64.fullmatch(extract_hash) and extract_hash == actual_extract_hash, f"{fact['fact_id']}: canonical distributor identity extract hash changed")
        if fact["provenance"] == "PRIMARY-SPEC":
            require(source["authority_class"] == "MANUFACTURER_PRIMARY", f"{fact['fact_id']}: primary provenance needs manufacturer primary source")
    for item in coverage:
        required_keys(item, schema["coverage_required"], "coverage")
        require(item["status"] in ("COVERED", "OPEN"), f"{item['coverage_id']}: unexplained coverage gap")
        require(isinstance(item["reason"], str) and item["reason"].strip(), f"{item['coverage_id']}: coverage reason")
        require(item["record_id"] in record_ids, f"{item['coverage_id']}: orphan coverage/unknown record ID")
        require(isinstance(item["fact_ids"], list) and len(item["fact_ids"]) == len(set(item["fact_ids"])), f"{item['coverage_id']}: fact_ids must be a unique list")
        require(set(item["fact_ids"]) <= set(facts_by_id), f"{item['coverage_id']}: unknown coverage fact ID")
        require(all(facts_by_id[fact_id]["record_id"] == item["record_id"] for fact_id in item["fact_ids"]), f"{item['coverage_id']}: coverage fact belongs to another record")
        require(isinstance(item["blocking_fact_ids"], list) and len(item["blocking_fact_ids"]) == len(set(item["blocking_fact_ids"])), f"{item['coverage_id']}: blocking_fact_ids must be a unique list")
        require(set(item["blocking_fact_ids"]) <= set(item["fact_ids"]), f"{item['coverage_id']}: blocking_fact_ids must be a subset of fact_ids")
        if item["status"] == "COVERED":
            require(item["fact_ids"], f"{item['coverage_id']}: COVERED domain requires explicit fact IDs")
            require(all(fact_evidence_available(fact_id, facts_by_id, sources_by_id) for fact_id in item["fact_ids"]), f"{item['coverage_id']}: COVERED domain depends on unavailable or UNSOURCED evidence")
        if item["status"] == "OPEN":
            for fact_id in item["blocking_fact_ids"]:
                require(fact_blocks_domain(fact_id, facts_by_id, sources_by_id), f"{item['coverage_id']}: blocking fact {fact_id} does not carry a blocking verdict")
            unnamed = [fact_id for fact_id in item["fact_ids"] if fact_blocks_domain(fact_id, facts_by_id, sources_by_id)]
            require(item["blocking_fact_ids"] or not unnamed, f"{item['coverage_id']}: OPEN entry cites blocking-verdict facts {sorted(unnamed)} but blocking_fact_ids is empty")
            if OPEN_UNAVAILABLE_CLAIM.search(item["reason"]):
                require(item["blocking_fact_ids"], f"{item['coverage_id']}: OPEN reason claims unavailable/lower-authority/UNSOURCED evidence but blocking_fact_ids is empty")
    for interaction in interactions:
        required_keys(interaction, schema["interaction_required"], "interaction")
        require(interaction["verdict"] in schema["verdicts"] and interaction["verdict"] != "CONFIRMED - distributor identity only", f"{interaction['interaction_id']}: verdict")
        require(interaction["record_ids"] and set(interaction["record_ids"]) <= record_ids, f"{interaction['interaction_id']}: orphan interaction/unknown record ID")
        require(set(interaction["fact_ids"]) <= {fact["fact_id"] for fact in facts}, f"{interaction['interaction_id']}: unknown fact ID")
        fact_record_ids = {fact["record_id"] for fact in facts if fact["fact_id"] in interaction["fact_ids"]}
        require(fact_record_ids <= set(interaction["record_ids"]), f"{interaction['interaction_id']}: fact belongs to an unlisted record")
        if interaction["verdict"] in ("PASS - primary-source confirmed", "BLOCKER - deterministic spec violation"):
            require(interaction["fact_ids"] and all(fact_primary_trusted(fact_id, facts_by_id, sources_by_id) for fact_id in interaction["fact_ids"]), f"{interaction['interaction_id']}: PASS/BLOCKER interaction is not trust-closed")
    for route in routes:
        required_keys(route, ("route_id", "record_id", "aliases", "positive", "negative"), "route")
        require(set(route["aliases"]) == {"mpn", "lcsc", "manufacturer", "function"}, f"{route['route_id']}: routing alias classes")
        require(all(route["aliases"][key] for key in route["aliases"]), f"{route['route_id']}: blank routing aliases")
        require(route["positive"] and route["negative"], f"{route['route_id']}: positive/negative routing fixtures")
        require(route["record_id"] in record_ids, f"{route['route_id']}: orphan route/unknown record ID")
        record = records_by_id[route["record_id"]]
        require(record["mpn"] in route["aliases"]["mpn"] and record["lcsc"] in route["aliases"]["lcsc"] and record["manufacturer"] in route["aliases"]["manufacturer"], f"{route['route_id']}: exact identity aliases missing")
        for query in route["positive"]:
            require(resolve_bundle_route(query, routes) == [route["record_id"]], f"{route['route_id']}: positive query does not resolve uniquely to its record: {query}")
        for mpn in route["aliases"]["mpn"]:
            require(resolve_bundle_route(mpn, routes) == [route["record_id"]], f"{route['route_id']}: declared MPN alias does not route")
            for alias_class in ("manufacturer", "function"):
                for alias in route["aliases"][alias_class]:
                    require(resolve_bundle_route(f"{alias} {mpn}", routes) == [route["record_id"]], f"{route['route_id']}: declared {alias_class} alias does not route: {alias}")
        for lcsc in route["aliases"]["lcsc"]:
            require(resolve_bundle_route(lcsc, routes) == [route["record_id"]], f"{route['route_id']}: declared LCSC alias does not route")
        for query in route["negative"]:
            require(resolve_bundle_route(query, routes) == [], f"{route['route_id']}: negative query unexpectedly resolves: {query}")
    for mapping in pin_maps:
        require(mapping["record_id"] in record_ids, f"{mapping['pin_map_id']}: orphan pin map/unknown record ID")
    require({mapping["record_id"] for mapping in pin_maps} == record_ids, "pin maps: exact record coverage parity required")


def load_skill_bundle(skill_dir):
    return {
        "records": load(skill_dir / "manifest.json")["records"],
        "sources": load(skill_dir / "sources.json")["sources"],
        "facts": load(skill_dir / "facts.json")["facts"],
        "coverage": load(skill_dir / "coverage.json")["coverage"],
        "routes": load(skill_dir / "routing.json")["routes"],
        "interactions": load(skill_dir / "interactions.json")["interactions"],
        "pin_maps": load(skill_dir / "pin-map.json")["pin_maps"],
    }


def canonical_pin_map(mapping):
    payload = {
        "record_id": mapping["record_id"],
        "pin_map_id": mapping["pin_map_id"],
        "symbol": mapping["symbol"],
        "footprint": mapping["footprint"],
        "pins": sorted(
            ({key: pin[key] for key in ("symbol_pin", "name", "footprint_pad", "function")} for pin in mapping["pins"]),
            key=lambda pin: (pin["symbol_pin"], pin["footprint_pad"]),
        ),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sexp_named_block(text, kind, name):
    match = re.search(rf'\({re.escape(kind)}\s+"{re.escape(name)}"', text)
    require(match is not None, f"KiCad {kind} {name}: definition missing")
    depth, quoted, escaped = 0, False, False
    for index in range(match.start(), len(text)):
        char = text[index]
        if quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char == "(": depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0: return text[match.start():index + 1]
    raise ContractError(f"KiCad {kind} {name}: unterminated definition")


def validate_pin_assets(aggregate, inventory, generated, schema, symbols_path=None, footprints_root=None):
    symbols_path = symbols_path or (ROOT / project(schema, "symbol_library"))
    footprints_root = footprints_root or (ROOT / project(schema, "footprint_library_dir"))
    require(symbols_path.is_file(), f"pin assets: KiCad symbol library {symbols_path} is missing")
    require(footprints_root.is_dir(), f"pin assets: KiCad footprint library {footprints_root} is missing")
    symbol_text = symbols_path.read_text(encoding="utf-8")
    records = {record["record_id"]: record for record in aggregate["records"]}
    lines = {line["line_id"]: line for line in inventory}
    for mapping in aggregate["pin_maps"]:
        record = records[mapping["record_id"]]
        if record["line_id"] is None:
            continue  # an unplaced candidate has no generator placement to lock against
        line = lines[record["line_id"]]
        if line["lcsc"] not in generated:
            continue  # staged: the line's only placements are on a board whose spec is absent
        generator_symbols = generated[line["lcsc"]]["symbols"]
        require(len(generator_symbols) == 1, f"{record['record_id']}: conflicting generator symbols")
        symbol = next(iter(generator_symbols))
        require(mapping["symbol"] == symbol, f"{record['record_id']}: pin map symbol differs from generator")
        require(mapping["footprint"] == generated[line["lcsc"]]["package"], f"{record['record_id']}: pin map footprint differs from generator")
        block = sexp_named_block(symbol_text, "symbol", symbol)
        actual_symbol_pins = set(re.findall(r'\(number\s+"([^"\s]+)"', block))
        locked_symbol_pins = {pin["symbol_pin"] for pin in mapping["pins"]}
        require(locked_symbol_pins == actual_symbol_pins, f"{record['record_id']}: pin map differs from KiCad symbol {symbol}")
        footprint_path = footprints_root / f"{mapping['footprint']}.kicad_mod"
        require(footprint_path.is_file(), f"{record['record_id']}: KiCad footprint missing")
        footprint = footprint_path.read_text(encoding="utf-8")
        actual_pads = set(re.findall(r'\(pad\s+"?([^"\s()]+)"?\s+', footprint))
        locked_pads = {pin["footprint_pad"] for pin in mapping["pins"]}
        require(locked_pads == actual_pads, f"{record['record_id']}: pin map differs from KiCad footprint {mapping['footprint']}")
        require(all(pin["symbol_pin"] == pin["footprint_pad"] for pin in mapping["pins"]), f"{record['record_id']}: symbol-pin to footprint-pad mapping differs from KiCad numbering")


def validate_real_pin_locks(aggregate, data, schema):
    locks = data["locks"]
    records = {record["record_id"]: record for record in aggregate["records"]}
    maps = {mapping["pin_map_id"]: mapping for mapping in aggregate["pin_maps"]}
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    sources = {source["source_id"]: source for source in aggregate["sources"]}
    require(len(maps) == len(aggregate["pin_maps"]) and {mapping["record_id"] for mapping in maps.values()} == set(records), "real pin maps: exact record/pin-map parity required")
    require(len(locks) == len(maps) and {lock["pin_map_id"] for lock in locks} == set(maps), "real pin locks: exact pin-map parity required")
    for lock in locks:
        required_keys(lock, ("record_id", "pin_map_id", "canonical_sha256", "evidence_fact_ids", "trust_status", "critical_pins", "reviewer"), "real pin lock")
        mapping = maps[lock["pin_map_id"]]
        require(lock["record_id"] == mapping["record_id"], f"{lock['record_id']}: pin-map record lock changed")
        require(lock["canonical_sha256"] == canonical_pin_map(mapping), f"{lock['record_id']}: canonical pin map changed")
        require(lock["trust_status"] in schema["pin_trust_states"], f"{lock['record_id']}: pin trust status")
        require(lock["evidence_fact_ids"] and set(lock["evidence_fact_ids"]) <= set(facts), f"{lock['record_id']}: pin evidence fact IDs")
        require(all(facts[fact_id]["record_id"] == lock["record_id"] for fact_id in lock["evidence_fact_ids"]), f"{lock['record_id']}: pin evidence belongs to another record")
        require(isinstance(lock["reviewer"], str) and lock["reviewer"].strip(), f"{lock['record_id']}: pin lock reviewer")
        # Trust state is derived from the cited evidence, never asserted on its own.
        if lock["trust_status"] == "TRUSTED":
            require(all(fact_primary_trusted(fact_id, facts, sources) for fact_id in lock["evidence_fact_ids"]), f"{lock['record_id']}: TRUSTED pin lock cites evidence that is not primary-source confirmed")
        if lock["trust_status"] == "UNSOURCED":
            require(any(fact_blocks_domain(fact_id, facts, sources) for fact_id in lock["evidence_fact_ids"]), f"{lock['record_id']}: UNSOURCED pin lock cites only available, non-blocking evidence")
        pins = {(pin["symbol_pin"], pin["name"], pin["footprint_pad"], pin["function"]) for pin in mapping["pins"]}
        locked = {(pin["symbol_pin"], pin["name"], pin["footprint_pad"], pin["function"]) for pin in lock["critical_pins"]}
        require(locked <= pins, f"{lock['record_id']}: critical pin lock changed")


def validate_critical_fact_review(aggregate, data, schema):
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    sources = {source["source_id"]: source for source in aggregate["sources"]}
    reviews = data["reviews"]
    require(reviews, "critical fact review: empty")
    require(len({review["review_id"] for review in reviews}) == len(reviews), "critical fact review: duplicate review ID")
    required_domains = set(schema["critical_review_domains"])
    require(required_domains <= {review["domain"] for review in reviews}, "critical fact review: required destructive-risk domains missing")
    passes = data.get("independent_review_passes", [])
    require(len(passes) >= 2, "critical fact review: two independent review passes required")
    pass_ids = []
    for review_pass in passes:
        required_keys(review_pass, ("reviewer", "review_log", "review_log_sha256", "review_ids"), "critical fact independent pass")
        require(review_pass["reviewer"].strip() and review_pass["review_log"].strip() and review_pass["review_ids"], "critical fact review: incomplete independent pass")
        require(HEX64.fullmatch(review_pass["review_log_sha256"]) and review_pass["review_log_sha256"] != ZERO_SHA256, "critical fact review: independent pass needs a concrete review-log hash")
        review_log_path = AUDIT / review_pass["review_log"]
        require(review_log_path.is_file() and review_log_path.resolve().is_relative_to(AUDIT.resolve()), "critical fact review: committed review-log file is missing or outside audit skill")
        require(hashlib.sha256(review_log_path.read_bytes()).hexdigest() == review_pass["review_log_sha256"], "critical fact review: review-log hash changed")
        pass_ids.extend(review_pass["review_ids"])
    require(len({review_pass["reviewer"] for review_pass in passes}) == len(passes), "critical fact review: independent pass reviewers must be distinct")
    require(len(pass_ids) == len(set(pass_ids)) and set(pass_ids) == {review["review_id"] for review in reviews}, "critical fact review: every fact needs exactly one independent family pass in addition to integration review")
    locks = {lock["review_id"]: lock["sha256"] for lock in data.get("fact_locks", [])}
    require(len(locks) == len(reviews) and set(locks) == {review["review_id"] for review in reviews}, "critical fact review: exact value/unit/evidence lock parity required")
    for review in reviews:
        required_keys(review, ("review_id", "domain", "fact_id", "source_id", "physical_pdf_page_index", "printed_page_label", "locator", "evidence_extract", "conditions", "reviewer", "status"), "critical fact review")
        pass_reviewer = next(review_pass["reviewer"] for review_pass in passes if review["review_id"] in review_pass["review_ids"])
        require(review["reviewer"] != pass_reviewer, f"{review['review_id']}: foreground and independent reviewers must differ")
        require(review["fact_id"] in facts and review["source_id"] in sources, f"{review['review_id']}: unknown fact/source")
        fact, source = facts[review["fact_id"]], sources[review["source_id"]]
        require(fact["source_id"] == review["source_id"], f"{review['review_id']}: fact/source mismatch")
        require(review["physical_pdf_page_index"] == source["physical_pdf_page_index"], f"{review['review_id']}: physical page index changed")
        require(review["printed_page_label"] == source["printed_page_label"], f"{review['review_id']}: printed page label changed")
        require(review["locator"] == fact["locator"] and review["conditions"] == fact["conditions"], f"{review['review_id']}: locator/conditions changed")
        require(isinstance(review["evidence_extract"], str) and review["evidence_extract"].strip(), f"{review['review_id']}: minimal extract required")
        lock_payload = {
            "value": fact["value"], "unit": fact["unit"], "locator": fact["locator"], "conditions": fact["conditions"],
            "source_evidence_extract": source["evidence_extract"], "review_evidence_extract": review["evidence_extract"],
        }
        actual_lock = hashlib.sha256(json.dumps(lock_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(locks[review["review_id"]] == actual_lock, f"{review['review_id']}: value/unit/evidence lock changed")
        require(review["status"] in ("CONFIRMED", "OPEN", "UNSOURCED"), f"{review['review_id']}: review status")
        if source["availability"] == "SOURCE UNAVAILABLE" or fact["verdict"] == "UNSOURCED":
            require(review["status"] in ("OPEN", "UNSOURCED"), f"{review['review_id']}: unavailable/UNSOURCED fact cannot be confirmed")


def validate_refresh_evidence(aggregate, data):
    sources = {source["source_id"]: source for source in aggregate["sources"]}
    evidence = data["evidence"]
    require(evidence, "refresh evidence: empty")
    classes = set()
    for item in evidence:
        required_keys(item, ("source_id", "authoritative_url", "sha256", "checked_at", "result", "retrieval_profile"), "refresh evidence")
        require(item["source_id"] in sources, f"refresh evidence: unknown source {item['source_id']}")
        source = sources[item["source_id"]]
        require(source["availability"] == "AVAILABLE", f"{item['source_id']}: refresh evidence source unavailable")
        require((item["authoritative_url"], item["sha256"]) == (source["authoritative_url"], source["sha256"]), f"{item['source_id']}: stale refresh evidence")
        require(item["result"] == "MATCH" and item["retrieval_profile"] == "browser-like-v1", f"{item['source_id']}: invalid refresh result/profile")
        classes.add(source["authority_class"])
    require("PROJECT_GENERATOR" in classes and "MANUFACTURER_PRIMARY" in classes, "refresh evidence requires generator and manufacturer-primary examples")


def validate_evidence_chain(chain, aggregate, schema):
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    expected_stages = schema["integration_evidence_chain_stages"]
    require([stage["stage"] for stage in chain["evidence_chain"]] == expected_stages, "integration evidence chain: stage order changed")
    for stage in chain["evidence_chain"]:
        required_keys(stage, ("stage", "status", "fact_ids"), "integration evidence stage")
        require(stage["status"] in ("CONFIRMED", "MIXED", "OPEN"), f"integration evidence chain: invalid status {stage['status']}")
        require(set(stage["fact_ids"]) <= set(chain["fact_ids"]), "integration evidence chain: unknown stage fact")
        if stage["status"] == "CONFIRMED":
            require(stage["fact_ids"] and all(fact_evidence_available(fact_id, facts, {source["source_id"]: source for source in aggregate["sources"]}) for fact_id in stage["fact_ids"]), "integration evidence chain: CONFIRMED stage lacks available evidence")
        if stage["stage"] == "generated-netlist":
            require(stage["status"] == "MIXED", "integration evidence chain: generator prose cannot CONFIRM an exported netlist")
        if stage["status"] == "OPEN":
            require(not stage["fact_ids"], "integration evidence chain: OPEN stage must not claim proof")
    require(all(stage["status"] == "OPEN" for stage in chain["evidence_chain"][-5:]), "integration evidence chain: downstream proof must remain OPEN")


def validate_integration_artifacts(aggregate, schema, *, staged=True):
    frontmatter(INTEGRATION / "SKILL.md", "circuit-spec-integration")
    for relative in ("agents/openai.yaml", "references/rules.json", "references/forward-tests.json", "references/observed-runs.json", "scripts/check_forward_tests.py"):
        require((INTEGRATION / relative).is_file(), f"circuit-spec-integration: missing {relative}")
    facts = {fact["fact_id"]: fact for fact in aggregate["facts"]}
    fact_owners = {fact["fact_id"]: fact["record_id"] for fact in aggregate["facts"]}
    records = {record["record_id"] for record in aggregate["records"]}
    rules = load(INTEGRATION / "references/rules.json")["rules"]
    required_domains = set(schema["integration_domains"])
    require(rules or staged, "integration rules: strict mode requires committed cross-component rules")
    require(len({rule["rule_id"] for rule in rules}) == len(rules), "integration rules: duplicate rule ID")
    require({rule["domain"] for rule in rules} == required_domains, "integration rules: exact required domains")
    for rule in rules:
        required_keys(rule, ("rule_id", "domain", "record_ids", "fact_ids", "conditions", "verdict", "refusal"), "integration rule")
        require(set(rule["record_ids"]) <= records and set(rule["fact_ids"]) <= set(facts), f"{rule['rule_id']}: unknown record/fact ID")
        require({fact_owners[fact_id] for fact_id in rule["fact_ids"]} <= set(rule["record_ids"]), f"{rule['rule_id']}: fact owner missing from record_ids")
        require(rule["record_ids"] and rule["fact_ids"] and rule["conditions"].strip() and rule["refusal"].strip(), f"{rule['rule_id']}: incomplete conditioned refusal")
        require(rule["verdict"] in ("NEEDS BENCH", "UNSOURCED"), f"{rule['rule_id']}: unsafe integration verdict")
        calculations = rule.get("conditioned_calculations", [])
        require(len({item["calculation_id"] for item in calculations}) == len(calculations), f"{rule['rule_id']}: duplicate conditioned calculation")
        for item in calculations:
            required_keys(item, ("calculation_id", "fact_ids", "expression", "result_key", "conditions"), "conditioned calculation")
            require(set(item["fact_ids"]) <= set(rule["fact_ids"]) and item["expression"].strip() and item["conditions"].strip(), f"{item['calculation_id']}: incomplete calculation evidence")
            require(item["result_key"] in item or item.get("results"), f"{item['calculation_id']}: calculation result missing")
            fact_values = {fact_id.replace("-", "_"): facts[fact_id]["value"] for fact_id in item["fact_ids"] if isinstance(facts[fact_id]["value"], (int, float))}
            names = expression_names(item["expression"])
            require(set(fact_values) <= names, f"{item['calculation_id']}: declared numeric fact is unused")
            require({name for name in names if name.startswith("fact_")} <= {fact_id.replace("-", "_") for fact_id in item["fact_ids"]}, f"{item['calculation_id']}: expression uses an undeclared fact")
            if item.get("results"):
                for scenario in item["results"]:
                    require(item["result_key"] in scenario, f"{item['calculation_id']}: scenario output missing")
                    inputs = {key: value for key, value in scenario.items() if key != item["result_key"] and isinstance(value, (int, float))}
                    require(names - set(fact_values) == set(inputs), f"{item['calculation_id']}: scenario variables must be explicit and exact")
                    require(math.isclose(arithmetic(item["expression"], {**fact_values, **inputs}), scenario[item["result_key"]], rel_tol=1e-12, abs_tol=1e-12), f"{item['calculation_id']}: scenario result is stale")
            else:
                require(math.isclose(arithmetic(item["expression"], fact_values), item[item["result_key"]], rel_tol=1e-12, abs_tol=1e-12), f"{item['calculation_id']}: result is stale")
    chain = next((rule for rule in rules if rule["domain"] == "source-to-bench-chain"), None)
    if chain is not None:
        validate_evidence_chain(chain, aggregate, schema)


def component_skill_dirs(skills_root):
    return {
        path.name for path in skills_root.glob("component-*")
        if path.is_dir() and path.name != "component-spec-audit"
    }


def owner_skills(inventory, candidates):
    return {line["owner_skill"] for line in inventory} | {item["owner_skill"] for item in candidates}


def validate_local_skills(schema, inventory, candidates=(), *, staged=True, skills_root=None):
    required = schema["required_skill_files"]
    candidates = list(candidates)
    owners = owner_skills(inventory, candidates)
    skills_root = skills_root or (ROOT / ".claude/skills")
    actual_component_dirs = component_skill_dirs(skills_root)
    unassigned = actual_component_dirs - owners
    require(not unassigned, f"owner skills: component directories {sorted(unassigned)} are not assigned any inventory line or candidate")
    if not staged:
        require(actual_component_dirs == owners, f"owner skills: expected exact directories {sorted(owners)}, got {sorted(actual_component_dirs)}")
    global_ids = {label: set() for label in ("record", "source", "fact", "interaction")}
    aggregate = {key: [] for key in ("records", "sources", "facts", "coverage", "routes", "interactions", "pin_maps")}
    for owner in sorted(owners & actual_component_dirs):
        skill_dir = skills_root / owner
        missing = [name for name in required if not (skill_dir / name).is_file()]
        require(not missing, f"{skill_dir.name}: missing local manifest files {missing}")
        frontmatter(skill_dir / "SKILL.md", skill_dir.name)
        bundle = load_skill_bundle(skill_dir)
        validate_bundle(bundle, schema)
        expected_lines = {line["line_id"]: line for line in inventory if line["owner_skill"] == skill_dir.name}
        expected_candidates = {item["candidate_id"]: item for item in candidates if item["owner_skill"] == skill_dir.name}
        actual_lines = {record["line_id"]: record for record in bundle["records"] if record["line_id"]}
        actual_candidates = {record["candidate_id"]: record for record in bundle["records"] if record["candidate_id"]}
        require(len(actual_lines) + len(actual_candidates) == len(bundle["records"]), f"{skill_dir.name}: duplicate line/candidate ownership inside the bundle")
        require(set(actual_lines) <= set(expected_lines), f"{skill_dir.name}: local manifest claims inventory lines {sorted(set(actual_lines) - set(expected_lines))} it does not own")
        require(set(actual_candidates) <= set(expected_candidates), f"{skill_dir.name}: local manifest claims candidates {sorted(set(actual_candidates) - set(expected_candidates))} it does not own")
        if not staged:
            require(set(actual_lines) == set(expected_lines), f"{skill_dir.name}: local manifest does not own exactly its assigned inventory lines")
            require(set(actual_candidates) == set(expected_candidates), f"{skill_dir.name}: local manifest does not own exactly its assigned candidates")
        for entry_id, record in {**actual_lines, **actual_candidates}.items():
            entry = expected_lines.get(entry_id) or expected_candidates[entry_id]
            for key in ("mpn", "manufacturer", "lcsc", "package"):
                require(record[key] == entry[key], f"{skill_dir.name}/{entry_id}: {key} differs from the central identity")
        current = {
            "record": {item["record_id"] for item in bundle["records"]},
            "source": {item["source_id"] for item in bundle["sources"]},
            "fact": {item["fact_id"] for item in bundle["facts"]},
            "interaction": {item["interaction_id"] for item in bundle["interactions"]},
        }
        for label, values in current.items():
            require(not (values & global_ids[label]), f"{skill_dir.name}: duplicate global {label} IDs")
            global_ids[label].update(values)
        for key in aggregate:
            aggregate[key].extend(bundle[key])
    actual_line_ids = [record["line_id"] for record in aggregate["records"] if record["line_id"]]
    actual_candidate_ids = [record["candidate_id"] for record in aggregate["records"] if record["candidate_id"]]
    require(len(actual_line_ids) == len(set(actual_line_ids)) and len(actual_candidate_ids) == len(set(actual_candidate_ids)), "owner skills: an inventory line or candidate is claimed by two bundles")
    if not staged:
        require(set(actual_line_ids) == {line["line_id"] for line in inventory}, "owner skills: exact global inventory-record parity required")
        require(set(actual_candidate_ids) == {item["candidate_id"] for item in candidates}, "owner skills: exact global candidate-record parity required")
    return aggregate


def validate_golden(data, schema, enforce_lock=True):
    for source in data["sources"]: validate_source(source, schema)
    validate_facts(data["facts"], data["sources"], schema)
    validate_pin_maps([data["pin_map"]])
    if enforce_lock:
        facts = {fact["fact_id"]: fact for fact in data["facts"]}
        expected = {
            "fact-golden-pin": ("1", "pin", "symbol-to-footprint mapping", "src-golden: Section 2, Figure 1, pin 1"),
            "fact-golden-limit": (20, "V", "DC, TA=25 degC", "src-golden: Section 2, Table 3, row VIN_MAX"),
            "fact-golden-project": (15, "V", "nominal contracted input", "src-golden: Section 2, Table 3, row VIN_PROJECT"),
            "fact-golden-default": ("LOW", "NONE", "after power-on reset before configuration", "src-golden: Section 2, Table 3, row RESET_DEFAULT"),
        }
        for fact_id, values in expected.items():
            fact = facts[fact_id]
            require((fact["value"], fact["unit"], fact["conditions"], fact["locator"]) == values, f"golden fact changed: {fact_id}")
        require(data["pin_map"]["pins"][0]["footprint_pad"] == "1", "golden pin map changed")


def set_target(data, target, value):
    parts = target.split(".")
    current = data
    for part in parts[:-1]:
        if isinstance(current, list):
            if part.isdigit():
                current = current[int(part)]
            else:
                current = next(item for item in current if any(item.get(key) == part for key in ("line_id", "candidate_id", "record_id", "fact_id", "source_id", "coverage_id")))
        else:
            current = current[part]
    current[parts[-1]] = value


def template_bundle():
    return load_skill_bundle(TEMPLATE)


def validate_template_skill():
    template_skill = TEMPLATE / "SKILL.md"
    frontmatter(template_skill, "component-example")
    text = template_skill.read_text(encoding="utf-8")
    closing = text.find("---\n", 4)
    require(closing >= 0 and text.find("## Human component reference", closing + 4) >= 0, "component template: missing Human component reference section")


def synthetic_inventory(schema):
    """The fixture world: a two-board inventory plus candidates that always exists."""
    data = load(SYNTHETIC / "inventory.json")
    lines, generated = validate_inventory(data, schema, staged=False, root=SYNTHETIC)
    candidates = validate_candidates(load(SYNTHETIC / "candidates.json"), schema, lines, generated)
    return data, lines, candidates


def run_seeded_fixtures(schema):
    golden = load(FIXTURES / "golden/critical-facts.json")
    validate_golden(golden, schema)
    mutations = sorted((FIXTURES / "mutations").glob("*.json"))
    require(len(mutations) >= 6, "mutations: expected pin/value/unit/condition/default/locator fixtures")
    for path in mutations:
        mutation = load(path)
        changed = copy.deepcopy(golden)
        set_target(changed, mutation["target"], mutation["to"])
        try:
            validate_golden(changed, schema)
        except ContractError as exc:
            require(mutation["expected_error"] in str(exc), f"{path.name}: failed for unintended reason: {exc}")
        else:
            raise ContractError(f"{path.name}: seeded mutation passed")

    inventory_data, lines, _candidates = synthetic_inventory(schema)
    candidates_data = load(SYNTHETIC / "candidates.json")
    validate_routing(lines, load(SYNTHETIC / "direct-routing.json"))
    inventory_mutations = sorted((FIXTURES / "mutations-inventory").glob("*.json"))
    require(len(inventory_mutations) >= 8, "inventory mutations: expected placement-DNP and candidate fixtures")
    seen = {mutation["mutation"] for mutation in map(load, inventory_mutations)}
    require({"placement dnp fitted-to-dnp", "placement dnp dnp-to-fitted", "line-level dnp"} <= seen, "inventory mutations: placement-level DNP cases are required")
    require({"candidate collides with placed line", "candidate replaces unknown line"} <= seen, "inventory mutations: candidate cases are required")
    for path in inventory_mutations:
        mutation = load(path)
        try:
            apply_inventory_case(schema, inventory_data, candidates_data, mutation["base"], mutation["target"], mutation["to"])
        except (ContractError, StopIteration) as exc:
            require(mutation["expected_error"] in str(exc), f"{path.name}: failed for unintended reason: {exc}")
        else:
            raise ContractError(f"{path.name}: seeded mutation passed")

    subordinate = load(FIXTURES / "valid/subordinate-record.json")
    validate_bundle(subordinate, schema)
    for case in load(FIXTURES / "invalid/contract-cases.json")["cases"]:
        try:
            if case["base"] in ("inventory", "candidates"):
                apply_inventory_case(schema, inventory_data, candidates_data, case["base"], case["target"], case["value"])
            elif case["base"] == "golden":
                changed = copy.deepcopy(golden); set_target(changed, case["target"], case["value"]); validate_golden(changed, schema, False)
            else:
                bundle = template_bundle(); set_target(bundle, case["target"], case["value"]); validate_bundle(bundle, schema)
        except (ContractError, StopIteration) as exc:
            require(case["expected_error"].casefold() in str(exc).casefold(), f"{case['name']}: failed for unintended reason: {exc}")
        else:
            raise ContractError(f"{case['name']}: invalid fixture passed")


def apply_inventory_case(schema, inventory_data, candidates_data, base, target, value):
    """Mutate one synthetic inventory/candidates fixture and revalidate the pair."""
    inventory_changed = copy.deepcopy(inventory_data)
    candidates_changed = copy.deepcopy(candidates_data)
    set_target(inventory_changed if base == "inventory" else candidates_changed, target, value)
    lines, generated = validate_inventory(inventory_changed, schema, staged=False, root=SYNTHETIC)
    validate_candidates(candidates_changed, schema, lines, generated)


def verify_payload(payload, expected_sha256, source_id):
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, f"{source_id}: stale online hash")


def fetch_source(source, opener=urllib.request.urlopen):
    request = urllib.request.Request(source["authoritative_url"], headers={**HTTP_HEADERS, **source.get("request_headers", {})})
    with opener(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return response.read()


def online_sources(schema, sources, selected_ids=None, opener=urllib.request.urlopen):
    sources_by_id = {source["source_id"]: source for source in sources}
    selected = set(selected_ids or ())
    if selected:
        require(selected <= set(sources_by_id), f"online refresh: unknown source IDs {sorted(selected - set(sources_by_id))}")
        chosen = [sources_by_id[source_id] for source_id in sorted(selected)]
    else:
        chosen = [source for source in sources if source["availability"] == "AVAILABLE"]
    for source in chosen:
        validate_source(source, schema)
        require(source["availability"] == "AVAILABLE", f"{source['source_id']}: only AVAILABLE sources can be refreshed")
        require(source.get("refresh_policy", "HASH-LOCKED") == "HASH-LOCKED", f"{source['source_id']}: volatile source cannot claim deterministic selective refresh")
        payload = fetch_source(source, opener)
        verify_payload(payload, source["sha256"], source["source_id"])


def load_contract(*, staged, skipped=None, root=None):
    """Shared staged-bootstrap for every consumer of the contract: load the
    schema, validate the inventory and candidates with the staged/strict
    tolerances, and return (schema, lines, candidates, generated).

    validate_all and circuit-spec-integration's check_forward_tests.py both
    call this — one body, so the two gates cannot drift apart."""
    skipped = skipped if skipped is not None else []
    root = root or ROOT
    schema = load(REFS / "schema.json")

    inventory_path = REFS / "inventory.json"
    if inventory_path.is_file():
        inventory_data = load(inventory_path)
        lines, generated = validate_inventory(inventory_data, schema, staged=staged, root=root)
        if generated is None:
            skipped.append("generator specs are absent: inventory-to-generator identity, placement/DNP, exclusion, and KiCad pin-asset parity were not checked")
        else:
            absent_boards = [item["board"] for item in inventory_data["generator_specs"] if not (root / item["spec"]).is_file()]
            if absent_boards:
                skipped.append(f"generator specs for {absent_boards} are absent: their placements, exclusions, and KiCad pin-asset parity were not checked")
    else:
        require(staged, f"{inventory_path}: inventory is required in strict mode")
        skipped.append("references/inventory.json is absent: the whole central identity lock was not checked")
        lines, generated = [], None

    candidates_path = REFS / "candidates.json"
    if candidates_path.is_file():
        candidates = validate_candidates(load(candidates_path), schema, lines, generated)
    else:
        require(staged, f"{candidates_path}: candidates file is required in strict mode")
        skipped.append("references/candidates.json is absent: replacement-candidate identity was not checked")
        candidates = []

    return schema, lines, candidates, generated


def validate_all(*, staged=True, online=False, refresh_source_ids=None, skipped=None):
    skipped = skipped if skipped is not None else []
    schema, lines, candidates, generated = load_contract(staged=staged, skipped=skipped)
    frontmatter(AUDIT / "SKILL.md", "component-spec-audit")
    validate_template_skill()
    validate_bundle(template_bundle(), schema)
    run_seeded_fixtures(schema)

    validate_routing(lines)
    owners = owner_skills(lines, candidates)
    present_owners = owners & component_skill_dirs(ROOT / ".claude/skills")
    if owners - present_owners:
        skipped.append(f"owner skills {sorted(owners - present_owners)} have no bundle yet: their evidence, pin, and coverage contracts were not checked")
    aggregate = validate_local_skills(schema, lines, candidates, staged=staged)

    locks = load(FIXTURES / "golden/real-pin-maps.json")
    if locks["locks"] or not staged:
        require(locks["locks"] or not aggregate["pin_maps"], "real pin locks: strict mode requires a committed lock per pin map")
        validate_real_pin_locks(aggregate, locks, schema)
    else:
        skipped.append("fixtures/golden/real-pin-maps.json is empty: reviewed pin-map locks were not checked")

    if generated is not None and aggregate["pin_maps"]:
        validate_pin_assets(aggregate, lines, generated, schema)
    elif not staged:
        require(generated is not None, "pin assets: strict mode requires the generator specs")

    review = load(FIXTURES / "golden/critical-fact-review.json")
    if review["reviews"] or not staged:
        validate_critical_fact_review(aggregate, review, schema)
    else:
        skipped.append("fixtures/golden/critical-fact-review.json is empty: destructive-risk fact review was not checked")

    refresh = load(FIXTURES / "refresh-evidence.json")
    if refresh["evidence"] or not staged:
        validate_refresh_evidence(aggregate, refresh)
    else:
        skipped.append("fixtures/refresh-evidence.json is empty: dated source-hash refresh evidence was not checked")

    validate_integration_artifacts(aggregate, schema, staged=staged)
    if not load(INTEGRATION / "references/rules.json")["rules"]:
        skipped.append("circuit-spec-integration/references/rules.json is empty: no cross-component rule was checked")

    if online or refresh_source_ids:
        online_sources(schema, aggregate["sources"], refresh_source_ids)
    return {"lines": len(lines), "candidates": len(candidates), "bundles": len(present_owners), "skipped": skipped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true", help="tolerate absent generator specs and owner skills that do not exist yet (default)")
    parser.add_argument("--strict", action="store_true", help="require full generator, owner, pin-asset, review, and integration parity")
    parser.add_argument("--online", action="store_true", help="opt in to authoritative URL/hash checks")
    parser.add_argument("--refresh-source", action="append", default=[], metavar="SOURCE_ID", help="opt in to refreshing one exact AVAILABLE source ID; repeatable")
    args = parser.parse_args()
    try:
        require(not (args.staged and args.strict), "choose --staged or --strict, not both")
        require(not (args.online and args.refresh_source), "choose --online or --refresh-source, not both")
        summary = validate_all(staged=not args.strict, online=args.online, refresh_source_ids=args.refresh_source)
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for note in summary["skipped"]:
        print(f"STAGED-SKIP: {note}")
    offline = not args.online and not args.refresh_source
    refreshed = ",".join(args.refresh_source) if args.refresh_source else ("all" if args.online else "none")
    mode = "strict" if args.strict else "staged"
    print(
        f"PASS: component-spec contract; mode={mode}; {summary['lines']} lines; "
        f"{summary['candidates']} candidates; {summary['bundles']} bundles; offline={offline}; refreshed={refreshed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
