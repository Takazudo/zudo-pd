import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';
import { build } from 'esbuild';
import { root, packageRoot } from './compatibility-helpers.mjs';
// Execute the installed island with controlled hooks and a plain dialog shell.
// No browser/DOM: the tested image/title/event logic is the package's actual code.
const result=await build({stdin:{contents:`export {FootprintPreviewIsland} from ${JSON.stringify(join(packageRoot,'lib/islands/footprint-preview-island.js'))}; export {initialize,beginRender} from "controlled-hooks"; export {default as render} from "preact-render-to-string";`,resolveDir:root,loader:'js'},bundle:true,write:false,platform:'node',format:'esm',plugins:[{
 name:'controlled-island-state',setup(builder){
  builder.onResolve({filter:/^(preact\/hooks|controlled-hooks)$/},()=>({path:'hooks',namespace:'controlled'}));
  builder.onResolve({filter:/preview-enlarge-dialog\.js$/},()=>({path:'dialog',namespace:'controlled'}));
  builder.onLoad({filter:/^hooks$/,namespace:'controlled'},()=>({loader:'js',contents:`let values=[],cursor=0; export function initialize(next){values=[...next];cursor=0;} export function beginRender(){cursor=0;} export function useRef(value){return {current:value};} export function useEffect(){} export function useState(initial){const slot=cursor++; if(values[slot]===undefined)values[slot]=initial; return [values[slot],next=>{values[slot]=typeof next==='function'?next(values[slot]):next;}];}`}));
  builder.onLoad({filter:/^dialog$/,namespace:'controlled'},()=>({loader:'js',resolveDir:root,contents:`import {h} from 'preact'; export function PreviewEnlargeDialog(props){return h('dialog',{'aria-label':props.title,'data-component-preview-dialog':props.variant},props.children);}`}));
 }
}]});
const {FootprintPreviewIsland,initialize,beginRender,render}=await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`);
const rawIsland=await readFile(join(packageRoot,'lib/islands/footprint-preview-island.js'),'utf8');
function find(node,predicate){if(Array.isArray(node)){for(const child of node){const found=find(child,predicate);if(found)return found;}}else if(node&&typeof node==='object'){if(predicate(node))return node;return find(node.props?.children,predicate);}return null;}

test('installed footprint enlargement keeps exact image alt and named media-only dialog after trigger and failure',()=>{
 assert.match(rawIsland,/^"use client";/u,'island keeps its client directive first');
 for(const footprintName of ['QFN-24_L4.0-W4.0-P0.50-BL-EP2.8','SMA_Diodes_SDT5A60SA_C3024223']){
  const assetUrl=`/assets/component-previews/footprints/${footprintName}.svg`,alt=`Footprint preview for ${footprintName}`;
  initialize([true,true,false,false]);let tree=FootprintPreviewIsland({assetUrl,footprintName});
  const inline=find(tree,node=>node.type==='img');assert.equal(inline.props.alt,alt);
  const trigger=find(tree,node=>node.type==='button'&&node.props['data-component-preview-enlarge']==='footprint');assert.ok(trigger);
  trigger.props.onClick({currentTarget:{}});beginRender();tree=FootprintPreviewIsland({assetUrl,footprintName});
  const dialog=find(tree,node=>node.props?.variant==='footprint');assert.equal(dialog.props.title,alt);assert.equal(dialog.props.isOpen,true);
  const enlarged=dialog.props.children;assert.equal(enlarged.type,'img');assert.equal(enlarged.props.src,assetUrl);assert.equal(enlarged.props.alt,alt,'enlarged media keeps exact footprint identity');
  const html=render(tree);assert.ok(html.includes(`aria-label="${alt}"`));assert.ok(html.includes(`src="${assetUrl}" alt="${alt}"`));
  assert.equal(find(dialog.props.children,node=>node.type==='a'),null,'enlarged media remains media-only');
  enlarged.props.onError();beginRender();tree=FootprintPreviewIsland({assetUrl,footprintName});
  const fallback=find(tree,node=>node.props?.role==='img');assert.ok(fallback);assert.equal(fallback.props['aria-label'],'Footprint preview could not be loaded');
  const failedDialog=find(tree,node=>node.props?.variant==='footprint');assert.equal(failedDialog.props.title,alt);assert.equal(find(failedDialog.props.children,node=>node.type==='img'),null);
 }
});
