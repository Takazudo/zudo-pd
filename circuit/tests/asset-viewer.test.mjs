import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, mkdir, mkdtemp, writeFile, rm, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { root } from './compatibility-helpers.mjs';
const docDist=dirname(fileURLToPath(import.meta.resolve('@takazudo/zudo-doc/config')));
const {scanAssets}=await import(pathToFileURL(join(docDist,'plugins/internal/asset-viewer/scan.js')).href);
const {buildAssetSnapshot}=await import(pathToFileURL(join(docDist,'plugins/internal/asset-viewer/build.js')).href);
const host=await readFile(join(root,'doc/zfb.config.ts'),'utf8');
const exclusions=JSON.parse(host.match(/assetViewerExclude:\s*(\[[^\]]*\])/u)?.[1]??'[]');

test('host excludes package previews using asset-directory-relative paths without removing raw assets',async()=>{
 assert.match(host,/assetViewer:\s*true/u);
 assert.match(host,/assetViewerIndex:\s*false/u);
 assert.match(host,/assetViewerIndexing:\s*false/u);
 assert.deepEqual(exclusions,['component-previews/**']);
 const before=await scanAssets(join(root,'doc'),'assets');
 assert.ok(before.includes('component-previews/footprints/manifest.json'),'real leak path must exist before exclusion');
 assert.ok(before.some(p=>p.startsWith('component-previews/footprints/')&&p.endsWith('.svg')));
 assert.ok(before.some(p=>p.startsWith('component-previews/models/')&&p.endsWith('.wrl')));
 const after=await scanAssets(join(root,'doc'),'assets',exclusions);
 assert.deepEqual(after,before.filter(p=>!p.startsWith('component-previews/')));
 for(const path of before.filter(p=>p.startsWith('component-previews/')))assert.ok((await stat(join(root,'doc/public/assets',path))).isFile(),`raw package asset retained: ${path}`);
});

test('installed viewer snapshot cannot mirror package manifest or preview bytes into HTML, but still renders manual assets',async()=>{
 const fixture=await mkdtemp(join(tmpdir(),'zudo-pd-asset-viewer-'));
 const manifest='component-previews/footprints/manifest.json';
 const denied='fixture-denied-source-sha256-value';
 const contents={ [manifest]:JSON.stringify({sources:[{sha256:denied}]}), 'component-previews/footprints/part.svg':'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><path d="M0 0 L1 1"/></svg>', 'component-previews/models/part.wrl':'#VRML V2.0 utf8\nShape {}', 'manual/guide.txt':'Reviewed manual asset remains viewable.' };
 try {
  for(const[path,value]of Object.entries(contents)){const file=join(fixture,'public/assets',path);await mkdir(dirname(file),{recursive:true});await writeFile(file,value);}
  const options={projectRoot:fixture,dir:'assets',routePrefix:'files',contentRoots:[],base:'/',trailingSlash:true,logger:{warn(){}},highlightCode:async code=>`<pre><code>${code.replaceAll('&','&amp;').replaceAll('<','&lt;')}</code></pre>`};
  const unfiltered=await buildAssetSnapshot({...options,exclude:[]});
  assert.ok(unfiltered.records[manifest].html.includes(denied),'unexcluded text manifest reproduces the real HTML leak');
  const filtered=await buildAssetSnapshot({...options,exclude:exclusions});
  assert.deepEqual(Object.keys(filtered.records),['manual/guide.txt']);
  assert.ok(filtered.records['manual/guide.txt'].html.includes(contents['manual/guide.txt']));
  assert.ok(!JSON.stringify(filtered).includes(denied));
  assert.ok(filtered.watchFiles.every(path=>!path.includes('/component-previews/')));
  for(const[path,value]of Object.entries(contents))assert.equal(await readFile(join(fixture,'public/assets',path),'utf8'),value,'viewer exclusion never deletes package assets');
 } finally {await rm(fixture,{recursive:true,force:true});}
});
