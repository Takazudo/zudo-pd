import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../../../..');
const { anchor, assertUnique, recordSlug } = await import(pathToFileURL(join(root, 'node_modules/@takazudo/zudo-circuit-doc/lib/core/ids.js')));
const { recordRoute, integrationRoute } = await import(pathToFileURL(join(root, 'node_modules/@takazudo/zudo-circuit-doc/lib/core/site.js')));

test('pinned package rejects invalid and reserved route identities', () => {
  assert.throws(() => recordSlug('rec-index'), /reserved slug/);
  assert.throws(() => recordSlug('rec-404'), /usable slug/);
  assert.throws(() => recordSlug('rec-Bad'), /usable slug/);
  assert.throws(() => anchor('fact bad'), /usable as an anchor/);
  assert.throws(() => assertUnique('route', ['/docs/components/records/x/', '/docs/components/records/x/']), /duplicate route/);
  assert.equal(recordRoute(recordSlug('rec-example'), anchor('fact-example')),
    '/docs/components/records/example/#fact-example');
  assert.equal(integrationRoute(anchor('calc-example')),
    '/docs/components/integration/#calc-example');
});

test('actual proposal has valid unique routes and exposes calculation gap', () => {
  const fresh = JSON.parse(execFileSync(process.execPath, [join(here, 'check.mjs')], { encoding: 'utf8' }));
  const committed = JSON.parse(readFileSync(join(here, 'result.json'), 'utf8'));
  assert.deepEqual(fresh, committed);
  assert.equal(fresh.proposed_led_record_routes, 35);
  assert.equal(fresh.changed_legacy_led_routes, 35);
  assert.deepEqual(fresh.invalid_proposed_anchor_ids, []);
  assert.equal(fresh.duplicate_record_routes, 0);
  assert.equal(fresh.duplicate_integration_routes, 0);
  assert.equal(fresh.calculation_review.length, 9);
  assert.ok(fresh.calculation_review.every((row) => row.unchanged_id_in_c3c &&
    row.translated_fact_ids_in_structured_table && row.old_fact_aliases_still_in_expression.length > 0));
});
