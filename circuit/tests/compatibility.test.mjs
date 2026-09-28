import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, rm, symlink } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { root, packageRoot, internal, json, scratch, dispose, cli, mutate, corpus } from './compatibility-helpers.mjs';
const inventoryPath = '.claude/skills/component-spec-audit/references/inventory.json';
const candidatesPath = '.claude/skills/component-spec-audit/references/candidates.json';
const baseline = await json(join(root, 'circuit/tests/compatibility-baseline.json'));
const {mapped, index, model} = await corpus(root);
const {PublicationPolicy} = await internal('core/publication.js');
const {fitLabel, placementSummary} = await internal('core/render/shared.js');
const {partitionBundles} = await internal('provider/v1/evidence.js');
const {encodeComponentReferencesDescriptor, decodeComponentReferencesDescriptor, createComponentReferencesDescriptor} = await internal('core/reference-descriptor.js');
const {scanTargets, assertNoLeaks, subtractPublishedElsewhere, harvestCanaries} = await internal('core/scan.js');
const {independentContentTargets, scanSiteTargets} = await internal('scan/artifacts.js');
const {build} = await import('esbuild');
const ssr = await build({stdin: {contents: `export {ComponentReferences} from ${JSON.stringify(join(packageRoot,'lib/ui/component-references.js'))}; export {h} from "preact"; export {default as render} from "preact-render-to-string";`, resolveDir: root, loader: 'js'}, bundle: true, write: false, platform: 'node', format: 'esm', alias: {'react/jsx-runtime': 'preact/jsx-runtime', react: 'preact/compat'}});
const {ComponentReferences, h, render} = await import(`data:text/javascript;base64,${Buffer.from(ssr.outputFiles[0].text).toString('base64')}`);

test('installed patched runtime preserves closed evidence identities, counts and canonical bytes', async () => {
  assert.equal((await json(join(packageRoot, 'package.json'))).version, '0.1.0');
  assert.deepEqual(model.corpus, baseline.corpus);
  for (const [label, entries, key] of [['records',index.records,'record'],['sources',index.records.flatMap(r=>r.sources),'source_id'],['facts',index.records.flatMap(r=>r.facts),'fact_id'],['coverage',index.records.flatMap(r=>r.coverage),'coverage_id'],['pins',index.records.flatMap(r=>r.pinMaps),'pin_map_id'],['integration',index.integrationRules,'rule_id']]) assert.deepEqual(entries.map(e=>label==='records'?e.record.record_id:e[key]).sort(), baseline.ids[label]);
  for (const [path, hash] of Object.entries(baseline.files)) assert.equal(createHash('sha256').update(await readFile(join(root,path))).digest('hex'),hash,path);
  assert.equal(model.packagePreviews.length,34);
  const inv=await json(join(root,inventoryPath));
  assert.equal(inv.lines.flatMap(l=>l.placements).filter(p=>!p.dnp).length,113);
  assert.equal(inv.lines.flatMap(l=>l.placements).filter(p=>p.dnp).length,8);
});

test('real installed CLI doctor/validate/generate/check/models/footprints pass and generation is idempotent', async () => {
  const dir=await scratch();
  try {
    for (const [command,args] of [['doctor',[]],['validate',[]],['generate',[]],['check',[]],['models',['--check']],['footprints',['check']]]) {
      const run=cli(dir,command,args); assert.equal(run.status,0,`${command}: ${run.stdout}\n${run.stderr}`);
    }
    const repeat=cli(dir,'generate'); assert.equal(repeat.status,0,repeat.stderr); assert.match(repeat.stdout,/0 written, 64 unchanged/);
    for(const path of ['doc/src/content/docs/components/catalog/index.mdx','doc/src/content/docs/components/integration/index.mdx']) {
      const before=await readFile(join(root,path),'utf8'), after=await readFile(join(dir,path),'utf8');
      for(const anchor of before.matchAll(/<EvidenceAnchor id="([^"]+)"/g)) assert.ok(after.includes(`id="${anchor[1]}"`),`${path}: lost ${anchor[1]}`);
    }
    const missingDocument=await readFile(join(dir,'doc/src/content/docs/components/records/c335982/index.mdx'),'utf8');
    assert.match(missingDocument,/LCSC/);
    for(const record of model.records) {
      const path=`doc/src/content/docs/components/records/${record.identity.slug}/index.mdx`;
      const before=await readFile(join(root,path),'utf8'), after=await readFile(join(dir,path),'utf8');
      for(const anchor of before.matchAll(/<EvidenceAnchor id="([^"]+)"/g)) assert.ok(after.includes(`id="${anchor[1]}"`),`${path}: lost ${anchor[1]}`);
      assert.ok(after.includes('id="component-references"'));
    } assert.match(missingDocument,/No manufacturer document exists/);
    assert.doesNotMatch(missingDocument,/Datasheet PDF|Specification PDF|\/docs\/claude-skills\//);
  } finally {await dispose(dir);}
});

test('canonical and legacy generator declarations; board/path checks; finite MPN exceptions; placement DNP parity', () => {
  const program = String.raw`
import copy, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from circuit_evidence.inventory.led_generator_v1 import LedGeneratorProvider
from circuit_evidence.inventory.common import validate_line_shape, validate_counts
from circuit_evidence.errors import ContractError
root=Path(sys.argv[2]); data=json.loads((root/"${inventoryPath}").read_text())
opts={"kind":"led-generator-v1","specs":[{"path":str(root/p)} for p in ["scripts/schgen/board_a_spec.py","scripts/schgen/board_b_spec.py","scripts/schgen/board_p_spec.py"]],"mpnFromValueLcsc":["C144397","C591344"]}
p=LedGeneratorProvider(opts); p.validate_inventory(data,{"projectRoot":str(root)})
def rejects(fn):
    try: fn()
    except ContractError: return
    raise AssertionError("mutation accepted")
legacy=copy.deepcopy(data); legacy["generator_specs"]=[x["spec"] for x in data["generator_specs"]]; p.validate_inventory(legacy,{"projectRoot":str(root)})
bad=copy.deepcopy(data);bad["generator_specs"][0]["board"]="false-board";rejects(lambda:p.validate_inventory(bad,{"projectRoot":str(root)}))
bad=copy.deepcopy(data);bad["generator_specs"][0]["spec"]="../escape.py";rejects(lambda:p.validate_inventory(bad,{"projectRoot":str(root)}))
bad=copy.deepcopy(data);bad["lines"][0]["placements"][0]["dnp"]=not bad["lines"][0]["placements"][0]["dnp"];rejects(lambda:p.validate_inventory(bad,{"projectRoot":str(root)}))
rejects(lambda:LedGeneratorProvider({**opts,"mpnFromValueLcsc":[]}).validate_inventory(data,{"projectRoot":str(root)}))
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    spec=Path(tmp)/"fixture.py"
    spec.write_text('PROJECT_NAME = "fixture"\nCOMPONENTS = {"J1": ("SYMBOL_C144397", "VALUE144397", "C144397", "lib:p", False, (0, 0)), "J2": ("SYMBOL_C591344", "VALUE591344", "C591344", "lib:p", False, (0, 0)), "J3": ("EXACT_C999", "DISPLAY_VALUE", "C999", "lib:p", False, (0, 0))}\nNETS = {}\n')
    fixture={**opts,"specs":[{"path":str(spec)}]}
    grouped=LedGeneratorProvider(fixture).generated()[0]
    assert grouped["C144397"]["mpn"]=="VALUE144397"
    assert grouped["C591344"]["mpn"]=="VALUE591344"
    assert grouped["C999"]["mpn"]=="EXACT"
    assert LedGeneratorProvider({**fixture,"mpnFromValueLcsc":[]}).generated()[0]["C591344"]["mpn"]=="SYMBOL"
bad=copy.deepcopy(data);bad["lines"][0]["mpn"]="identity-corrupted";rejects(lambda:p.validate_inventory(bad,{"projectRoot":str(root)}))
line=copy.deepcopy(data["lines"][0]);line["placements"]=[{"board":"b","refdes":"R1","dnp":False},{"board":"b","refdes":"R2","dnp":True}];validate_line_shape(line)
validate_counts({"lines":[line],"assertions":{"orderable_lines":1,"fitted_lines":1,"dnp_or_hand_fit_lines":1}})
legacyline=copy.deepcopy(line);legacyline["dnp"]=False;legacyline["placements"]=[{"board":"b","refdes":"R1"}];validate_line_shape(legacyline)
bad=copy.deepcopy(line);bad["placements"][0]["dnp"]="false";rejects(lambda:validate_line_shape(bad))
`;
  const result=spawnSync('python3',['-c',program,join(packageRoot,'python'),root],{encoding:'utf8'}); assert.equal(result.status,0,result.stderr);
  const mixed=[{board:'b',refdes:'R1',dnp:false},{board:'b',refdes:'R2',dnp:true}];
  assert.match(fitLabel(false,mixed),/Mixed/); assert.match(placementSummary(mixed),/R1 \(fitted\).*R2 \(DNP or hand-fit\)/);
});

test('mixed placement DNP survives actual public projection', async () => {
  const {projectIndex}=await internal('provider/v1/index.js');
  const changed=structuredClone(index);const entry=changed.records.find(e=>e.line.placements.length>1);
  entry.line.placements[0].dnp=true;entry.line.placements[1].dnp=false;
  const projected=projectIndex(changed,new PublicationPolicy(mapped.matrix,mapped.selection));const record=projected.records.find(r=>r.identity.recordId===entry.record.record_id);
  assert.equal(record.identity.dnp,false);assert.equal(record.identity.placements[0].dnp,true);assert.equal(record.identity.placements[1].dnp,false);assert.match(fitLabel(record.identity.dnp,record.identity.placements),/Mixed/);
});

test('all candidates retained for validation, never projected; unknown null line and cross-partition links fail', async () => {
  const candidates=await json(join(root,candidatesPath)); assert.equal(candidates.candidates.length,12);
  assert.ok(model.records.every(r=>r.identity.lineId));
  const bundle={skill:'owner',records:[{record_id:'rec-a',line_id:'line-a',candidate_id:null,mpn:'a',manufacturer:'v',lcsc:'C1',package:'p'},{record_id:'rec-c',line_id:null,candidate_id:'cand-c',mpn:'c',manufacturer:'v',lcsc:'C2',package:'p'}],facts:[{fact_id:'f-a',record_id:'rec-a',depends_on:[]},{fact_id:'f-c',record_id:'rec-c',depends_on:[]}],sources:[],coverage:[],routes:[],pinMaps:[],interactions:[]};
  const lines=[{line_id:'line-a',owner_skill:'owner',mpn:'a',manufacturer:'v',lcsc:'C1',package:'p'}], cands=[{candidate_id:'cand-c',owner_skill:'owner',mpn:'c',manufacturer:'v',lcsc:'C2',package:'p'}];
  assert.equal(partitionBundles([bundle],lines,cands)[0].records.length,1);
  assert.throws(()=>partitionBundles([bundle],lines,[]),/unregistered/);
  const cross=structuredClone(bundle);cross.facts[0].depends_on=['f-c'];assert.throws(()=>partitionBundles([cross],lines,cands),/cross-partition/);
  const interaction=structuredClone(bundle);interaction.interactions=[{interaction_id:'i',record_ids:['rec-a','rec-c']}];assert.throws(()=>partitionBundles([interaction],lines,cands),/cross-partition/);
  const duplicate=structuredClone(bundle);duplicate.facts.push(duplicate.facts[0]);assert.throws(()=>partitionBundles([duplicate],lines,cands),/duplicate/);
  const orphan=structuredClone(bundle);orphan.sources=[{source_id:'s-orphan',record_id:'unregistered'}];assert.throws(()=>partitionBundles([orphan],lines,cands),/orphan/);
  const coverage=structuredClone(bundle);coverage.coverage=[{coverage_id:'cov',record_id:'rec-a',fact_ids:['f-c'],blocking_fact_ids:[]}];assert.throws(()=>partitionBundles([coverage],lines,cands),/cross-partition/);
});

test('candidate ownership, placement exclusion, candidate-only source/fact/pin validation fail closed', async () => {
  const mutations=[
    [candidatesPath,d=>{d.candidates[0].owner_skill='component-wrong-owner';}],
    [candidatesPath,d=>{d.candidates[0].lcsc='C144397';}],
    [candidatesPath,d=>{d.candidates.push(d.candidates[0]);}],
    ['.claude/skills/component-ptc-smd1210p200tf-c20808/sources.json',d=>{d.sources[0].availability='INVENTED';}],
    ['.claude/skills/component-ptc-smd1210p200tf-c20808/facts.json',d=>{d.facts[0].source_id='src-absent';}],
    ['.claude/skills/component-ptc-smd1210p200tf-c20808/pin-map.json',d=>{d.pin_maps[0].record_id='rec-absent';}],
  ];
  for(const [path,mutation] of mutations){const dir=await scratch();try{await mutate(dir,path,mutation);const run=cli(dir,'validate');assert.notEqual(run.status,0,`${path}: ${run.stdout}`);}finally{await dispose(dir);}}
});

test('document selection and exceptions partition every record without inventing a PDF', async () => {
  assert.deepEqual(await json(join(root,'circuit/publication/document-verification.json')),baseline.documentVerification);
  assert.equal(mapped.selection.documentSelections.length,59);assert.equal(mapped.selection.documentExceptions.length,1);
  const record=model.records.find(r=>r.identity.recordId==='rec-c335982'); assert.equal(record.reference.document,null); assert.ok(record.reference.footprint.modelPath);assert.ok(record.sources.some(s=>s.authorityClass==='DISTRIBUTOR_IDENTITY'));
  for(const exceptions of [[],[{recordId:mapped.selection.documentSelections[0].recordId,reason:'overlap'}],[...mapped.selection.documentExceptions,...mapped.selection.documentExceptions],[{recordId:'absent',reason:'missing'}],[{recordId:'rec-c335982',reason:''}]])assert.throws(()=>new PublicationPolicy(mapped.matrix,{...mapped.selection,documentExceptions:exceptions}));
});

test('11 denied fields remain denied, owner identity and package membership are null and harvested', async () => {
  assert.deepEqual(mapped.matrix,baseline.matrix);assert.equal(Object.keys(mapped.matrix).length,99);assert.equal(Object.values(mapped.matrix).filter(v=>v==='DENY').length,11);
  assert.ok(model.records.every(r=>r.identity.ownerSkill===null));assert.ok(model.integration.every(r=>r.ownerSkill===null));assert.ok(model.packagePreviews.every(p=>p.recordIds===null));
  const {readCanaries}=await internal('provider/v1/canaries.js');const canaries=await readCanaries(mapped.paths,mapped.matrix);assert.ok(canaries.some(c=>c.normalized.includes('component-project-passives')));
});

test('SSR and descriptor schema resolve all three cards independently', () => {
  const document={label:'Datasheet PDF',title:'Reviewed document',authority:'MANUFACTURER_PRIMARY',availability:'AVAILABLE',url:'https://example.com/reviewed.pdf'};
  for(const doc of [document,null])for(const footprintName of ['TEST',null])for(const modelValue of [null,{version:1,packageId:'TEST',packageLabel:'TEST',modelUrl:'/assets/component-previews/models/TEST.wrl',offset:{x:0,y:0,z:0},rotation:{x:0,y:0,z:0},scale:{x:1,y:1,z:1}}]){
    const descriptor=createComponentReferencesDescriptor({document:doc,footprintName,model:modelValue});const encoded=encodeComponentReferencesDescriptor(descriptor);assert.deepEqual(decodeComponentReferencesDescriptor(encoded),descriptor);
    const html=render(h(ComponentReferences,{descriptor:encoded}));assert.equal(html.includes('Datasheet PDF'),doc!==null);assert.equal(html.includes('Footprint preview unavailable.'),footprintName===null);assert.equal(html.includes('Package model unavailable.'),modelValue===null);
  }
  assert.throws(()=>decodeComponentReferencesDescriptor(encodeComponentReferencesDescriptor({version:1,document:{...document,label:'LCSC Datasheet PDF'},footprint:null,modelDescriptor:null})));
});

test('unavailable model is independent, while missing/corrupt/multiple declared models fail', async () => {
  const first=model.packagePreviews[0];const dir=await scratch();const file=join(dir,first.footprintPath);const original=await readFile(file,'utf8');
  try{
    const remove=original.replace(/\(model\s+"[^"]+"\s*\(offset\s+\(xyz[^)]+\)\s*\)\s*\(scale\s+\(xyz[^)]+\)\s*\)\s*\(rotate\s+\(xyz[^)]+\)\s*\)\s*\)/u,'');
    assert.notEqual(remove,original);await writeFile(file,remove);const result=await corpus(dir);const descriptor=result.model.packagePreviews.find(p=>p.packageId===first.packageId);assert.equal(descriptor.modelPath,null);
    // Model declarations do not alter footprint SVG geometry. Keep the scratch
    // master/library pair and reviewed canonical-input proof synchronized.
    await writeFile(join(dir,'footprints/kicad',first.footprintName+'.kicad_mod'),remove);
    const manifestPath=join(dir,'doc/public/assets/component-previews/footprints/manifest.json');const manifest=await json(manifestPath);
    const {aggregateHash,sha256}=await internal('footprint-previews/hash.js');
    manifest.packages.find(p=>p.packageId===first.packageId).canonicalInputSha256=sha256(remove);
    manifest.canonicalInputSha256=aggregateHash(manifest.packages.map(p=>({path:p.footprintPath,sha256:p.canonicalInputSha256})));
    await writeFile(manifestPath,JSON.stringify(manifest,null,2)+'\n');
    const stale=cli(dir,'models',['--check']);assert.notEqual(stale.status,0);await rm(join(dir,'doc/public/assets/component-previews/models',first.modelPath.split('/').at(-1)));
    for(const [command,args] of [['generate',[]],['models',[]],['models',['--check']],['check',[]]]){const run=cli(dir,command,args);assert.equal(run.status,0,`${command}: ${run.stdout}\n${run.stderr}`);}
    const page=await readFile(join(dir,'doc/src/content/docs/components/records/c74561/index.mdx'),'utf8');assert.ok(page.includes('ComponentReferences'));

    await writeFile(file,original);await rm(join(dir,first.modelPath));await assert.rejects(()=>corpus(dir),/missing/);
    await writeFile(join(dir,first.modelPath),'#VRML V2.0 utf8\nScript {}');await assert.rejects(()=>corpus(dir),/executable/);
    await writeFile(file,original+'\n(model "another.wrl")');await assert.rejects(()=>corpus(dir),/exactly one/);
  }finally{await dispose(dir);}
});

test('generated content cannot subtract canaries; planted MDX/search/dist/public leaks remain detected', async () => {
  const dir=await scratch();try{
    const value='private-compatibility-canary-forbidden';const canaries=harvestCanaries([{evidence_extract:value}],{deniedKeys:['evidence_extract']});assert.equal(canaries.length,1);
    await writeFile(join(dir,'doc/src/content/docs/components/planted.mdx'),value);
    const content=await independentContentTargets(join(dir,'doc'),join(dir,'doc/src/content/docs/components'));
    assert.ok(!content.some(t=>t.label.includes('components/')));const siteCanaries=subtractPublishedElsewhere(canaries,content);assert.equal(siteCanaries.length,1);
    for(const label of ['content/generated/planted.mdx','dist/search-index.json','dist/docs/other/index.html','public/extra.txt']){
      const result=await scanSiteTargets([{label,text:value}],siteCanaries,mapped.paths,model);assert.throws(()=>assertNoLeaks(result,{canaries:1,files:1}),/denied value/);
    }
  }finally{await dispose(dir);}
});

test('only recomputed reviewed manifest canonical hashes are excused in SITE, never OWNED or another public file', async () => {
  const text=await readFile(join(root,'doc/public/assets/component-previews/footprints/manifest.json'),'utf8');const data=JSON.parse(text);const hash=data.packages[0].canonicalInputSha256;
  const canaries=harvestCanaries([{sha256:hash}],{deniedKeys:['sha256']});assert.equal(canaries.length,1);
  const target={label:'public/assets/component-previews/footprints/manifest.json',text};
  const {readCanaries}=await internal('provider/v1/canaries.js');const realCanaries=await readCanaries(mapped.paths,mapped.matrix);assert.ok(scanTargets([target],realCanaries).hits.some(hit=>hit.canary.normalized==='d3facaa3fcd5c2b5d0f281d8729b87e49164d4551ada86466d0afaa1b70dad9c'));assert.equal((await scanSiteTargets([target],realCanaries,mapped.paths,model)).hits.length,0);
  assert.equal((await scanSiteTargets([target],canaries,mapped.paths,model)).hits.length,0);assert.equal(scanTargets([target],canaries).hits.length,1);
  assert.equal((await scanSiteTargets([target,{label:'public/extra.txt',text:hash}],canaries,mapped.paths,model)).hits.length,1);
  for(const apply of [d=>{d.packages[0].canonicalInputSha256='0'.repeat(64);},d=>{d.packages[0].footprintPath='../unproved.kicad_mod';},d=>{d.packages[0].packageId='unreviewed';},d=>{d.packages=[];}]){const changed=structuredClone(data);apply(changed);await assert.rejects(()=>scanSiteTargets([{...target,text:JSON.stringify(changed)}],canaries,mapped.paths,model));}
  const planted=structuredClone(data);planted.extra=hash;assert.equal((await scanSiteTargets([{...target,text:JSON.stringify(planted)}],canaries,mapped.paths,model)).hits.length,1);
});

test('canonical hash proof rejects symlinked source files', async () => {
 const dir=await scratch();try {
 const {mapped: scratchMapping, model: scratchModel}=await corpus(dir);const descriptor=scratchModel.packagePreviews[0];const path=join(dir,descriptor.footprintPath);await rm(path);await symlink(join(root,descriptor.footprintPath),path);
 const text=await readFile(join(dir,'doc/public/assets/component-previews/footprints/manifest.json'),'utf8');
 await assert.rejects(()=>scanSiteTargets([{label:'public/assets/component-previews/footprints/manifest.json',text}],[],scratchMapping.paths,scratchModel),/symlink|escapes/);
 } finally {await dispose(dir);}
});


test('declared candidate registry cannot disappear into an empty corpus', async () => {
  const dir=await scratch();try {await rm(join(dir,candidatesPath));const run=cli(dir,'doctor');assert.notEqual(run.status,0);assert.match(run.stdout+run.stderr,/candidates|declared/);}finally {await dispose(dir);}
});
