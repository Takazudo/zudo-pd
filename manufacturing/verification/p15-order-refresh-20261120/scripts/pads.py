import sys,math,json
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'scripts/schgen'))
from sexp import atom,find_all,load
b=load(sys.argv[1]); out={}
def props(n): return {atom(x[1]):atom(x[2]) for x in find_all(n,'property')}
for fp in find_all(b,'footprint'):
    p=props(fp); ref=p.get('Reference')
    if ref not in sys.argv[2].split(','): continue
    at=find_all(fp,'at')[0]; fx,fy=float(atom(at[1])),float(atom(at[2])); fr=float(atom(at[3])) if len(at)>3 else 0.0
    pads=[]
    for pad in find_all(fp,'pad'):
        pa=find_all(pad,'at')[0]; px,py=float(atom(pa[1])),float(atom(pa[2]))
        t=math.radians(-fr); ax=fx+px*math.cos(t)-py*math.sin(t); ay=fy+px*math.sin(t)+py*math.cos(t)
        net=find_all(pad,'net'); nn=atom(net[0][2]) if net and len(net[0])>2 else (atom(net[0][1]) if net else '')
        pads.append({'pad':atom(pad[1]),'abs_x':round(ax,3),'abs_y':round(ay,3),'net':nn})
    out[ref]={'fp':atom(fp[1]),'layer':atom(find_all(fp,'layer')[0][1]),'at':[fx,fy,fr],'lcsc':p.get('LCSC'),'value':p.get('Value'),'pads':pads}
print(json.dumps(out,indent=1))
