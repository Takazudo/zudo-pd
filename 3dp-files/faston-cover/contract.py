"""Standard-library PCB/cover contract checks, shared by tests and CAD verification."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
from sexp import atom,find_all,load

def field(node,name):return atom(find_all(node,name)[0][1])
def numbers(node,name):return [float(atom(v)) for v in find_all(node,name)[0][1:]]
def require(ok,message):
    if not ok:raise ValueError(message)


def primitive(kind,start,end,mid=None):
    a,b=sorted(tuple(round(x,5) for x in point) for point in [start,end])
    return kind,a,b,tuple(round(x,5) for x in mid) if mid else ()


def check_pcb(tree,c):
    width,height=c['world']['pcb_size_mm']
    expected=[primitive('line',*edge) for edge in [((0,0),(width,0)),((width,0),(width,height)),((width,height),(0,height))]]
    previous=[0,0]
    for notch in c['notch_geometry']['notches']:
        path=notch['edge_path_top_to_bottom'];expected.append(primitive('line',previous,path[0]['start']))
        for edge in path:expected.append(primitive(edge['type'],edge['start'],edge['end'],edge.get('mid')))
        previous=path[-1]['end']
    expected.append(primitive('line',previous,[0,height]))
    actual=[]
    for item in tree:
        if isinstance(item,list) and find_all(item,'layer') and field(item,'layer')=='Edge.Cuts':
            require(atom(item[0]) in ('gr_line','gr_arc'),'Unexpected additional Edge.Cuts primitive')
    for tag,kind in [('gr_line','line'),('gr_arc','arc')]:
        for item in find_all(tree,tag):
            if field(item,'layer')=='Edge.Cuts':actual.append(primitive(kind,numbers(item,'start'),numbers(item,'end'),numbers(item,'mid') if kind=='arc' else None))
    require(sorted(expected)==sorted(actual),'PCB outline differs from exact rounded-T contract')
    fps={}
    for fp in find_all(tree,'footprint'):
        props={atom(p[1]):atom(p[2]) for p in find_all(fp,'property')}
        ref=props['Reference'];require(ref not in fps,'Duplicate footprint '+ref);fps[ref]=(fp,props)
    for f in c['fastons']['placements']:
        ref=f['reference'];fp,props=fps[ref];at=numbers(fp,'at')
        require(field(fp,'layer')==c['fastons']['layer'],ref+' must be underneath')
        require(all(abs(a-b)<.001 for a,b in zip(at[:2],f['center_mm'])) and abs((at[2]%360)-270)<.001,ref+' position/orientation differs')
        require(atom(fp[1])==c['fastons']['footprint'] and props.get('LCSC')==c['fastons']['lcsc'],ref+' exact identity differs')
        models=find_all(fp,'model');require(len(models)==1,ref+' must have one reviewed model')
        for name,want in [('rotate',[0,0,90]),('offset',[0,0,0]),('scale',[1,1,1])]:
            values=numbers(find_all(models[0],name)[0],'xyz')
            require(all(abs(a-b)<.001 for a,b in zip(values,want)),ref+' model transform differs')
    thickness=float(field(find_all(tree,'general')[0],'thickness'))
    require(abs(thickness-1.6)<.001,'PCB nominal thickness differs from cover slot')
    return {'status':'PASS','outline_primitives':len(actual),'faston_count':4,'pcb_thickness_mm':thickness}


