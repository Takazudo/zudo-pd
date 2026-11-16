// Read-only audit against the installed, pinned 0.3.0 route and anchor functions.
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../../../..');
const installed = join(root, 'node_modules/@takazudo/zudo-circuit-doc');
const idsPath = join(installed, 'lib/core/ids.js');
const sitePath = join(installed, 'lib/core/site.js');
const { anchor, assertUnique, recordSlug, SLUG_PATTERN } = await import(pathToFileURL(idsPath));
const { recordRoute, integrationRoute } = await import(pathToFileURL(sitePath));

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
const sha256 = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');
const proposalPath = join(root, 'circuit/orchestration/campaigns/pd-led-20261116-c3/translation/proposal.json');
const proposal = readJson(proposalPath);
const packageJson = readJson(join(installed, 'package.json'));
if (packageJson.version !== '0.3.0' || proposal.schema !== 'pd-led-c3c-evidence-translation/1') {
  throw new Error('unexpected package or proposal contract');
}

const pdRoot = join(root, '.claude/skills');
const pdRecordIds = readdirSync(pdRoot)
  .filter((name) => name.startsWith('component-'))
  .flatMap((name) => {
    try { return readJson(join(pdRoot, name, 'manifest.json')).records.map((record) => record.record_id); }
    catch (error) { if (error.code === 'ENOENT') return []; throw error; }
  });
const proposedRecords = proposal.mappings.filter((row) => row.kind === 'record');
const allRecords = [...pdRecordIds, ...proposedRecords.map((row) => row.proposed_id)];
const routes = allRecords.map((id) => recordRoute(recordSlug(id)));
assertUnique('record route', routes);
const legacyRouteMap = proposedRecords.map((row) => ({
  old_id: row.old_id,
  legacy_led_route: recordRoute(recordSlug(row.old_id)),
  proposed_route: recordRoute(recordSlug(row.proposed_id)),
}));
for (const row of proposal.mappings) anchor(row.proposed_id);
for (const id of allRecords) anchor(id);

const pdRulesPath = join(pdRoot, 'circuit-spec-integration/references/rules.json');
const ledRulesPath = join(root, 'products/led-lamp/.claude/skills/circuit-spec-integration/references/rules.json');
const pdRules = readJson(pdRulesPath).rules;
const ledRules = readJson(ledRulesPath).rules;
const ruleMap = new Map(proposal.mappings.filter((row) => row.kind === 'rule')
  .map((row) => [row.old_id, row.proposed_id]));
const pdIntegrationIds = pdRules.flatMap((rule) => [rule.rule_id,
  ...(rule.conditioned_calculations ?? []).map((calc) => calc.calculation_id)]);
const ledIntegrationIds = ledRules.flatMap((rule) => [ruleMap.get(rule.rule_id),
  ...(rule.conditioned_calculations ?? []).map((calc) => calc.calculation_id)]);
if (ledIntegrationIds.some((id) => !id)) throw new Error('rule has no proposed ID');
const integrationRoutes = [...pdIntegrationIds, ...ledIntegrationIds].map((id) => integrationRoute(anchor(id)));
assertUnique('integration anchor route', integrationRoutes);

// The C3c structured-reference table does not include calculation IDs or
// expression aliases in integration rules. A route pass is not closure for them.
const calculationReview = ledRules.flatMap((rule) => (rule.conditioned_calculations ?? []).map((calc) => {
  const factSymbols = calc.fact_ids.map((id) => id.replaceAll('-', '_'));
  const oldSymbols = new Set(calc.expression.match(/[A-Za-z_][A-Za-z_0-9]*/g) ?? []);
  return {
    rule_id: rule.rule_id,
    calculation_id: calc.calculation_id,
    unchanged_id_in_c3c: !proposal.mappings.some((row) => row.old_id === calc.calculation_id),
    old_fact_aliases_still_in_expression: factSymbols.filter((symbol) => oldSymbols.has(symbol)),
    translated_fact_ids_in_structured_table: calc.fact_ids.every((id) => proposal.mappings.some((row) => row.kind === 'fact' && row.old_id === id)),
  };
}));
const sourceLocks = Object.fromEntries([
  proposalPath, join(root, 'pnpm-lock.yaml'), join(root, 'patches/@takazudo__zudo-circuit-doc@0.3.0.patch'),
  idsPath, sitePath, join(installed, 'lib/core/mdx.js'),
  join(installed, 'lib/provider/v1/index.js'), join(installed, 'lib/provider/v1/integration.js'),
  join(installed, 'python/circuit_evidence/integration/rules.py'), pdRulesPath, ledRulesPath,
].map((path) => [path.slice(root.length + 1), sha256(path)]));

const result = {
  schema: 'pd-led-c3e-route-contract/1',
  base_commit: 'f008ad037681bca977005b4353affa9928f0d146',
  installed_package_version: packageJson.version,
  proposal_source_set_sha256: proposal.source_set_sha256,
  inspected_file_sha256: sourceLocks,
  pd_record_routes: pdRecordIds.length,
  proposed_led_record_routes: proposedRecords.length,
  changed_legacy_led_routes: legacyRouteMap.filter((row) => row.legacy_led_route !== row.proposed_route).length,
  legacy_led_route_map: legacyRouteMap,
  proposed_record_slug_prefix: recordSlug(proposedRecords[0].proposed_id).split('-').slice(0, 2).join('-'),
  invalid_proposed_anchor_ids: proposal.mappings.filter((row) => !SLUG_PATTERN.test(row.proposed_id)).map((row) => row.proposed_id),
  duplicate_record_routes: 0,
  pd_integration_anchors: pdIntegrationIds.length,
  led_integration_anchors: ledIntegrationIds.length,
  duplicate_integration_routes: 0,
  calculation_review: calculationReview,
  holds: [
    'Current installed 0.3.0 route/anchor syntax passes; no generated page was built.',
    'C3c does not translate LED calculation_id or the fact aliases in integration calculation expressions.',
    'Nine current calculation IDs do not collide with PD today; later canonical work must review their identity and expression/structured fact IDs together.',
    'All legacy LED record routes would change; C5 must review old paths and fragments before any cutover.',
    'Textual, exact identity, CAD/SMAJ, DNP, publication, private resource and physical holds remain.',
  ],
};
console.log(JSON.stringify(result, null, 2));
