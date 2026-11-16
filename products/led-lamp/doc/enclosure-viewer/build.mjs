import { build } from "esbuild";
import { copyFile, mkdir, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import "./check-geometry.mjs";

const source = fileURLToPath(new URL("./", import.meta.url));
const output = fileURLToPath(new URL("../public/assets/enclosure/", import.meta.url));
await mkdir(output, { recursive: true });
const root = new URL("../../", import.meta.url);
execFileSync("python3", [fileURLToPath(new URL("enclosure/verify_exports.py", root))], { stdio: "inherit" });
const manifest = JSON.parse(await readFile(`${output}manifest.json`, "utf8"));
if (!manifest.pcb_models_checked) throw new Error("Enclosure PCB clearance checks missing. Run uv run enclosure/generate.py");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
for (const [path, hash] of Object.entries(manifest.source_hashes)) {
  if (sha(await readFile(new URL(path, root))) !== hash) throw new Error(`Enclosure source changed: ${path}. Regenerate CAD.`);
}
for (const [name, board] of Object.entries(manifest.board_sources)) {
  if (sha(await readFile(new URL(`boards/${name}/${name}.kicad_pcb`, root))) !== board.sha256) throw new Error(`Enclosure PCB changed: ${name}. Regenerate CAD.`);
}
for (const part of manifest.parts) {
  if (sha(await readFile(`${output}${part.file}`)) !== part.sha256) throw new Error(`Enclosure mesh changed: ${part.name}. Regenerate CAD.`);
}
await build({ entryPoints: [`${source}viewer.js`], bundle: true, format: "esm", minify: true,
  outfile: `${output}viewer.js`, legalComments: "eof", target: "es2022" });
await Promise.all([copyFile(`${source}index.html`, `${output}index.html`), copyFile(`${source}viewer.css`, `${output}viewer.css`)]);
console.log("Built enclosure viewer");
