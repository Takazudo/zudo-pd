import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve, join } from 'node:path';
import { cp, mkdir, mkdtemp, readFile, symlink, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
export const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
export const packageRoot = dirname(fileURLToPath(import.meta.resolve('@takazudo/zudo-circuit-doc/package.json')));
export const internal = path => import(pathToFileURL(join(packageRoot, 'lib', path)).href);
export const json = async path => JSON.parse(await readFile(path, 'utf8'));
export async function scratch() {
  const dir = await mkdtemp(join(tmpdir(), 'zudo-pd-compatibility-'));
  for (const path of ['.claude', 'scripts/schgen', 'footprints/kicad', 'symbols', 'circuit/publication', 'circuit.config.ts', 'doc/src/content/docs/components', 'doc/public/assets/component-previews']) {
    await mkdir(dirname(join(dir, path)), { recursive: true });
    await cp(join(root, path), join(dir, path), { recursive: true });
  }
  await symlink(join(root, 'node_modules'), join(dir, 'node_modules'), 'dir');
  return dir;
}
export const dispose = dir => rm(dir, { recursive: true, force: true });
export function cli(dir, command, args = []) {
  const run = spawnSync(process.execPath, [join(packageRoot, 'bin/zudo-circuit-doc.js'), command, '--config', join(dir, 'circuit.config.ts'), ...args], {encoding: 'utf8', timeout: 60000});
  if (run.error) throw run.error;
  if (run.signal || !Number.isInteger(run.status)) throw new Error(`${command} did not complete: ${run.signal}`);
  return run;
}
export async function mutate(dir, path, apply) {
  const file = join(dir, path), data = await json(file);
  apply(data);
  await writeFile(file, JSON.stringify(data, null, 2) + '\n');
}
export async function mapping(dir) {
  const {loadCircuitConfig} = await internal('config/load.js');
  const {mapCircuitConfig} = await internal('config/map.js');
  const loaded = await loadCircuitConfig({cwd: dir, configPath: join(dir, 'circuit.config.ts')});
  const {resolveCircuitConfig} = await internal('config/resolve.js');
  return mapCircuitConfig(resolveCircuitConfig(loaded.config, loaded.configDir));
}
export async function corpus(dir) {
  const mapped = await mapping(dir);
  const {readEvidenceIndex, projectIndex} = await internal('provider/v1/index.js');
  const {PublicationPolicy} = await internal('core/publication.js');
  const index = await readEvidenceIndex({paths: mapped.paths, selection: mapped.selection, reference: mapped.reference});
  const model = projectIndex(index, new PublicationPolicy(mapped.matrix, mapped.selection));
  return {mapped,index,model};
}
