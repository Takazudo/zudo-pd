import { createHash } from 'node:crypto';
import { readFile, readdir, realpath } from 'node:fs/promises';
import { join } from 'node:path';

const inputHashes = {
  'patches/@takazudo__zudo-circuit-doc@0.3.0.patch': '7991370866d4019bc1c7b2411e9421c18ba701a850f580c49c4d098e8b005e6c',
  'products/led-lamp/pnpm-lock.yaml': '6987246726a2cfa4aeb01cddb6825c3224f62ac64f62b2d00c7d0f8ae91a81d3',
  'products/led-lamp/doc/src/content/docs/components/records/c15849/index.mdx': 'f268aff069a8856587b7978b9262b25280e9cb8c655dfb432e8dcfa608bdd32b',
  'products/led-lamp/.claude/skills/component-stusb4500qtr/routing.json': '70ee838bacc3adee8eec210d80e02ea3d7b8a052008e66f15a4800b289e0c383',
};
const packageHashes = {
  'package.json': '515ab077229809efcd6f533b7c511cfcbdb4132ec2bee51d8f2e6f11fe390bd0',
  'lib/core/reference-descriptor.js': '41ed8727e9a0fc25f1fcbb1a089b182a5634796e60196581cede3088e698e061',
  'lib/ui/component-references.js': '2d9353b95ee036678d73ba0a927091e228238d25bcb5dd22180e945beea6557c',
};
const changedPackageHashes = {
  unified: {
    'lib/browser-smoke/cdp.js': '66f73b592160e4364809a97ef55d2d75558fbc8635597d6ed4891699435c2e8e',
    'lib/browser-smoke/chrome.js': '893e6abbfed1c3ee9a3fb0ef6b35209b0d46397566f7c21c5b67c0173d89e44a',
    'lib/scan/built-references.js': 'd2ea6cb4c52806dab3eb6ed4c9f589fdbde94fe36c533778ca83a7d9355bedb0',
    'python/circuit_evidence/routing.py': 'efd532f2f48992026e93f2651c0ba6768eea78f60b6c08e860590bea96854bea',
  },
  separate: {
    'lib/browser-smoke/cdp.js': 'd26c84c0920adf70d1892e30a30d7ac8761ce62509ae4bdf24ea1e242502e962',
    'lib/browser-smoke/chrome.js': 'b0368246efca5ea92b82d05de19fddb51bdeb061f143a4ab78f16cbcbf5cedd3',
    'lib/scan/built-references.js': '243420f726d8fa3781824e550bc103281e55498fe0a1d106558b3ffa566ffc51',
    'python/circuit_evidence/routing.py': '0ef884503557a755f3b8c468e377fa5040bac8fe8aa24ea5bf0458df3c32e19e',
  },
};
const transitiveHashes = {
  unified: {
    'hono@4.13.16': ['hono/dist/hono.js', '738a8bd80409502c22053c6c9a81196dcef373974a720c6f254634c742add525'],
    'parse5@8.1.0': ['parse5/dist/index.js', '40588f3496c59345bc65d86563c42ab8246f1b2edc8d3e8e9535b921d6a45a07'],
    '@jridgewell+resolve-uri@3.1.3': ['@jridgewell/resolve-uri/dist/resolve-uri.mjs', 'a363be70b71dbaf1b3e6fd25c35e45e3cd8993104bc4d9551c0568b6fd76963b'],
  },
  separate: {
    'hono@4.13.17': ['hono/dist/hono.js', '738a8bd80409502c22053c6c9a81196dcef373974a720c6f254634c742add525'],
    'parse5@8.1.1': ['parse5/dist/index.js', '40588f3496c59345bc65d86563c42ab8246f1b2edc8d3e8e9535b921d6a45a07'],
    '@jridgewell+resolve-uri@3.1.2': ['@jridgewell/resolve-uri/dist/resolve-uri.mjs', '92bc7d86f012f0a1a38447512014d2decabeec0663bcebf49b95ca6081722b90'],
  },
};

export function assertBoundBytes(bytes, expected, path) {
  const actual = createHash('sha256').update(bytes).digest('hex');
  if (actual !== expected) {
    throw new Error(`source binding mismatch: ${path}; expected ${expected}, got ${actual}`);
  }
}

async function assertBoundFile(path, expected, readBytes) {
  assertBoundBytes(await readBytes(path), expected, path);
}

export async function verifyBindings(unified, separate, ledSource, readBytes = readFile) {
  const repository = join(ledSource, '..', '..');
  for (const [relative, hash] of Object.entries(inputHashes)) {
    await assertBoundFile(join(repository, relative), hash, readBytes);
  }
  await assertBoundFile(join(unified, 'pnpm-lock.yaml'),
    '4642e444fcfe57682deea81634073311c1ffafaf530b8f0c077247544521a6c4', readBytes);
  await assertBoundFile(join(separate, 'pnpm-lock.yaml'), inputHashes['products/led-lamp/pnpm-lock.yaml'], readBytes);
  for (const [label, root, nested] of [['unified', unified, true], ['separate', separate, false]]) {
    const packageRoot = await realpath(join(root, nested
      ? 'products/led-lamp/node_modules/@takazudo/zudo-circuit-doc'
      : 'node_modules/@takazudo/zudo-circuit-doc'));
    for (const [relative, hash] of Object.entries({ ...packageHashes, ...changedPackageHashes[label] })) {
      await assertBoundFile(join(packageRoot, relative), hash, readBytes);
    }
    const installed = new Set(await readdir(join(root, 'node_modules/.pnpm')));
    for (const [folder, [relative, hash]] of Object.entries(transitiveHashes[label])) {
      if (!installed.has(folder)) throw new Error(`source binding mismatch: missing ${folder}`);
      await assertBoundFile(join(root, 'node_modules/.pnpm', folder, 'node_modules', relative), hash, readBytes);
    }
  }
}
