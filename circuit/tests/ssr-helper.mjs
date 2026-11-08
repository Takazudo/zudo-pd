// The only file that names the SSR engine: the installed zudo-react server
// renderer, with the package's real island roots registered so Island markup
// renders exactly as the published host bundle would render it.
import { build } from 'esbuild';
import { join } from 'node:path';
import { root, packageRoot } from './compatibility-helpers.mjs';
export async function bundleForSsr(uiModule, names) {
  const result = await build({
    stdin: {
      contents: [
        `export {${names.join(',')}} from ${JSON.stringify(join(packageRoot, 'lib', uiModule))};`,
        'export { h } from "@takazudo/zfb/zudo-react";',
        'import { renderToString } from "@takazudo/zfb/zudo-react/server";',
        'import { withIslandTestContext } from "@takazudo/zfb/zudo-react/testing";',
        `import { FootprintPreviewIsland } from ${JSON.stringify(join(packageRoot, 'lib/islands/footprint-preview-island.js'))};`,
        `import { PackageModelViewerIsland } from ${JSON.stringify(join(packageRoot, 'lib/islands/package-model-viewer-island.js'))};`,
        'export const render = (node) => withIslandTestContext({ components: { FootprintPreviewIsland, PackageModelViewerIsland } }, () => renderToString(node));',
      ].join('\n'),
      resolveDir: root,
      loader: 'js',
    },
    bundle: true, write: false, platform: 'node', format: 'esm', logLevel: 'silent',
  });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`);
}
