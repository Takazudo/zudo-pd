import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, realpath, mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { extractHeadings, extractAllHeadingIds } from '@takazudo/zudo-doc/extract-headings';
import { root } from './compatibility-helpers.mjs';
const requireDoc=createRequire(join(root,'doc/package.json'));
const {renderHtml}=await import(pathToFileURL(requireDoc.resolve('@takazudo/zfb-md-wasm/render')).href);
const ids=html=>[...html.matchAll(/<h[2-6]\b[^>]*\bid="([^"]+)"/gu)].map(m=>m[1]);
async function nativeIds(source, filename='heading-parity.md'){
 const result=await renderHtml(source,{filename,pipeline:{features:{headingIds:{strategy:'hierarchical'}}}});
 assert.deepEqual(result.diagnostics,[],JSON.stringify(result.diagnostics));assert.ok(result.html!==null);
 return ids(result.html);
}

test('installed heading helper matches native IDs for full entities, protected escapes/code, Unicode and deep headings',async()=>{
 const source=[
  '## Parent &copy; &frac12; &#62; &#x2192; 日本語',
  '### Ordinary &gt;1000ms and &lt;2mm &nbsp; &NotEqualTilde; &amp;lt;',
  '### Code `&lt;2mm &copy;` and \\&gt;1000ms',
  '### Escaped \\*asterisks\\* and \\_underscores\\_ with **strong** and [link](https://example.test/)',
  '### Numeric &#0; &#x80; &#xD800; &#x110000; &#000000060; and unknown &notARealEntity;',
  '### Control &#1; &#9; &#10; &#13; &#31; &#127; &#159; and &Tab; &NewLine; &#xFFFF;',
  '#### Child arrow → 13.5 V',
  '##### Deep h5 `code_text`',
  '###### Deep h6 日本語',
  '##### Deep h5 `code_text`',
  '## Parent &copy; &frac12; &#62; &#x2192; 日本語',
  '### Repeat',
 ].join('\n\n');
 assert.deepEqual(extractAllHeadingIds(source),await nativeIds(source));
 assert.equal(extractAllHeadingIds(source).length,12);
 const toc=extractHeadings(source);assert.ok(toc.every(h=>h.depth<=4));assert.ok(toc.some(h=>h.text.includes('>1000ms')));assert.ok(toc.some(h=>h.text.includes('`')===false&&h.text.includes('&lt;2mm &copy;')));
});

test('real fences hide code headings while inline triple spans, long/mismatched closers and indentation follow native behavior',async()=>{
 const source=[
  '## Start',
  '  ``` inline circuit drawing ```',
  '### After inline',
  '```js',
  '## Hidden backtick',
  '~~~',
  '## Still hidden wrong closer',
  '````` trailing text is not a closer',
  '## Still hidden invalid closer',
  '````',
  '### After backtick',
  '~~~~ language',
  '## Hidden tilde',
  '~~~',
  '## Still hidden short closer',
  '~~~~~   ',
  '#### After tilde',
  '',
  '    ``` four-space indented code',
  '    ## Hidden indented code',
  '    ```',
  '',
  '##### After indented code',
 ].join('\n');
 const expected=await nativeIds(source);assert.deepEqual(extractAllHeadingIds(source),expected);
 assert.equal(expected.length,5);assert.ok(expected.includes('start-after-backtick-after-tilde-after-indented-code'));
 assert.ok(!expected.some(id=>id.includes('hidden')));
 assert.ok(!extractAllHeadingIds(source).includes('missing-target'),'genuinely missing IDs remain rejected');
});

test('all archived circuit and entity-bearing heading IDs match actual production-rendered baseline IDs',async()=>{
 const baseline=JSON.parse(await readFile(join(root,'circuit/tests/heading-built-baseline.json'),'utf8'));
 for(const[path,expected]of Object.entries(baseline)){
  const source=await readFile(join(root,'doc/src/content/docs',path),'utf8');
  assert.deepEqual(extractAllHeadingIds(source),expected,path);
 }
 const fromRoot=await realpath(createRequire(join(root,'package.json')).resolve('@takazudo/zudo-doc/extract-headings'));
 assert.equal(await realpath(requireDoc.resolve('@takazudo/zudo-doc/extract-headings')),fromRoot);
 assert.match(fromRoot,/patch_hash=/u);
});

test('strict scaffold caller accepts native deep/entity/inline-span anchors and still rejects code/missing targets',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'zudo-pd-heading-links-'));
 const body='## Parent\n  ``` inline drawing ```\n### Child &gt;1000ms\n##### Deep\n\n```js\n## Hidden code\n```\n';
 try {
  await mkdir(join(dir,'src/content/docs'),{recursive:true});
  await writeFile(join(dir,'zfb.config.ts'),await readFile(join(root,'doc/zfb.config.ts'),'utf8'));
  await writeFile(join(dir,'src/content/docs/ref.md'),'---\ntitle: Reference\n---\n'+body);
  const valid=(await nativeIds(body)).at(-1);
  const entry=join(dir,'src/content/docs/index.md');
  await writeFile(entry,`---\ntitle: Links\n---\n[Valid](./ref.md#${valid})\n`);
  const run=()=>spawnSync(process.execPath,[join(root,'doc/scripts/check-links.js'),'--strict-anchors','--strict-broken'],{cwd:dir,encoding:'utf8',timeout:10000});
  const pass=run();assert.equal(pass.status,0,pass.stdout+pass.stderr);
  await writeFile(entry,`---\ntitle: Links\n---\n[Hidden](./ref.md#hidden-code)\n[Missing](./ref.md#never-existed)\n`);
  const fail=run();assert.equal(fail.status,1,fail.stdout+fail.stderr);assert.match(fail.stdout,/hidden-code/u);assert.match(fail.stdout,/never-existed/u);assert.match(fail.stdout,/STRICT FAIL: 2 invalid anchors/u);
 } finally {await rm(dir,{recursive:true,force:true});}
});
