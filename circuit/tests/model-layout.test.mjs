import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join, basename } from 'node:path';
import { build } from 'esbuild';
import { createComponentReferencesDescriptor, encodeComponentReferencesDescriptor, decodeComponentReferencesDescriptor } from '@takazudo/zudo-circuit-doc';
import { root, packageRoot, corpus } from './compatibility-helpers.mjs';
const {model}=await corpus(root);
const ssr=await build({stdin:{contents:`export {ComponentReferences} from ${JSON.stringify(join(packageRoot,'lib/ui/component-references.js'))}; export {h} from "preact"; export {default as render} from "preact-render-to-string";`,resolveDir:root,loader:'js'},bundle:true,write:false,platform:'node',format:'esm',alias:{'react/jsx-runtime':'preact/jsx-runtime',react:'preact/compat'}});
const {ComponentReferences,h,render}=await import(`data:text/javascript;base64,${Buffer.from(ssr.outputFiles[0].text).toString('base64')}`);

test('actual long rectifier package identity survives descriptors, SSR caption and enlargement labels in full',()=>{
 const part=model.records.find(r=>r.identity.slug==='c3024223');assert.ok(part);
 const packageInfo=part.reference.footprint,label=String(packageInfo.packageId);
 assert.equal(label,'SMA_Diodes_SDT5A60SA_C3024223');
 const descriptor=createComponentReferencesDescriptor({document:null,footprintName:String(packageInfo.footprintName),model:{version:1,packageId:label,packageLabel:label,modelUrl:`/assets/component-previews/models/${basename(String(packageInfo.modelPath))}`,offset:packageInfo.offset,rotation:packageInfo.rotation,scale:packageInfo.scale}});
 const encoded=encodeComponentReferencesDescriptor(descriptor);assert.deepEqual(decodeComponentReferencesDescriptor(encoded),descriptor);
 const html=render(h(ComponentReferences,{descriptor:encoded}));
 assert.ok(html.includes(`Shared footprint package:</strong> ${label}`),'SSR caption keeps the complete copyable identity');
 assert.ok(html.includes(`Enlarge 3D preview for ${label}`),'enlargement control keeps full accessible identity');
 assert.ok(html.includes(`Interactive 3D view of shared footprint package ${label}`),'viewer accessible identity remains full');
 assert.ok(html.includes('/assets/component-previews/models/'));
});

test('package viewer CSS constrains intrinsic grid sizing and wraps complete captions without truncation',async()=>{
 const css=await readFile(join(packageRoot,'styles.css'),'utf8');
 const rule=selector=>css.match(new RegExp('^'+selector.replaceAll('.','\\.')+'\\s*\\{([^}]*)\\}','mu'))?.[1]??'';
 const viewer=rule('.zcd-model-viewer'), caption=rule('.zcd-model-viewer__caption'), viewport=rule('.zcd-model-viewer__viewport');
 assert.match(viewer,/grid-template-columns:\s*minmax\(0,\s*1fr\)/u);assert.match(viewer,/min-width:\s*0/u);
 assert.match(css,/\.zcd-model-viewer > \*\s*\{[^}]*min-width:\s*0/u);
 assert.match(caption,/overflow-wrap:\s*anywhere/u);assert.match(viewport,/box-sizing:\s*border-box/u);assert.match(viewport,/min-width:\s*0/u);
 assert.doesNotMatch(caption,/text-overflow:\s*ellipsis|overflow:\s*hidden|line-clamp|display:\s*none/u);
});
