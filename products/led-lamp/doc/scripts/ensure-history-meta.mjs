import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

// The history plugin replaces this ignored file before a site build. Type
// checking and a clean standalone build still need the import to resolve.
const target = resolve(import.meta.dirname, '../.zfb/doc-history-meta.json');
await mkdir(dirname(target), { recursive: true });
try {
  await writeFile(target, '{}\n', { flag: 'wx' });
} catch (error) {
  if (error?.code !== 'EEXIST') throw error;
}
