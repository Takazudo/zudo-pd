import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../../../..');
const result = JSON.parse(readFileSync(join(here, 'result.json'), 'utf8'));
const idsRelative = 'node_modules/@takazudo/zudo-circuit-doc/lib/core/ids.js';
const idsPath = join(root, idsRelative);
assert.equal(createHash('sha256').update(readFileSync(idsPath)).digest('hex'),
  result.tool_sha256[idsRelative]);
const { anchor, assertUnique } = await import(pathToFileURL(idsPath));
const pdRuleBytes = readFileSync(join(root,
  '.claude/skills/circuit-spec-integration/references/rules.json'));
assert.equal(createHash('sha256').update(pdRuleBytes).digest('hex'), result.pd_rules_sha256);
const pdRules = JSON.parse(pdRuleBytes).rules;

test('nine proposed calculation IDs satisfy the pinned generator anchor contract', () => {
  const pdIds = pdRules.flatMap((rule) => (rule.conditioned_calculations ?? [])
    .map((calc) => calc.calculation_id));
  const proposed = result.calculation_rows.map((row) => row.proposed_calculation_id);
  assert.equal(proposed.length, 9);
  assert.deepEqual(proposed.map(anchor), proposed);
  assert.doesNotThrow(() => assertUnique('calculation anchor', [...pdIds, ...proposed]));
});
