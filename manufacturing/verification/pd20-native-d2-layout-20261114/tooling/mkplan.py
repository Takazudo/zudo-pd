import sys, json; sys.path.insert(0,'tmp/d2'); import d2lib as L
sys.path.insert(0,'scripts/schgen')
from sexp import load, find_all, atom
s=load('boards/board-b20-draft/board-b20-draft.kicad_sch')
uu={}
for x in find_all(s,'symbol'):
    if not find_all(x,'lib_id'): continue
    ref=[atom(p[2]) for p in find_all(x,'property') if atom(p[1])=='Reference']
    if ref: uu[ref[0]]=atom(find_all(x,'uuid')[0][1])
placed=json.load(open('tmp/d2/placed_bl.json'))+json.load(open('tmp/d2/placed_um.json'))
b=L.Board(); rm=set()
parts=[]
for q in placed:
    g=L.part_geom(q['ref'],*q['at'][:3])
    r=b.check(g); assert r is not None,(q['ref'],L.why(b,g)); rm|=set(r); b.placed.append(g)
    c=L.spec.COMPONENTS[q['ref']]
    parts.append({'ref':q['ref'],'fp':c[3].split(':')[1],'value':c[1],'lcsc':c[2],'sym_uuid':uu[q['ref']],'at':[q['at'][0],q['at'][1],q['at'][2]],
                  'nets':{p['num']:p['net'] for p in g['pads'] if p['net']},'pad_xy':{p['num']:[round(v,3) for v in p['c']] for p in g['pads']}})
items=json.load(open('tmp/d2/routes_all.json'))
# replaces the removed Q51.1 pad, which was the junction of the retained R60 to Q56 DIS_P chain
items.append(['DIS_P','t',[96.7,68.3],[97.6,67.6],'F.Cu',0.25])
# keep the B.Cu GND island at (50-64, 33-53) that the new M12_OUT B track cuts off from the main pour
items+= [['GND','v',[58.45,41.5]],['GND','v',[55.7,39.5]]]
plan={'lib':str(L.LIB),'remove_refs':sorted(L.REMOVED),'drop_nets':['P12_DX','P5_DX','M12_DX'],
      'remove_gnd_vias':[[round(v,3) for v in b.gvias[i].centroid.coords[0]] for i in sorted(rm)],
      'parts':parts,'items':items,'field_sync':{r:[L.spec.COMPONENTS[r][1],L.spec.COMPONENTS[r][2]] for r in ('R61','R62')},'prune_nets':['DIS_P','M12_DG','M12_OUT','P12_OUT','P5_OUT','GND']}
json.dump(plan,open('tmp/d2/plan.json','w'),indent=0)
print(len(parts),'parts',len(items),'items','gnd vias removed',plan['remove_gnd_vias'])
