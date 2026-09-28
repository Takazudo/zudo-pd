import { stat, realpath } from "node:fs/promises";
import { join, sep } from "node:path";
import { corpus, root, internal } from "../tests/compatibility-helpers.mjs";
export async function assertModelPairs(paths) {
  for (const path of paths) {
    if (!(await stat(path)).isFile()) throw new Error(`WRL model missing: ${path}`);
    const step = path.replace(/\.wrl$/u, ".step");
    if (step === path || !(await stat(step)).isFile()) throw new Error(`paired STEP missing: ${step}`);
    const canonicalStep = await realpath(step);
    if (!canonicalStep.startsWith(`${root}${sep}`)) throw new Error(`paired STEP escapes project: ${step}`);
  }
}
const { mapped, index } = await corpus(root);
const { assertFootprintLibraryParity } = await internal("footprint-previews/parity.js");
await assertFootprintLibraryParity(mapped.paths.footprintMasterRoot, mapped.paths.footprintLibraryRoot);
await assertModelPairs(index.references.packages.filter(p=>p.modelPath!==null).map(p=>join(root,p.modelPath)));
console.log(`PASS: dual footprint-library bytes and ${index.references.packages.length} local STEP/WRL pairs`);
