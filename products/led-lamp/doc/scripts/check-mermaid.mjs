import { readFile, readdir } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const docsRoot = path.resolve("src/content/docs");
const mermaidUrl = import.meta.resolve("mermaid");
const mermaidRequire = createRequire(mermaidUrl);
const dompurifyEntryPath = mermaidRequire.resolve("dompurify");
const dompurifyPackagePath = path.resolve(
  path.dirname(dompurifyEntryPath),
  "..",
  "package.json",
);
const dompurifyPackage = JSON.parse(await readFile(dompurifyPackagePath, "utf8"));
const dompurifyModulePath = path.resolve(
  path.dirname(dompurifyPackagePath),
  dompurifyPackage.module ?? "dist/purify.es.mjs",
);
const { default: DOMPurify } = await import(pathToFileURL(dompurifyModulePath));

// Mermaid's Node entry imports DOMPurify's browser factory. Parsing trusted
// repository sources does not need sanitization, so supply the two browser-only
// methods Mermaid calls while building its flowchart database.
DOMPurify.addHook ??= () => {};
DOMPurify.sanitize ??= (value) => value;

const { default: mermaid } = await import("mermaid");
mermaid.initialize({ startOnLoad: false });

async function collectDocs(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectDocs(entryPath)));
    } else if (/\.mdx?$/.test(entry.name)) {
      files.push(entryPath);
    }
  }

  return files;
}

const failures = [];
let diagramCount = 0;

for (const file of await collectDocs(docsRoot)) {
  const markdown = await readFile(file, "utf8");
  const diagrams = [...markdown.matchAll(/```mermaid[^\S\r\n]*\r?\n([\s\S]*?)```/g)];

  for (const [index, match] of diagrams.entries()) {
    diagramCount += 1;
    const source = match[1].replace(/\r\n?/g, "\n").trim();
    const collapsedSource = source.replace(/\s+/g, " ");

    try {
      // Production minification collapses data-mermaid text. Parsing that exact
      // shape prevents diagrams from silently depending on authored newlines.
      await mermaid.parse(collapsedSource, { suppressErrors: true });
    } catch (error) {
      failures.push({
        file: path.relative(process.cwd(), file),
        block: index + 1,
        message: error instanceof Error ? error.message : String(error),
      });
    }
  }
}

if (diagramCount === 0) {
  throw new Error(`No Mermaid diagrams found under ${docsRoot}`);
}

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`FAIL ${failure.file} (Mermaid block ${failure.block})`);
    console.error(failure.message);
  }
  process.exitCode = 1;
} else {
  console.log(`Validated ${diagramCount} collapsed Mermaid diagrams.`);
}
