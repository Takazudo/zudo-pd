import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';
import { build } from 'esbuild';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { root, packageRoot } from './compatibility-helpers.mjs';
// Execute the installed island and dialog markup with controlled hooks/modal effects.
// No browser/DOM: the tested image/title/event logic is the package's actual code.
const requireSdk=createRequire(import.meta.resolve('@takazudo/zudo-doc/config'));
const {parseFragment}=await import(pathToFileURL(requireSdk.resolve('parse5')).href);
const result=await build({stdin:{contents:`export {FootprintPreviewIsland} from ${JSON.stringify(join(packageRoot,'lib/islands/footprint-preview-island.js'))}; export {initialize,beginRender} from "controlled-hooks"; export {default as render} from "preact-render-to-string";`,resolveDir:root,loader:'js'},bundle:true,write:false,platform:'node',format:'esm',plugins:[{
 name:'controlled-island-state',setup(builder){
  builder.onResolve({filter:/^(preact\/hooks|controlled-hooks)$/},()=>({path:'hooks',namespace:'controlled'}));
  builder.onResolve({filter:/^@takazudo\/zudo-doc\/use-modal-dialog$/},()=>({path:'modal-effects',namespace:'controlled'}));
  builder.onLoad({filter:/^hooks$/,namespace:'controlled'},()=>({loader:'js',contents:`let values=[],cursor=0; export function initialize(next){values=[...next];cursor=0;} export function beginRender(){cursor=0;} export function useRef(value){return {current:value};} export function useEffect(){} export function useState(initial){const slot=cursor++; if(values[slot]===undefined)values[slot]=initial; return [values[slot],next=>{values[slot]=typeof next==='function'?next(values[slot]):next;}];}`}));
  builder.onLoad({filter:/^modal-effects$/,namespace:'controlled'},()=>({loader:'js',contents:`export function useModalDialog(){return {dialogRef:{current:null},handleBackdropClick(){}};}`}));
 }
}]});
const {FootprintPreviewIsland,initialize,beginRender,render}=await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`);
const rawIsland=await readFile(join(packageRoot,'lib/islands/footprint-preview-island.js'),'utf8');
function findMarkup(node,predicate){if(predicate(node))return node;for(const child of node.childNodes??[]){const found=findMarkup(child,predicate);if(found)return found;}return null;}
const attributes=node=>Object.fromEntries(node.attrs.map(a=>[a.name,a.value]));
function find(node,predicate){if(Array.isArray(node)){for(const child of node){const found=find(child,predicate);if(found)return found;}}else if(node&&typeof node==='object'){if(predicate(node))return node;return find(node.props?.children,predicate);}return null;}

test('installed footprint modal keeps exact inline identity with decorative enlarged media and error fallback',()=>{
 assert.match(rawIsland,/^"use client";/u,'island keeps its client directive first');
 for(const footprintName of ['QFN-24_L4.0-W4.0-P0.50-BL-EP2.8','SMA_Diodes_SDT5A60SA_C3024223']){
  const assetUrl=`/assets/component-previews/footprints/${footprintName}.svg`,alt=`Footprint preview for ${footprintName}`;
  initialize([true,true,false,false]);let tree=FootprintPreviewIsland({assetUrl,footprintName});
  const inline=find(tree,node=>node.type==='img');assert.equal(inline.props.alt,alt);
  const trigger=find(tree,node=>node.type==='button'&&node.props['data-component-preview-enlarge']==='footprint');assert.ok(trigger);
  trigger.props.onClick({currentTarget:{}});beginRender();tree=FootprintPreviewIsland({assetUrl,footprintName});
  const dialog=find(tree,node=>node.props?.variant==='footprint');assert.equal(dialog.props.title,alt);assert.equal(dialog.props.isOpen,true);
  const enlarged=dialog.props.children;assert.equal(enlarged.type,'img');assert.equal(enlarged.props.src,assetUrl);assert.equal(enlarged.props.alt,'','named media modal avoids duplicate image description');
  const markup=parseFragment(render(tree)),modal=findMarkup(markup,node=>node.nodeName==='dialog');assert.ok(modal);
  assert.equal(attributes(modal)['aria-label'],alt,'actual modal SSR retains exact accessible identity');assert.ok(!('aria-labelledby' in attributes(modal)),'actual dialog has no dangling removed-title reference');
  const media=findMarkup(modal,node=>node.nodeName==='img');assert.ok(media);assert.equal(attributes(media).src,assetUrl);assert.equal(attributes(media).alt,'','SSR includes an explicit decorative alt attribute');
  assert.equal(find(dialog.props.children,node=>node.type==='a'),null,'enlarged media remains media-only');
  enlarged.props.onError();beginRender();tree=FootprintPreviewIsland({assetUrl,footprintName});
  const fallback=find(tree,node=>node.props?.role==='img');assert.ok(fallback);assert.equal(fallback.props['aria-label'],'Footprint preview could not be loaded');
  const failedDialog=find(tree,node=>node.props?.variant==='footprint');assert.equal(failedDialog.props.title,alt);assert.equal(find(failedDialog.props.children,node=>node.type==='img'),null);
 }
});
