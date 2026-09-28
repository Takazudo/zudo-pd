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
    assert.match(component, /unittest discover -s \.claude\/skills\/component-spec-audit\/scripts/u);
    assert.match(component, /check_forward_tests\.py --strict/u);
    assert.match(component, /gen_schematic\.py board_[abp]_spec/u);
    assert.match(component, /check_baseline\.py/u);
    assert.match(component, /verify_geometry\.py/u);
    assert.match(component, /gen_courtyards\.py --check/u);
    assert.match(component, /check_bare_copper_attrs\.py/u);
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
