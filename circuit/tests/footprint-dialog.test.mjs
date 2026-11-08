import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';
import { build } from 'esbuild';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { root, packageRoot } from './compatibility-helpers.mjs';
// Execute the installed zudo-react island with the published server renderer.
// No browser/DOM: setup runs once, the captured description keeps its live
// signals, and each state change is observed by rendering that same tree again.
// Focus, Escape/backdrop and real activation stay in the project browser smoke.
const requireSdk=createRequire(import.meta.resolve('@takazudo/zudo-doc/config'));
const {parseFragment}=await import(pathToFileURL(requireSdk.resolve('parse5')).href);
const result=await build({stdin:{contents:`export {FootprintPreviewIsland} from ${JSON.stringify(join(packageRoot,'lib/islands/footprint-preview-island.js'))}; export {h} from "@takazudo/zfb/zudo-react"; export {renderToString} from "@takazudo/zfb/zudo-react/server";`,resolveDir:root,loader:'js'},bundle:true,write:false,platform:'node',format:'esm',logLevel:'silent'});
const {FootprintPreviewIsland,h,renderToString}=await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`);
const rawIsland=await readFile(join(packageRoot,'lib/islands/footprint-preview-island.js'),'utf8');
function findMarkup(node,predicate){if(predicate(node))return node;for(const child of node.childNodes??[]){const found=findMarkup(child,predicate);if(found)return found;}return null;}
const attributes=node=>Object.fromEntries((node.attrs??[]).map(a=>[a.name,a.value]));
function find(node,predicate){if(Array.isArray(node)){for(const child of node){const found=find(child,predicate);if(found)return found;}return null;}if(node&&typeof node==='object'&&node.props){if(predicate(node))return node;return find(node.props.children,predicate);}return null;}
const typeName=node=>typeof node.type==='function'?node.type.name:node.type;

test('installed footprint modal keeps exact inline identity with decorative enlarged media and error fallback',()=>{
 assert.match(rawIsland,/^"use client";/u,'island keeps its client directive first');
 for(const footprintName of ['QFN-24_L4.0-W4.0-P0.50-BL-EP2.8','SMA_Diodes_SDT5A60SA_C3024223']){
  const assetUrl=`/assets/component-previews/footprints/${footprintName}.svg`,alt=`Footprint preview for ${footprintName}`;
  let tree;
  const closed=parseFragment(renderToString(h(props=>(tree=FootprintPreviewIsland(props)),{assetUrl,footprintName})));
  const render=()=>parseFragment(renderToString(h(()=>tree)));
  const inline=findMarkup(closed,node=>node.nodeName==='img');assert.equal(attributes(inline).alt,alt);assert.equal(attributes(inline).src,assetUrl);
  const closedModal=findMarkup(closed,node=>node.nodeName==='dialog');assert.ok(closedModal,'native dialog is server-rendered');
  assert.equal(attributes(closedModal)['aria-label'],alt,'actual modal SSR retains exact accessible identity');assert.ok(!('aria-labelledby' in attributes(closedModal)),'actual dialog has no dangling removed-title reference');
  assert.equal(findMarkup(closedModal,node=>node.nodeName==='img'),null,'closed dialog carries no enlarged media');
  const trigger=find(tree,node=>node.type==='button'&&node.props['data-component-preview-enlarge']==='footprint');assert.ok(trigger);
  assert.equal(trigger.props['aria-label'],`Enlarge footprint preview for ${footprintName}`);
  trigger.props['on:click']({currentTarget:{}});
  const open=render(),modal=findMarkup(open,node=>node.nodeName==='dialog');
  assert.equal(attributes(modal)['aria-label'],alt);
  const media=findMarkup(modal,node=>node.nodeName==='img');assert.ok(media,'opening renders the enlarged media');assert.equal(attributes(media).src,assetUrl);assert.equal(attributes(media).alt,'','named media modal avoids duplicate image description');
  assert.equal(findMarkup(modal,node=>node.nodeName==='a'),null,'enlarged media remains media-only');
  const outer=find(tree,node=>typeName(node)==='Show');assert.ok(outer);
  const inner=outer.props.children();assert.equal(typeName(inner),'Show');
  const enlarged=inner.props.fallback();assert.equal(enlarged.type,'img');enlarged.props['on:error']();
  const failed=render(),failedModal=findMarkup(failed,node=>node.nodeName==='dialog');
  assert.equal(attributes(failedModal)['aria-label'],alt,'failed media keeps the dialog identity');
  assert.equal(findMarkup(failedModal,node=>node.nodeName==='img'),null);
  const fallback=findMarkup(failedModal,node=>attributes(node).role==='img');assert.ok(fallback);assert.equal(attributes(fallback)['aria-label'],'Footprint preview could not be loaded');
  trigger.props['on:click']({currentTarget:{}});
  assert.ok(findMarkup(findMarkup(render(),node=>node.nodeName==='dialog'),node=>node.nodeName==='img'),'reopening clears the previous media failure');
 }
});
