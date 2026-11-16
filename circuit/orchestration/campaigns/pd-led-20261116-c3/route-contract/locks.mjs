import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const pdManifestPattern = /^\.claude\/skills\/component-[^/]+\/manifest\.json$/u;

export function discoverPdManifests(root) {
  const pdRoot = join(root, '.claude/skills');
  return readdirSync(pdRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith('component-'))
    .map((entry) => `.claude/skills/${entry.name}/manifest.json`)
    .filter((path) => existsSync(join(root, path))).sort();
}

export function verifyLockedCorpus(root, locks, sourceSetSha256) {
  const sorted = Object.fromEntries(Object.entries(locks).sort(([left], [right]) =>
    left < right ? -1 : left > right ? 1 : 0));
  if (hash(Buffer.from(JSON.stringify(sorted))) !== sourceSetSha256) {
    throw new Error('proposal source-set digest mismatch');
  }
  const expected = Object.keys(locks).filter((path) => pdManifestPattern.test(path)).sort();
  const actual = discoverPdManifests(root);
  const added = actual.filter((path) => !expected.includes(path));
  const removed = expected.filter((path) => !actual.includes(path));
  if (added.length || removed.length) {
    throw new Error(`PD manifest set drift: added=${JSON.stringify(added)} removed=${JSON.stringify(removed)}`);
  }
  const verifiedBytes = new Map();
  for (const [path, expectedHash] of Object.entries(locks)) {
    let bytes;
    try { bytes = readFileSync(join(root, path)); }
    catch (error) {
      if (error.code === 'ENOENT') throw new Error(`locked input removed: ${path}`);
      throw error;
    }
    if (hash(bytes) !== expectedHash) throw new Error(`locked input changed: ${path}`);
    verifiedBytes.set(path, bytes);
  }
  return { locked_source_files_verified: Object.keys(locks).length,
    locked_pd_manifest_files_verified: expected.length, verifiedBytes };
}
