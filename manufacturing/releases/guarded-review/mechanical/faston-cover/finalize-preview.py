#!/usr/bin/env python3
"""Bundle portable preview models and optionally rebind a silk-position-only PCB.

A rebound PCB must be structurally identical to the checked snapshot after
removing only board-silkscreen text positions and reference positions/visibility.
Copper, all other footprint fields, text content/style, model transforms and
all other nodes must remain identical.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
import sys
import zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def serialize(node):
 if isinstance(node,list):return '('+' '.join(serialize(v) for v in node)+')'
 return json.dumps(node[1]) if node[0]=='str' else node[1]
def presentation_removed(tree):
 tree=copy.deepcopy(tree)
 for text in find_all(tree,'gr_text'):
  layers=find_all(text,'layer')
  if layers and atom(layers[0][1]) in ['F.SilkS','B.SilkS']:
   for at in find_all(text,'at'):text.remove(at)
 for fp in find_all(tree,'footprint'):
  for prop in find_all(fp,'property'):
   if atom(prop[1])!='Reference':continue
   for at in find_all(prop,'at'):prop.remove(at)
   for node in [prop,*find_all(prop,'effects')]:
    node[:]=[v for v in node if v!=('atom','hide')]
    for hidden in find_all(node,'hide'):node.remove(hidden)
 return tree

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('pcb',type=Path);a.add_argument('--checked-pcb',type=Path)
 args=a.parse_args();pcb=args.pcb.resolve();out=HERE/'generated';preview=out/'preview';proof_path=out/'verification.json';manifest_path=out/'manifest.json'
 proof=json.loads(proof_path.read_text());manifest=json.loads(manifest_path.read_text());require(proof['status']=='PASS','Complete populated CAD verification first')
 tree=load(pcb)
 if proof['pcb_sha256']!=sha(pcb):
  require(args.checked_pcb is not None,'PCB changed; supply the exact previously checked snapshot')
  old=args.checked_pcb.resolve();require(sha(old)==proof['pcb_sha256'],'Snapshot is not the PCB checked by this report')
  old_tree=load(old);require(presentation_removed(old_tree)==presentation_removed(tree),'Change is not limited to approved silkscreen/reference presentation')
  proof['silkscreen_only_rebind']={'checked_pcb_sha256':proof['pcb_sha256'],'final_pcb_sha256':sha(pcb),'physical_nodes_identical':True,'allowed_difference':'Board F/B.SilkS gr_text at plus Reference at/visibility fields only','step_and_cad_preview_unchanged':'These exports contain no board silkscreen geometry.'}
  proof['pcb_sha256']=sha(pcb);proof['pcb']=str(pcb.relative_to(ROOT))
 require(proof['contract_sha256']==sha(HERE/'pcb-contract.json'),'Contract changed after CAD verification')
 for path,digest in proof['model_sources_sha256'].items():require(sha(ROOT/path)==digest,'Component STEP changed after verification: '+path)
 for name,digest in manifest['assembly_files'].items():require(sha(out/name)==digest,'Guard assembly asset changed')
 previous=load(preview/'guarded-assembly-preview.kicad_pcb')
 extras=[]
 for fp in find_all(previous,'footprint'):
  props={atom(v[1]):atom(v[2]) for v in find_all(fp,'property')}
  if props.get('Reference')=='MECH_PREVIEW':extras.append(fp)
 require(len(extras)==1,'Expected exactly one board-only assembly model footprint')
 copy_tree=copy.deepcopy(tree);models=preview/'models';models.mkdir(exist_ok=True);model_hashes={}
 for fp in find_all(copy_tree,'footprint'):
  for model in find_all(fp,'model'):
   source=Path(atom(model[1]).replace('${KIPRJMOD}',str(pcb.parent)))
   if not source.is_absolute():source=pcb.parent/source
   source=source.resolve();require(source.is_file(),'Missing source model: '+str(source))
   candidates=[source]
   if source.suffix.lower()=='.wrl' and source.with_suffix('.step').is_file():candidates.append(source.with_suffix('.step'))
   for candidate in candidates:
    destination=models/candidate.name;key='models/'+candidate.name
    require(key not in model_hashes or model_hashes[key]==sha(candidate),'Different models share a filename')
    shutil.copyfile(candidate,destination);model_hashes[key]=sha(destination)
   model[1]=('str','${KIPRJMOD}/models/'+source.name)
 copy_tree.append(extras[0]);preview_pcb=preview/'guarded-assembly-preview.kicad_pcb';preview_pcb.write_text(serialize(copy_tree)+'\n')
 # Validate containment after relocation: every model referenced by the review
 # PCB resolves to an asset inside this self-contained cover directory.
 for fp in find_all(copy_tree,'footprint'):
  for model in find_all(fp,'model'):
   resolved=Path(atom(model[1]).replace('${KIPRJMOD}',str(preview))).resolve()
   require(HERE in resolved.parents and resolved.is_file(),'Preview model escapes its portable bundle')
 source_project=pcb.with_suffix('.kicad_pro')
 if source_project.exists():shutil.copyfile(source_project,preview/'guarded-assembly-preview.kicad_pro')
 files=dict(proof['preview_sha256']);files.update(model_hashes);files['guarded-assembly-preview.kicad_pcb']=sha(preview_pcb)
 for name in ['guarded-assembly-preview.kicad_pro','native-assembly-bottom.png']:
  if (preview/name).is_file():files[name]=sha(preview/name)
 proof['preview_sha256']=files;proof['preview_finalizer_sha256']=sha(__file__)
 proof['interactive_preview'].update({'sha256':sha(preview_pcb),'self_contained':True,'original_pcb_geometry_unchanged':True,'bundled_component_model_files':len(model_hashes)})
 proof_path.write_text(json.dumps(proof,indent=2)+'\n')
 manifest['pcb_instance_check']={'status':'PASS','board_b_sha256':proof['pcb_sha256'],'board_p_sha256':proof['board_p']['pcb_sha256'],'verification_file':'generated/verification.json','verification_sha256':sha(proof_path)}
 manifest['preview_files_sha256']=files;manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
 with zipfile.ZipFile(out/'print-parts.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for part in manifest['parts']:archive.write(HERE/part['file'],Path(part['file']).name)
  for path in [HERE/'README.md',HERE/'pcb-contract.json',manifest_path,proof_path]:archive.write(path,path.name)
 print(json.dumps({'status':'PASS','pcb_sha256':proof['pcb_sha256'],'self_contained_preview':True,'bundled_models':len(model_hashes),'silk_only_rebound':'silkscreen_only_rebind' in proof},indent=2))
if __name__=='__main__':main()
