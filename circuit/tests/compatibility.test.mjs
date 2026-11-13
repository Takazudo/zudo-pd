import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, mkdtemp, rm, symlink, cp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { root, packageRoot, internal, json, scratch, dispose, cli, mutate, corpus } from './compatibility-helpers.mjs';
import { bundleForSsr } from './ssr-helper.mjs';
const inventoryPath = '.claude/skills/component-spec-audit/references/inventory.json';
const candidatesPath = '.claude/skills/component-spec-audit/references/candidates.json';
const ptcBundle = '.claude/skills/component-ptc-smd1210p200tf-c20808';
const canonicalFootprint = 'IDC-TH_16P-P2.54_321016RG0ABK00A01';
const canonicalDigest = 'd3facaa3fcd5c2b5d0f281d8729b87e49164d4551ada86466d0afaa1b70dad9c';
const manifestPublicPath = 'assets/component-previews/footprints/manifest.json';
const baseline = await json(join(root, 'circuit/tests/compatibility-baseline.json'));
const currentEvidence = await json(join(root, 'circuit/tests/current-evidence-baseline.json'));
baseline.corpus = currentEvidence.corpus;
baseline.ids = currentEvidence.ids;
Object.assign(baseline.files, currentEvidence.files);
for (const path of currentEvidence.retiredFiles.paths) {
  assert.ok(path in baseline.files, `retired ${path} is not a historical baseline file`);
  delete baseline.files[path];
}
const {mapped, index, model} = await corpus(root);
const {PublicationPolicy} = await internal('core/publication.js');
const {fitLabel, fitRollupLabel, hasMixedFit, placementSummary, buildRecordIndex} = await internal('core/render/shared.js');
const {renderRecord} = await internal('core/render/record.js');
const {renderCatalog} = await internal('core/render/catalog.js');
const {encodeComponentReferencesDescriptor, decodeComponentReferencesDescriptor, createComponentReferencesDescriptor, MODEL_UNAVAILABLE_TEXT, DOCUMENT_UNAVAILABLE_LABEL} = await internal('core/reference-descriptor.js');
const {scanTargets, assertNoLeaks, subtractPublishedElsewhere, harvestCanaries, readScanTargets} = await internal('core/scan.js');
const {authoredContentTargets} = await internal('scan/artifacts.js');
const {derivePublicCanonicalHashes, subtractPublicCanonicalHashes} = await internal('scan/public-canonical.js');
const {checkRecordPage} = await internal('scan/built-references.js');
const {readCanaries} = await internal('provider/v1/canaries.js');
const {ComponentReferences, h, render} = await bundleForSsr('ui/component-references.js', ['ComponentReferences']);
const canaryOptions = {matrix: mapped.matrix, integrationOwnerSkill: mapped.integrationOwnerSkill};

function referenceDescriptorOn(contents) {
  const tags = [...contents.matchAll(/<ComponentReferences descriptor="([0-9a-f]+)"\s*\/>/gu)];
  assert.equal(tags.length, 1);
  return tags[0][1];
}

/** A dist root holding only the published footprint manifest, as zfb copies it from public/. */
async function distWithManifest(text) {
  const dist = await mkdtemp(join(tmpdir(), 'zudo-pd-compatibility-dist-'));
  await mkdir(dirname(join(dist, manifestPublicPath)), {recursive: true});
  await writeFile(join(dist, manifestPublicPath), text ?? await readFile(join(root, 'doc/public', manifestPublicPath)));
  return dist;
}

test('installed runtime preserves closed evidence identities, counts and canonical bytes', async () => {
  assert.equal((await json(join(packageRoot, 'package.json'))).version, '0.3.0');
  assert.deepEqual(model.corpus, baseline.corpus);
  for (const [label, entries, key] of [['records',index.records,'record'],['sources',index.records.flatMap(r=>r.sources),'source_id'],['facts',index.records.flatMap(r=>r.facts),'fact_id'],['coverage',index.records.flatMap(r=>r.coverage),'coverage_id'],['pins',index.records.flatMap(r=>r.pinMaps),'pin_map_id'],['integration',index.integrationRules,'rule_id']]) assert.deepEqual(entries.map(e=>label==='records'?e.record.record_id:e[key]).sort(), baseline.ids[label]);
  for (const [path, hash] of Object.entries(baseline.files)) assert.equal(createHash('sha256').update(await readFile(join(root,path))).digest('hex'),hash,path);
  for (const path of currentEvidence.retiredFiles.paths) assert.equal(existsSync(join(root,path)),false,`retired ${path} reappeared`);
  assert.equal(model.packagePreviews.length,48);
  const inv=await json(join(root,inventoryPath));
  assert.equal(inv.lines.flatMap(l=>l.placements).filter(p=>!p.dnp).length,435);
  assert.equal(inv.lines.flatMap(l=>l.placements).filter(p=>p.dnp).length,12);
});

test('real installed CLI doctor/validate/generate/check/models/footprints pass and generation is idempotent', async () => {
  const dir=await scratch();
  try {
    for (const [command,args] of [['doctor',[]],['validate',[]],['generate',[]],['check',[]],['models',['--check']],['footprints',['check']]]) {
      const run=cli(dir,command,args); assert.equal(run.status,0,`${command}: ${run.stdout}\n${run.stderr}`);
    }
    const repeat=cli(dir,'generate'); assert.equal(repeat.status,0,repeat.stderr); assert.match(repeat.stdout,/0 written, 134 unchanged/);
    for(const path of ['doc/src/content/docs/components/catalog/index.mdx','doc/src/content/docs/components/integration/index.mdx']) {
      const before=await readFile(join(root,path),'utf8'), after=await readFile(join(dir,path),'utf8');
      for(const anchor of before.matchAll(/<EvidenceAnchor id="([^"]+)"/g)) assert.ok(after.includes(`id="${anchor[1]}"`),`${path}: lost ${anchor[1]}`);
    }
    for(const record of model.records) {
      const path=`doc/src/content/docs/components/records/${record.identity.slug}/index.mdx`;
      const before=await readFile(join(root,path),'utf8'), after=await readFile(join(dir,path),'utf8');
      for(const anchor of before.matchAll(/<EvidenceAnchor id="([^"]+)"/g)) assert.ok(after.includes(`id="${anchor[1]}"`),`${path}: lost ${anchor[1]}`);
      assert.ok(after.includes('id="component-references-heading"'),`${path}: lost the Component references heading anchor`);
      assert.equal([...after.matchAll(/<ComponentReferences descriptor=/g)].length,1,path);
    }
    const missingDocument=await readFile(join(dir,'doc/src/content/docs/components/records/c335982/index.mdx'),'utf8');
    assert.match(missingDocument,/LCSC/);
    assert.match(missingDocument,/\*\*Selected document:\*\* Document unavailable/);
    assert.match(missingDocument,/No manufacturer document exists/);
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
boards=[("board-a","scripts/schgen/board_a_spec.py"),("board-b","scripts/schgen/board_b_spec.py"),("board-p","scripts/schgen/board_p_spec.py"),("board-p15","scripts/schgen/board_p15_spec.py"),("board-b20-draft","scripts/schgen/board_b20_components.py")]
opts={"kind":"led-generator-v1","fit":"placement","specs":[{"path":str(root/p),"board":b} for b,p in boards],"mpnFromValueLcsc":["C144397"]}
cfg={"projectRoot":str(root)}
p=LedGeneratorProvider(opts); p.validate_inventory(data,cfg)
assert data["generator_specs"]==[{"board":b,"spec":s} for b,s in boards]
def rejects(fn):
    try: fn()
    except ContractError: return
    raise AssertionError("mutation accepted")
def fails(fn):
    try: fn()
    except Exception: return
    raise AssertionError("mutation accepted")
# The removed C591344 exception is inert for every current generator input, and the runtime refuses it.
rejects(lambda:LedGeneratorProvider({**opts,"mpnFromValueLcsc":["C144397","C591344"]}).validate_inventory(data,cfg))
rejects(lambda:LedGeneratorProvider({**opts,"mpnFromValueLcsc":[]}).validate_inventory(data,cfg))
# Line-level fit cannot read this per-placement inventory; 0.3.0 fails closed (an uncaught KeyError, not a ContractError).
fails(lambda:LedGeneratorProvider({**opts,"fit":"line"}).validate_inventory(data,cfg))
legacy=copy.deepcopy(data); legacy["generator_specs"]=[x["spec"] for x in data["generator_specs"]]; p.validate_inventory(legacy,cfg)
bad=copy.deepcopy(data);bad["generator_specs"][0]["board"]="false-board";rejects(lambda:p.validate_inventory(bad,cfg))
bad=copy.deepcopy(data);bad["generator_specs"][0]["spec"]="../escape.py";rejects(lambda:p.validate_inventory(bad,cfg))
bad=copy.deepcopy(data);bad["generator_specs"]=bad["generator_specs"][::-1];rejects(lambda:p.validate_inventory(bad,cfg))
bad=copy.deepcopy(data);bad["lines"][0]["placements"][0]["dnp"]=not bad["lines"][0]["placements"][0]["dnp"];rejects(lambda:p.validate_inventory(bad,cfg))
bad=copy.deepcopy(data["lines"][0]);del bad["placements"][0]["dnp"];rejects(lambda:validate_line_shape(bad,placement_fit=True))
bad=copy.deepcopy(data);bad["lines"][0]["mpn"]="identity-corrupted";rejects(lambda:p.validate_inventory(bad,cfg))
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    spec=Path(tmp)/"fixture.py"
    spec.write_text('PROJECT_NAME = "fixture"\nCOMPONENTS = {"J1": ("SYMBOL_C144397", "VALUE144397", "C144397", "lib:p", False, (0, 0)), "J2": ("SYMBOL_C591344", "VALUE591344", "C591344", "lib:p", False, (0, 0)), "J3": ("EXACT_C999", "DISPLAY_VALUE", "C999", "lib:p", False, (0, 0))}\nNETS = {}\n')
    fixture={**opts,"specs":[{"path":str(spec),"board":"fixture"}],"mpnFromValueLcsc":["C144397","C591344"]}
    grouped=LedGeneratorProvider(fixture).generated()[0]
    assert grouped["C144397"]["mpn"]=="VALUE144397"
    assert grouped["C591344"]["mpn"]=="VALUE591344"
    assert grouped["C999"]["mpn"]=="EXACT"
    assert LedGeneratorProvider({**fixture,"mpnFromValueLcsc":[]}).generated()[0]["C591344"]["mpn"]=="SYMBOL"
line=copy.deepcopy(data["lines"][0]);line["placements"]=[{"board":"b","refdes":"R1","dnp":False},{"board":"b","refdes":"R2","dnp":True}]
validate_line_shape(line,placement_fit=True)
validate_counts({"lines":[line],"assertions":{"orderable_lines":1,"fitted_lines":1,"dnp_or_hand_fit_lines":1,"fitted_placements":1,"dnp_placements":1}},placement_fit=True)
rejects(lambda:validate_counts({"lines":[line],"assertions":{"orderable_lines":1,"fitted_lines":1,"dnp_or_hand_fit_lines":0}},placement_fit=True))
legacyline=copy.deepcopy(line);legacyline["dnp"]=False;legacyline["placements"]=[{"board":"b","refdes":"R1"}];validate_line_shape(legacyline)
rejects(lambda:validate_line_shape(legacyline,placement_fit=True))
bad=copy.deepcopy(line);bad["placements"][0]["dnp"]="false";rejects(lambda:validate_line_shape(bad,placement_fit=True))
bad=copy.deepcopy(line);bad["dnp"]=False;rejects(lambda:validate_line_shape(bad,placement_fit=True))
`;
  const result=spawnSync('python3',['-c',program,join(packageRoot,'python'),root],{encoding:'utf8'}); assert.equal(result.status,0,result.stderr);
  const mixed=[{board:'b',refdes:'R1',dnp:false},{board:'b',refdes:'R2',dnp:true}];
  assert.equal(hasMixedFit({dnp:false,placements:mixed}),true);
  assert.match(String(fitRollupLabel({dnp:false,placements:mixed})),/Mixed: fitted and DNP or hand-fit by placement/);
  assert.equal(String(fitLabel(true)),'DNP or hand-fit');assert.equal(String(fitLabel(false)),'Fitted');
  assert.equal(String(placementSummary(mixed)),'b R1, R2');
});

test('mixed placement DNP survives actual public projection and rendered record/catalog pages', async () => {
  const {projectIndex}=await internal('provider/v1/index.js');
  assert.ok(model.records.every(r=>!hasMixedFit(r.identity)),'the reviewed corpus has no mixed line');
  const changed=structuredClone(index);const entry=changed.records.find(e=>e.line.placements.length>1);
  entry.line.placements[0].dnp=true;entry.line.placements[1].dnp=false;
  const projected=projectIndex(changed,new PublicationPolicy(mapped.matrix,mapped.selection));const record=projected.records.find(r=>r.identity.recordId===entry.record.record_id);
  assert.equal(record.identity.placements[0].dnp,true);assert.equal(record.identity.placements[1].dnp,false);
  assert.match(String(fitRollupLabel(record.identity)),/Mixed/);
  const page=renderRecord(record,buildRecordIndex(projected)).contents;
  assert.match(page,/Mixed: fitted and DNP or hand-fit by placement/);
  assert.match(page,/\|\s*Board\s*\|\s*Reference designator\s*\|\s*Fit\s*\|/);
  assert.match(page,new RegExp(`\\|\\s*\`${record.identity.placements[0].refdes}\`\\s*\\|\\s*DNP or hand-fit\\s*\\|`));
  const catalog=renderCatalog(projected).contents;
  assert.match(catalog,/DNP or hand-fit placements/);
  const unchanged=renderRecord(model.records.find(r=>r.identity.recordId===entry.record.record_id),buildRecordIndex(model)).contents;
  assert.doesNotMatch(unchanged,/\|\s*Board\s*\|\s*Reference designator\s*\|\s*Fit\s*\|/);
});

test('all candidates retained for validation, never projected; unknown and cross-partition links fail', async () => {
  const candidates=await json(join(root,candidatesPath)); assert.equal(candidates.candidates.length,16);
  assert.equal(index.candidates.length,16);
  const candidateRecords=new Set(index.candidates.map(e=>e.record.record_id));
  assert.ok(model.records.every(r=>r.identity.lineId&&!candidateRecords.has(r.identity.recordId)));
  const fitted='rec-ptc-smd1210p150tf16-c7529589', candidate='rec-ptc-smd1210p200tf-c20808';
  assert.ok(candidateRecords.has(candidate));assert.ok(model.records.some(r=>r.identity.recordId===fitted));
  const mutations=[
    [`${ptcBundle}/facts.json`,d=>{d.facts.find(f=>f.fact_id==='fact-ptc1b-ihold-margin').depends_on.push('fact-ptc1-ihold');},/fact dependency crosses fitted\/candidate partitions/],
    [`${ptcBundle}/coverage.json`,d=>{d.coverage.find(c=>c.coverage_id==='cov-ptc1b-electrical-limits').fact_ids.push('fact-ptc1-ihold');},/coverage fact crosses fitted\/candidate partitions|coverage/],
    [`${ptcBundle}/interactions.json`,d=>{d.interactions.find(i=>i.interaction_id==='int-ptc1-12v-rail-protection').record_ids.push(fitted);},/crosses fitted\/candidate partitions|interaction/],
    [candidatesPath,d=>{d.candidates=d.candidates.filter(c=>c.candidate_id!=='cand-ptc-smd1210p200tf-c20808');},/unknown inventory line or has no known candidate identity/],
    [`${ptcBundle}/facts.json`,d=>{d.facts.push(d.facts[0]);},/duplicate fact id/],
    [`${ptcBundle}/sources.json`,d=>{d.sources.push({...d.sources.find(s=>s.record_id===fitted),source_id:'src-orphan-compatibility'});},/not listed by the record that owns it/],
    ['.claude/skills/circuit-spec-integration/references/rules.json',d=>{d.rules[0].record_ids.push(candidate);},/integration rule names an audited candidate record or fact|candidate/],
  ];
  for(const [path,apply,expected] of mutations){const dir=await scratch();try{await mutate(dir,path,apply);await assert.rejects(()=>corpus(dir),expected,path);}finally{await dispose(dir);}}
});

test('candidate ownership, placement exclusion, candidate-only source/fact/pin validation fail closed', async () => {
  const mutations=[
    [candidatesPath,d=>{d.candidates[0].owner_skill='component-wrong-owner';}],
    [candidatesPath,d=>{d.candidates[0].lcsc='C144397';}],
    [candidatesPath,d=>{d.candidates.push(d.candidates[0]);}],
    [`${ptcBundle}/sources.json`,d=>{d.sources[0].availability='INVENTED';}],
    [`${ptcBundle}/facts.json`,d=>{d.facts[0].source_id='src-absent';}],
    [`${ptcBundle}/pin-map.json`,d=>{d.pin_maps[0].record_id='rec-absent';}],
  ];
  for(const [path,mutation] of mutations){const dir=await scratch();try{await mutate(dir,path,mutation);const run=cli(dir,'validate');assert.notEqual(run.status,0,`${path}: ${run.stdout}`);}finally{await dispose(dir);}}
});

test('document selection and exceptions partition every record without inventing a PDF', async () => {
  assert.deepEqual(await json(join(root,'circuit/publication/document-verification.json')),baseline.documentVerification);
  assert.equal(mapped.selection.documentSelections.length,129);assert.equal(mapped.selection.documentExceptions.length,1);
  const record=model.records.find(r=>r.identity.recordId==='rec-c335982'); assert.equal(record.reference.document,null);
  assert.match(String(record.reference.documentUnavailableReason),/No manufacturer document exists/);
  assert.ok(record.reference.footprint.modelPath);assert.ok(record.sources.some(s=>s.authorityClass==='DISTRIBUTOR_IDENTITY'));
  assert.equal(model.records.filter(r=>r.reference.document!==null).length,129);
  for(const exceptions of [[],[{recordId:mapped.selection.documentSelections[0].recordId,reason:'overlap'}],[...mapped.selection.documentExceptions,...mapped.selection.documentExceptions],[{recordId:'absent',reason:'missing'}],[{recordId:'rec-c335982',reason:''}]])assert.throws(()=>new PublicationPolicy(mapped.matrix,{...mapped.selection,documentExceptions:exceptions}));
});

test('11 denied fields remain denied, owner identity and package membership are null and harvested', async () => {
  assert.deepEqual(mapped.matrix,baseline.matrix);assert.equal(Object.keys(mapped.matrix).length,99);assert.equal(Object.values(mapped.matrix).filter(v=>v==='DENY').length,11);
  assert.ok(model.records.every(r=>r.identity.ownerSkill===null));assert.ok(model.integration.every(r=>r.ownerSkill===null));assert.ok(model.packagePreviews.every(p=>p.recordIds===null));
  const manifest=await json(join(root,'doc/public',manifestPublicPath));assert.ok(manifest.packages.every(p=>!('recordIds' in p)),'package membership stays out of the public manifest');
  const canaries=await readCanaries(mapped.paths,canaryOptions);
  assert.ok(canaries.some(c=>c.normalized.includes('component-project-passives')));
  assert.ok(canaries.some(c=>c.normalized==='circuit-spec-integration'),'the configured integration owner is harvested');
});

test('SSR and descriptor schema resolve all three cards independently', () => {
  const document={label:'Datasheet PDF',title:'Reviewed document',authority:'MANUFACTURER_PRIMARY',availability:'AVAILABLE',url:'https://example.com/reviewed.pdf'};
  const unavailable={label:DOCUMENT_UNAVAILABLE_LABEL,reason:'No manufacturer document exists for this fixture.'};
  const viewer={version:1,packageId:'TEST',packageLabel:'TEST',modelUrl:'/assets/component-previews/models/TEST.wrl',offset:{x:0,y:0,z:0},rotation:{x:0,y:0,z:0},scale:{x:1,y:1,z:1}};
  for(const doc of [document,unavailable])for(const modelValue of [null,viewer]){
    const descriptor=createComponentReferencesDescriptor({document:doc,footprintName:'TEST',model:modelValue});const encoded=encodeComponentReferencesDescriptor(descriptor);assert.deepEqual(decodeComponentReferencesDescriptor(encoded),descriptor);
    const html=render(h(ComponentReferences,{descriptor:encoded}));
    assert.equal(html.includes('Datasheet PDF'),doc===document);
    assert.equal(html.includes('https://example.com/reviewed.pdf'),doc===document);
    assert.equal(html.includes('data-document-unavailable'),doc===unavailable);
    assert.equal(html.includes(unavailable.reason),doc===unavailable);
    assert.ok(html.includes('/assets/component-previews/footprints/TEST.svg'));
    assert.equal(html.includes(MODEL_UNAVAILABLE_TEXT),modelValue===null);
    assert.equal(html.includes('data-model-url'),modelValue!==null);
  }
  assert.throws(()=>decodeComponentReferencesDescriptor(encodeComponentReferencesDescriptor({version:1,document:{...document,label:'LCSC Datasheet PDF'},footprint:{name:'TEST',assetUrl:'/assets/component-previews/footprints/TEST.svg'},modelDescriptor:null})));
  assert.throws(()=>encodeComponentReferencesDescriptor({version:1,document:null,footprint:{name:'TEST',assetUrl:'/assets/component-previews/footprints/TEST.svg'},modelDescriptor:null}));
  assert.throws(()=>encodeComponentReferencesDescriptor({version:1,document:{...unavailable,reason:''},footprint:{name:'TEST',assetUrl:'/assets/component-previews/footprints/TEST.svg'},modelDescriptor:null}));
});

test('document-unavailable record may link only its footprint and declared model; any other link still fails', () => {
  const record=model.records.find(r=>r.identity.recordId==='rec-c335982');
  const encoded=referenceDescriptorOn(renderRecord(record,buildRecordIndex(model)).contents);
  const section=render(h(ComponentReferences,{descriptor:encoded}));
  const page=links=>`<main>${section.replace('</section>',`${links}</section>`)}<h2 id="sources">Sources</h2><table class="zcd-evidence-table"></table></main>`;
  checkRecordPage(record.identity.slug,page(''),new Set(),new Set(),true,record);
  assert.match(section,/data-model-url="\/assets\/component-previews\/models\/[^"]+\.wrl"/);
  for(const href of ['https://example.com/datasheet.pdf','/assets/component-previews/models/OTHER.wrl','/docs/claude-skills/'])
    assert.throws(()=>checkRecordPage(record.identity.slug,page(`<a href="${href}">x</a>`),new Set(),new Set(),true,record),/must not link a document/,href);
  const linked=model.records.find(r=>r.reference.document!==null&&r.reference.footprint?.modelPath);
  const linkedSection=render(h(ComponentReferences,{descriptor:referenceDescriptorOn(renderRecord(linked,buildRecordIndex(model)).contents)}));
  assert.throws(()=>checkRecordPage(record.identity.slug,`<main>${linkedSection}<h2 id="sources">Sources</h2><table class="zcd-evidence-table"></table></main>`,new Set(),new Set(),true,record),/unavailable-document label|must not link/);
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
    const affected=result.model.records.filter(r=>r.reference.footprint?.packageId===first.packageId);assert.ok(affected.length>0);
    for(const record of affected){
      const page=await readFile(join(dir,`doc/src/content/docs/components/records/${record.identity.slug}/index.mdx`),'utf8');
      const references=decodeComponentReferencesDescriptor(referenceDescriptorOn(page));assert.equal(references.modelDescriptor,null);assert.equal(references.footprint.name,first.footprintName);
    }

    await writeFile(file,original);await rm(join(dir,first.modelPath));await assert.rejects(()=>corpus(dir),/missing/);
    await writeFile(join(dir,first.modelPath),'#VRML V2.0 utf8\nScript {}');await assert.rejects(()=>corpus(dir),/executable/);
    await writeFile(file,original+'\n(model "another.wrl")');await assert.rejects(()=>corpus(dir),/exactly one|multiple footprint roots/);
  }finally{await dispose(dir);}
});

test('generated content cannot subtract canaries; planted dist/search/agent leaks remain detected', async () => {
  const value='private-compatibility-canary-forbidden';const canaries=harvestCanaries([{evidence_extract:value}],{deniedKeys:['evidence_extract']});assert.equal(canaries.length,1);
  const contentRoot=join(root,'doc/src/content/docs'), roots={contentRoot,generatedRoot:mapped.paths.generatedRoot};
  assert.equal(mapped.paths.generatedRoot,join(contentRoot,'components'));
  const real=await readScanTargets(contentRoot,'content');assert.ok(real.some(t=>t.label.startsWith('content/components/')));
  const content=authoredContentTargets([...real,{label:'content/components/planted.mdx',text:value}],roots);
  assert.ok(content.length>0);assert.ok(!content.some(t=>t.label.startsWith('content/components/')));
  const siteCanaries=subtractPublishedElsewhere(canaries,content);assert.equal(siteCanaries.length,1);
  for(const label of ['dist/search-index.json','dist/docs/other/index.html','dist/assets/extra.txt','agent-skill/SKILL.md']){
    assert.throws(()=>assertNoLeaks(scanTargets([{label,text:value}],siteCanaries),{canaries:1,files:1}),/denied value/,label);
  }
  // An authored page that publishes the value withholds it from SITE; scan.expectedWithheld pins that count.
  const authored=authoredContentTargets([...real,{label:'content/planted-authored.mdx',text:value}],roots);
  assert.equal(subtractPublishedElsewhere(canaries,authored).length,0);
});

test('only the declared, dist-proved canonical footprint hash is excused in SITE, never OWNED or other evidence text', async () => {
  const realCanaries=await readCanaries(mapped.paths,canaryOptions);
  const manifestText=await readFile(join(root,'doc/public',manifestPublicPath),'utf8');const manifest=JSON.parse(manifestText);
  const target={label:`dist/${manifestPublicPath}`,text:manifestText};
  assert.ok(scanTargets([target],realCanaries).hits.some(hit=>hit.canary.normalized===canonicalDigest),'OWNED-tier canaries still match the canonical digest');
  const dist=await distWithManifest();try{
    const paths={...mapped.paths,distRoot:dist};
    const hashes=await derivePublicCanonicalHashes({declared:[canonicalFootprint],model,paths});
    assert.deepEqual(hashes.map(x=>x.sha256),[canonicalDigest]);
    const {kept,withheld}=subtractPublicCanonicalHashes(realCanaries,hashes);
    assert.equal(withheld.length,1);assert.ok(withheld.every(c=>c.path.endsWith('.sha256')&&c.normalized===canonicalDigest));
    assert.equal(scanTargets([target],kept).hits.length,0);
    assert.deepEqual(await derivePublicCanonicalHashes({declared:[],model,paths}),[]);
    const evidenceText=harvestCanaries([{evidence_extract:canonicalDigest}],{deniedKeys:['evidence_extract']});
    assert.equal(subtractPublicCanonicalHashes(evidenceText,hashes).kept.length,1,'equal evidence text remains a canary');
    const other=manifest.packages.find(p=>p.footprintName!==canonicalFootprint);
    const otherCanary=harvestCanaries([{sha256:other.canonicalInputSha256}],{deniedKeys:['sha256']});
    assert.equal(subtractPublicCanonicalHashes(otherCanary,hashes).kept.length,1,'an undeclared footprint hash stays a hit');
    for(const declared of [['unreviewed-footprint'],['../escape']])
      await assert.rejects(()=>derivePublicCanonicalHashes({declared,model,paths}),undefined,String(declared));
  }finally{await rm(dist,{recursive:true,force:true});}
  for(const apply of [d=>{d.packages.find(p=>p.footprintName===canonicalFootprint).canonicalInputSha256='0'.repeat(64);},d=>{d.packages.find(p=>p.footprintName===canonicalFootprint).footprintPath='../unproved.kicad_mod';},d=>{d.packages=[];},d=>{d.formatVersion=-1;}]){
    const changed=structuredClone(manifest);apply(changed);const dist=await distWithManifest(JSON.stringify(changed));
    try{await assert.rejects(()=>derivePublicCanonicalHashes({declared:[canonicalFootprint],model,paths:{...mapped.paths,distRoot:dist}}),/manifest/);}finally{await rm(dist,{recursive:true,force:true});}
  }
});

test('canonical hash proof rejects symlinked source files', async () => {
  const dir=await scratch();const dist=await distWithManifest();try {
    const {mapped: scratchMapping, model: scratchModel}=await corpus(dir);
    const path=join(scratchMapping.paths.footprintLibraryRoot,`${canonicalFootprint}.kicad_mod`);
    const original=join(mapped.paths.footprintLibraryRoot,`${canonicalFootprint}.kicad_mod`);
    const copy=join(dir,'symlink-target.kicad_mod');await cp(original,copy);await rm(path);await symlink(copy,path);
    await assert.rejects(()=>derivePublicCanonicalHashes({declared:[canonicalFootprint],model:scratchModel,paths:{...scratchMapping.paths,distRoot:dist}}),/symlink|escapes/);
  } finally {await dispose(dir);await rm(dist,{recursive:true,force:true});}
});

test('declared candidate registry cannot disappear into an empty corpus', async () => {
  const dir=await scratch();try {await rm(join(dir,candidatesPath));const run=cli(dir,'doctor');assert.notEqual(run.status,0);assert.match(run.stdout+run.stderr,/candidates|declared/);}finally {await dispose(dir);}
});
