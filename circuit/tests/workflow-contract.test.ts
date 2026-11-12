import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, describe, it } from "node:test";

import { REPO_ROOT } from "./project-context.mjs";

const WORKFLOWS = ["main-deploy.yml", "pr-checks.yml", "component-spec-skills.yml"] as const;
const REQUIRED_PATHS = [
  "readme.md",
  "CLAUDE.md",
  "AGENTS.md",
  "package.json",
  "pnpm-workspace.yaml",
  "pnpm-lock.yaml",
  "patches/**",
  "circuit.config.ts",
  "circuit/**",
  "doc/**",
  ".claude/skills/**",
  ".github/workflows/**",
  "lefthook.yml",
  "scripts/mdx-format.sh",
  "scripts/schgen/**",
  "boards/**",
  "symbols/**",
  "footprints/**",
] as const;
const REQUIRED_PYTHON = "3.12";
// Inputs the component gate (circuit/scripts/run-python-gates.sh) consumes beyond REQUIRED_PATHS.
// Traced with a Python open() audit hook over every gate; each family lists representative files.
// These belong only to component-spec-skills.yml, not to every documentation workflow.
const COMPONENT_GATE_INPUTS: ReadonlyArray<{ readonly pattern: string; readonly samples: readonly string[] }> = [
  {
    pattern: "scripts/pcb/**",
    samples: [
      "scripts/pcb/board-p/nvm-intent-20v.py",
      "scripts/pcb/board-p/q1-closure.py",
      "scripts/pcb/board-p/q1-closure-inputs.json",
      "scripts/pcb/board-b20/report_provenance.py",
      "scripts/pcb/board-b20/test_load_cases.py",
      "scripts/pcb/board-p-r3-draft/build-draft.py",
      "scripts/pcb/export-jlcpcb.py",
      "scripts/pcb/calculate-board-b20-draft.py",
      "scripts/pcb/pcb_common.py",
      "scripts/pcb/board-p15/nvm-image.py",
    ],
  },
  { pattern: "manufacturing/README.md", samples: ["manufacturing/README.md"] },
  { pattern: "manufacturing/package-notes-p15.md", samples: ["manufacturing/package-notes-p15.md"] },
  { pattern: "manufacturing/pd20-status.md", samples: ["manufacturing/pd20-status.md"] },
  { pattern: "manufacturing/power-budget.json", samples: ["manufacturing/power-budget.json"] },
  { pattern: "manufacturing/power-budget.md", samples: ["manufacturing/power-budget.md"] },
  { pattern: "manufacturing/power-budget-p15.json", samples: ["manufacturing/power-budget-p15.json"] },
  { pattern: "manufacturing/power-budget-b20.json", samples: ["manufacturing/power-budget-b20.json"] },
  { pattern: "manufacturing/supply-capability.json", samples: ["manufacturing/supply-capability.json"] },
  { pattern: "manufacturing/power-layout.json", samples: ["manufacturing/power-layout.json"] },
  { pattern: "manufacturing/power-layout-b20.json", samples: ["manufacturing/power-layout-b20.json"] },
  {
    pattern: "manufacturing/releases/corner-support-review/**",
    samples: ["manufacturing/releases/corner-support-review/manifest.json", "manufacturing/releases/corner-support-review/board-p15/bom.csv"],
  },
  {
    pattern: "manufacturing/sim/board-b20-phase33/**",
    samples: ["manufacturing/sim/board-b20-phase33/analyze_refinement.py", "manufacturing/sim/board-b20-phase33/test_run_ladder.py"],
  },
  { pattern: "manufacturing/sim/board-b20-phase7/ac/**", samples: ["manufacturing/sim/board-b20-phase7/ac/m12_full_19_47n.cir"] },
];
// Changed-file sets that must schedule the component gate on both pull_request and main push.
const COMPONENT_GATE_FIXTURES: ReadonlyArray<readonly [string, readonly string[]]> = [
  ["analyzer-only", ["manufacturing/sim/board-b20-phase33/analyze_refinement.py"]],
  ["NVM-only", ["scripts/pcb/board-p/nvm-intent-20v.py"]],
  ["Q1 closure inputs-only", ["scripts/pcb/board-p/q1-closure-inputs.json"]],
  ["shared-helper-only", ["scripts/pcb/board-b20/report_provenance.py"]],
  ["exporter-only", ["scripts/pcb/export-jlcpcb.py"]],
  ["P r3 source-binding-only", ["scripts/pcb/board-p-r3-draft/build-draft.py"]],
  ["retained-report-only", ["manufacturing/power-budget-b20.json"]],
  ["supply-capability-report-only", ["manufacturing/supply-capability.json"]],
  ["status-report-only", ["manufacturing/pd20-status.md"]],
  ["C12 template-only", ["manufacturing/sim/board-b20-phase7/ac/m12_full_19_47n.cir"]],
];
// Not consumed by any gate; selecting them would mean an indiscriminate manufacturing/** filter.
const COMPONENT_GATE_UNRELATED = ["manufacturing/sim/board-b20-phase9/README.md", "manufacturing/heat-spreader-concept.md"] as const;
const DRIFT_PATHS = [
  "doc/src/content/docs/components",
  "circuit/generated/preflight.json",
  "doc/public/assets/component-previews",
] as const;
const BUILTIN_PNPM_COMMANDS = new Set(["install", "exec", "dlx", "add", "remove"]);
const SCRIPT = join(REPO_ROOT, "circuit", "scripts", "check-generated-diff.sh");

let scratch = "";

before(async () => {
  scratch = await mkdtemp(join(tmpdir(), "zudo-pd-workflow-contract-"));
});

after(async () => {
  await rm(scratch, { recursive: true, force: true });
});

describe("root workspace workflow contract", () => {
  it("every workflow installs the root lockfile and runs only defined root scripts", async () => {
    const packageJson = JSON.parse(await readFile(join(REPO_ROOT, "package.json"), "utf8")) as {
      packageManager?: string;
      scripts?: Record<string, string>;
    };
    const scripts = packageJson.scripts ?? {};
    assert.equal(packageJson.packageManager, "pnpm@11.5.2");

    for (const workflow of WORKFLOWS) {
      const source = await workflowSource(workflow);
      assert.match(source, /pnpm install --frozen-lockfile/u, `${workflow} must install the root lockfile`);
      assert.match(source, /cache-dependency-path:\s*pnpm-lock\.yaml/u, `${workflow} must cache from the root lock`);
      for (const script of extractPnpmScripts(source)) {
        assert.ok(scripts[script], `${workflow} invokes missing root script pnpm ${script}`);
      }
      for (const pin of source.matchAll(/^[ \t]*(?:-[ \t]+)?uses:\s*\S+@([^\s#]+)/gmu)) {
        assert.match(pin[1] ?? "", /^[0-9a-f]{40}$/u, `${workflow} has an unpinned action: ${pin[0]}`);
      }
    }
  });

  for (const workflow of WORKFLOWS) {
    it(`${workflow} selects all root, patch, circuit, evidence, CAD and site inputs`, async () => {
      const source = await workflowSource(workflow);
      const pathBlocks = extractWorkflowPathBlocks(source);
      for (const [index, paths] of pathBlocks.entries()) {
        for (const path of REQUIRED_PATHS) {
          assert.ok(paths.includes(path), `${workflow} paths block ${index + 1} is missing ${path}`);
        }
      }
    });
  }

  it("component gate selects every traced PD20/P15 gate input on both events", async () => {
    const events = extractEventPaths(await workflowSource("component-spec-skills.yml"));
    assert.deepEqual(Object.keys(events).sort(), ["pull_request", "push"]);
    assert.deepEqual(events.push?.branches, ["main"], "push must stay main-only");
    assert.deepEqual(events.pull_request?.branches, [], "pull_request must not gain a branch filter");
    for (const [event, block] of Object.entries(events)) {
      assert.deepEqual(componentCoverageFailures(block.paths), [], `${event} block is missing gate inputs`);
      for (const [name, files] of COMPONENT_GATE_FIXTURES) {
        assert.ok(selectsAny(block.paths, files), `${event}: ${name} change does not schedule the component gate`);
      }
      for (const file of COMPONENT_GATE_UNRELATED) {
        assert.ok(!selectsAny(block.paths, [file]), `${event}: ${file} should not schedule the component gate`);
      }
    }
  });

  it("component coverage check fails when any input family is dropped from either event", async () => {
    const events = extractEventPaths(await workflowSource("component-spec-skills.yml"));
    for (const [event, block] of Object.entries(events)) {
      for (const family of COMPONENT_GATE_INPUTS) {
        const reduced = block.paths.filter((path) => path !== family.pattern);
        assert.equal(reduced.length, block.paths.length - 1, `${event} lacks ${family.pattern}`);
        const failures = componentCoverageFailures(reduced);
        assert.ok(failures.length > 0, `${event}: dropping ${family.pattern} went unnoticed`);
        assert.ok(failures.every((sample) => family.samples.includes(sample)), `${event}: unexpected ${failures.join(", ")}`);
      }
    }
  });

  it("every Python gate target is a selected path and every input family names real files", async () => {
    const gates = await readFile(join(REPO_ROOT, "circuit", "scripts", "run-python-gates.sh"), "utf8");
    const targets = new Set<string>();
    for (const match of gates.matchAll(/^(?:python3|bash)\s+(?:-m unittest discover -s\s+)?([\w./-]+)/gmu)) {
      const target = match[1] ?? "";
      if (target && !target.startsWith("-")) targets.add(target.endsWith(".py") || target.endsWith(".sh") ? target : `${target}/test_fixture.py`);
    }
    assert.ok(targets.has("manufacturing/sim/board-b20-phase33/test_fixture.py"), "phase33 gate target was not parsed");
    assert.ok(targets.has("scripts/pcb/board-p/nvm-intent-20v.py"), "20 V NVM gate target was not parsed");
    const events = extractEventPaths(await workflowSource("component-spec-skills.yml"));
    for (const [event, block] of Object.entries(events)) {
      for (const target of targets) {
        assert.ok(selectsAny(block.paths, [target]), `${event}: gate target ${target} is not a selected path`);
      }
    }
    const tracked = execFileSync("git", ["ls-files"], { cwd: REPO_ROOT, encoding: "utf8" }).split("\n");
    for (const family of COMPONENT_GATE_INPUTS) {
      for (const sample of family.samples) {
        assert.ok(tracked.includes(sample), `sample ${sample} is not a tracked file`);
        assert.ok(globMatches(family.pattern, sample), `${family.pattern} does not match its sample ${sample}`);
      }
    }
  });

  it("production and pull-request jobs retain strict gates, complete history and browser coverage", async () => {
    const main = await workflowSource("main-deploy.yml");
    const pr = await workflowSource("pr-checks.yml");
    const contracts: ReadonlyArray<readonly [string, string, readonly string[]]> = [
      ["main-deploy.yml", main, ["pnpm circuit:check", "pnpm check", "pnpm build", "pnpm check:site", "pnpm circuit:check-generated"]],
      ["pr-checks.yml", pr, [
        "pnpm circuit:check",
        "pnpm test:circuit",
        "pnpm test:compatibility",
        "pnpm check",
        "pnpm build",
        "pnpm test:model-viewer:browser",
        "pnpm exec zudo-circuit-doc check-browser",
        "pnpm check:site",
        "pnpm circuit:check-generated",
      ]],
    ];
    for (const [name, source, commands] of contracts) {
      for (const command of commands) {
        assert.ok(source.includes(command), `${name} omits ${command}`);
      }
      assert.match(source, /fetch-depth:\s*0/u, `${name} must preserve doc-history metadata`);
      assert.match(source, /ZUDO_DOC_BUILD_LOG:\s*\$\{\{ runner\.temp \}\}\/doc-build\.log/u);
    }
    assert.match(main, /CLOUDFLARE_API_TOKEN/u);
    assert.match(main, /CLOUDFLARE_ACCOUNT_ID/u);
    assert.match(main, /production domain/u);
    assert.match(pr, /preview alias/u);
    assert.match(pr, /route smoke/u);

    const component = await workflowSource("component-spec-skills.yml");
    for (const command of ["pnpm circuit:check", "pnpm test:circuit", "pnpm test:compatibility", "pnpm check"]) {
      assert.ok(component.includes(command), `component-spec-skills.yml omits ${command}`);
    }
    assert.match(component, /python-version:\s*'3\.12'/u);
    // CI and the local b4push share one Python gate script, so neither can drop a gate alone.
    assert.match(component, /bash circuit\/scripts\/run-python-gates\.sh/u);
    const b4push = await readFile(join(REPO_ROOT, "circuit", "scripts", "run-b4push.sh"), "utf8");
    assert.match(b4push, /bash circuit\/scripts\/run-python-gates\.sh/u);
    const gates = await readFile(join(REPO_ROOT, "circuit", "scripts", "run-python-gates.sh"), "utf8");
    assert.match(gates, /^set -euo pipefail$/mu);
    assert.match(gates, /validate\.py --strict/u);
    assert.match(gates, /unittest discover -s \.claude\/skills\/component-spec-audit\/scripts/u);
    assert.match(gates, /check_forward_tests\.py --strict/u);
    for (const spec of ["board_a_spec", "board_b_spec", "board_p_spec", "board_p15_spec"]) {
      assert.match(gates, new RegExp(`gen_schematic\\.py ${spec}\\b`, "u"));
    }
    assert.match(gates, /check_baseline\.py/u);
    assert.match(gates, /verify_geometry\.py/u);
    assert.match(gates, /check_decisions\.py/u);
    assert.match(gates, /board-p15\/nvm-image\.py --check/u);
    assert.match(gates, /gen_courtyards\.py --check/u);
    assert.match(gates, /check_bare_copper_attrs\.py/u);
    assert.match(component, /pnpm install --frozen-lockfile/u);
  });

  it("root commands own formatting, preparation, host build and the single-guard local gate", async () => {
    const packageJson = JSON.parse(await readFile(join(REPO_ROOT, "package.json"), "utf8")) as {
      scripts: Record<string, string>;
    };
    const docPackage = JSON.parse(await readFile(join(REPO_ROOT, "doc", "package.json"), "utf8")) as {
      scripts: Record<string, string>;
    };
    assert.match(packageJson.scripts.build ?? "", /^pnpm circuit:prepare &&/u);
    assert.match(packageJson.scripts["circuit:prepare"] ?? "", /circuit:project-check && zudo-circuit-doc models && zudo-circuit-doc generate/u);
    assert.match(packageJson.scripts["circuit:project-check"] ?? "", /validate\.py --strict.*check_forward_tests\.py --strict/u);
    assert.match(packageJson.scripts["check:site"] ?? "", /strict-anchors --strict-broken/u);
    assert.match(packageJson.scripts["check:site"] ?? "", /check-built-fragment-links/u);
    assert.match(packageJson.scripts["check:site"] ?? "", /check-zfb-link-warnings/u);
    assert.match(packageJson.scripts["b4push"] ?? "", /run-b4push\.sh/u);
    assert.match(packageJson.scripts["format:md:check"] ?? "", /doc\/src\/content\/docs/u);
    assert.equal(docPackage.scripts.build, "zfb build");
    assert.match(docPackage.scripts.dev ?? "", /pnpm --dir \.\. circuit:prepare/u);
    assert.match(docPackage.scripts["dev:circuit"] ?? "", /zudo-circuit-doc generate --watch --config circuit\.config\.ts/u);
    for (const retired of ["generate:components", "generate:models", "test:components", "b4push"]) {
      assert.equal(docPackage.scripts[retired], undefined, `doc/package.json still owns retired ${retired}`);
    }
  });
});

describe("generated-output drift gate", () => {
  it("checks exactly the generated trees through the tested HEAD comparison helper", async () => {
    const source = await readFile(join(REPO_ROOT, "circuit", "scripts", "check-generated-drift.sh"), "utf8");
    assert.match(source, /check-generated-diff\.sh/u);
    for (const path of DRIFT_PATHS) assert.ok(source.includes(path), `drift script omits ${path}`);
    const helper = await readFile(SCRIPT, "utf8");
    assert.match(helper, /git add --intent-to-add -A/u);
    assert.match(helper, /git diff --exit-code HEAD/u);
  });

  it("passes clean output and fails ordinary edits, tracked deletions, and new output", async () => {
    const baseline = await runDriftFixture();
    assert.equal(baseline.status, 0, baseline.stderr);

    const edited = await runDriftFixture(async (root) => {
      await writeFile(join(root, "generated", "ordinary.txt"), "edited output\n");
    });
    assert.notEqual(edited.status, 0, "an ordinary generated-file edit must fail");

    const deleted = await runDriftFixture(async (root) => {
      await rm(join(root, "generated", "deleted.txt"));
    });
    assert.notEqual(deleted.status, 0, "a tracked generated-file deletion must fail");

    const added = await runDriftFixture(async (root) => {
      await writeFile(join(root, "generated", "new.txt"), "new generated output\n");
    });
    assert.notEqual(added.status, 0, "an untracked generated file must fail");
  });
});

async function workflowSource(name: (typeof WORKFLOWS)[number]): Promise<string> {
  return readFile(join(REPO_ROOT, ".github", "workflows", name), "utf8");
}

function extractPnpmScripts(source: string): string[] {
  return [...source.matchAll(/(?<!\S)pnpm[ \t]+(?:run[ \t]+)?([\w:-]+)/gu)]
    .map((match) => match[1] ?? "")
    .filter((command) => command && !BUILTIN_PNPM_COMMANDS.has(command));
}

function extractWorkflowPathBlocks(source: string): string[][] {
  const lines = source.split(/\r?\n/u);
  const blocks: string[][] = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (!/^ {4}paths:\s*$/u.test(lines[index] ?? "")) continue;
    const paths: string[] = [];
    for (let next = index + 1; next < lines.length; next += 1) {
      const line = lines[next] ?? "";
      if (/^ {0,4}\S/u.test(line)) break;
      const match = /^ {6}-\s+["']?([^"'#]+?)["']?\s*$/u.exec(line);
      if (match?.[1] !== undefined) paths.push(match[1].trim());
    }
    blocks.push(paths);
  }
  assert.ok(blocks.length > 0, "workflow has no parsed path filters");
  return blocks;
}

type EventFilter = { branches: string[]; paths: string[] };

function extractEventPaths(source: string): Record<string, EventFilter> {
  const lines = source.split(/\r?\n/u);
  const start = lines.findIndex((line) => /^on:\s*$/u.test(line));
  assert.ok(start >= 0, "workflow has no on: block");
  const events: Record<string, EventFilter> = {};
  let event: string | undefined;
  let list: keyof EventFilter | undefined;
  for (const line of lines.slice(start + 1)) {
    if (/^\S/u.test(line)) break;
    const eventMatch = /^ {2}([\w-]+):\s*$/u.exec(line);
    if (eventMatch?.[1] !== undefined) {
      event = eventMatch[1];
      events[event] = { branches: [], paths: [] };
      list = undefined;
      continue;
    }
    assert.ok(!/^ {4}(?:paths|branches)-ignore:/u.test(line), `unsupported ignore filter: ${line.trim()}`);
    const listMatch = /^ {4}(branches|paths):\s*$/u.exec(line);
    if (listMatch?.[1] !== undefined) {
      list = listMatch[1] as keyof EventFilter;
      continue;
    }
    if (/^ {4}\S/u.test(line) && !/^ {4}#/u.test(line)) list = undefined;
    if (event === undefined || list === undefined || !/^ {6}-/u.test(line)) continue;
    const item = /^ {6}-\s+["']?([^"'#!]+?)["']?\s*$/u.exec(line);
    assert.ok(item?.[1] !== undefined, `unparsed or negated filter entry: ${line.trim()}`);
    events[event]![list].push(item[1].trim());
  }
  return events;
}

// GitHub path-filter globbing: `**` crosses directories, `*` stays within one segment.
function globMatches(pattern: string, file: string): boolean {
  const source = pattern
    .split("**")
    .map((part) => part.split("*").map((text) => text.replace(/[.+?^${}()|[\]\\]/gu, "\\$&")).join("[^/]*"))
    .join(".*");
  return new RegExp(`^${source}$`, "u").test(file);
}

function selectsAny(patterns: readonly string[], files: readonly string[]): boolean {
  return files.some((file) => patterns.some((pattern) => globMatches(pattern, file)));
}

function componentCoverageFailures(patterns: readonly string[]): string[] {
  return COMPONENT_GATE_INPUTS.flatMap((family) => family.samples).filter((sample) => !selectsAny(patterns, [sample]));
}

async function runDriftFixture(mutate?: (root: string) => Promise<void>): Promise<{
  status: number | null;
  stderr: string;
}> {
  const root = await mkdtemp(join(scratch, "git-fixture-"));
  try {
    await mkdir(join(root, "generated"), { recursive: true });
    await writeFile(join(root, "generated", "ordinary.txt"), "committed output\n");
    await writeFile(join(root, "generated", "deleted.txt"), "committed output\n");
    execFileSync("git", ["init", "-q"], { cwd: root });
    execFileSync("git", ["config", "user.name", "Workflow Fixture"], { cwd: root });
    execFileSync("git", ["config", "user.email", "fixture@example.invalid"], { cwd: root });
    execFileSync("git", ["add", "generated"], { cwd: root });
    execFileSync("git", ["commit", "-qm", "baseline"], { cwd: root });
    await mutate?.(root);
    const result = spawnSync("bash", [SCRIPT, "generated"], { cwd: root, encoding: "utf8" });
    if (result.error) throw result.error;
    return { status: result.status, stderr: result.stderr };
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}
