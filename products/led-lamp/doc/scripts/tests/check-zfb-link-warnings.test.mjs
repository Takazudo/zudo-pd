// Negative and positive cases for the build-log link gate (#127).
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const script = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../check-zfb-link-warnings.sh");
const ESC = "\u001b";
const GEN = "/repo/doc/src/content/docs/components/records/al8860mp-13/index.mdx";
const AUTHORED = "/repo/doc/src/content/docs/architecture/board-l.mdx";
const BUILT = "✓ 197 pages built in 32.00s";

function run(lines, { generated = true } = {}) {
  const dir = mkdtempSync(path.join(tmpdir(), "zfb-gate-test-"));
  try {
    const log = path.join(dir, "build.log");
    writeFileSync(log, lines.join("\n") + "\n");
    const genDir = path.join(dir, "components");
    mkdirSync(genDir);
    if (generated) writeFileSync(path.join(genDir, "index.mdx"), "---\ntitle: x\n---\n");
    const result = spawnSync("bash", [script, log], {
      encoding: "utf8",
      env: { ...process.env, GITHUB_ACTIONS: "", ZFB_LINK_GATE_GENERATED_DIR: genDir },
    });
    return { code: result.status, out: result.stdout + result.stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("accepts generated-anchor warnings in both the 2.x and ZB001 shapes", () => {
  const r = run([
    `zfb warn: ${GEN}: broken link: #src-al8860-ds39014`,
    `zfb warn: ZB001 ${GEN}: broken link: #fact-al8860-vin`,
    BUILT,
  ]);
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /suppressed\s+2 same-page fragment/);
});

test("fails on a broken hand-authored link", () => {
  const r = run([`zfb warn: ZB001 ${GEN}: broken link: #a`, `zfb warn: ZB001 ${AUTHORED}: broken link: #missing`, BUILT]);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /board-l\.mdx: broken link: #missing/);
});

test("fails on a generated-tree link to another page", () => {
  const r = run([`zfb warn: ZB001 ${GEN}: broken link: #a`, `zfb warn: ZB001 ${GEN}: broken link: /docs/nowhere/`, BUILT]);
  assert.equal(r.code, 1, r.out);
});

test("sees a hand-authored broken link behind ANSI colour codes", () => {
  const r = run([
    `${ESC}[33mzfb warn:${ESC}[0m ZB001 ${GEN}: broken link: #a`,
    `${ESC}[33mzfb warn: ${ESC}[0mZB001 ${AUTHORED}: broken link: #missing`,
    BUILT,
  ]);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /board-l\.mdx/);
});

test("sees a hand-authored broken link behind a timestamp or label prefix", () => {
  const r = run([
    `[12:00:01] zfb warn: ZB001 ${GEN}: broken link: #a`,
    `2026-11-08T00:00:00Z zfb warn: ZB001 ${AUTHORED}: broken link: #missing`,
    BUILT,
  ]);
  assert.equal(r.code, 1, r.out);
});

test("fails on an unrecognised warning shape, including another diagnostic code", () => {
  assert.equal(run([`zfb warn: ZB001 ${GEN}: broken link: #a`, "zfb warn: ZB005 x.tsx:1:1: pragma", BUILT]).code, 1);
  assert.equal(run([`zfb warn: ZB001 ${GEN}: broken link: #a`, "zfb warn: plain CSS import `a.css` was dropped", BUILT]).code, 1);
});

test("a changed warning prefix cannot pass silently while generated pages exist", () => {
  const r = run([`zfb warning: ZB001 ${GEN}: broken link: #a`, `zfb warning: ZB001 ${AUTHORED}: broken link: #missing`, BUILT]);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /recognised no|no generated-anchor link warning/);
});

test("a log without zfb's build-complete line is refused", () => {
  assert.equal(run([`zfb warn: ZB001 ${GEN}: broken link: #a`]).code, 1);
  assert.equal(run([]).code, 1);
});

test("an empty generated tree does not require generated-anchor warnings", () => {
  assert.equal(run([BUILT], { generated: false }).code, 0);
});

test("usage error without a readable log", () => {
  const result = spawnSync("bash", [script, "/nonexistent/build.log"], { encoding: "utf8" });
  assert.equal(result.status, 2);
});

const HIST = [
  "zfb warn: ZB006 plugin-host:stdout: doc-history-server: content-dir resolved to /repo/doc/src/content/docs",
  "zfb warn: ZB006 plugin-host:stdout: Processing default: 57 files in /repo/doc/src/content/docs",
  "zfb warn: ZB006 plugin-host:stdout: Generated 57 history files in 2.2s",
];

test("accepts the three doc-history progress messages in the zfb 5 ZB006 and 2.x shapes", () => {
  const r = run([
    `zfb warn: ZB001 ${GEN}: broken link: #a`,
    ...HIST,
    "zfb warn: [plugin-host stdout] Generated 57 history files in 2.2s",
    BUILT,
  ]);
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /suppressed\s+4 doc-history progress/);
});

test("rejects other ZB006 plugin output, including the INIT_CWD fallback on stderr", () => {
  const base = [`zfb warn: ZB001 ${GEN}: broken link: #a`, BUILT];
  for (const extra of [
    'zfb warn: ZB006 plugin-host:stderr: doc-history-server: INIT_CWD candidate "/repo/src/content/docs" does not exist; falling back to process.cwd()',
    "zfb warn: ZB006 plugin-host:stderr: Generated 57 history files in 2.2s",
    "zfb warn: ZB006 plugin-host:stdout: Generated many history files",
    "zfb warn: ZB006 plugin-host:stdout: Processing default: 57 files in /repo/doc/src/content/other",
    "zfb warn: ZB006 /repo/doc/src/content/docs/architecture/board-l.mdx: broken link: #missing",
    "zfb warn: Generated 57 history files in 2.2s",
  ]) {
    const r = run([...base, extra]);
    assert.equal(r.code, 1, `${extra}\n${r.out}`);
  }
});


test("generated-path payloads cannot disguise unknown diagnostics or plugin output", () => {
  for (const prefix of [
    "ZB999 ",
    "ZB006 plugin-host:stderr: ",
    "ZB006 plugin-host:stdout: ",
    "[plugin-host stdout] ",
  ]) {
    const disguised = `zfb warn: ${prefix}${GEN}: broken link: #missing`;
    // Reject even alongside a genuine warning: liveness alone is insufficient.
    for (const lines of [[disguised, BUILT], [`zfb warn: ZB001 ${GEN}: broken link: #a`, disguised, BUILT]]) {
      const r = run(lines);
      assert.equal(r.code, 1, `${disguised}\n${r.out}`);
      assert.match(r.out, /outside the known-false class/);
    }
  }
});
