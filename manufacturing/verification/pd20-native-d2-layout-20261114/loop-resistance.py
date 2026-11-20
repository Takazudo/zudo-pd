"""Copper resistance (1 oz, 35 um, 20 C) from each D2 discharge part rail pad to the rail connectors, along routed tracks and vias. usage: loop-resistance.py geom.json"""
import json,math,heapq,collections,sys
g=json.load(open(sys.argv[1]))  # dump.py output of the saved native PCB
RHO=1.72e-8;T=35e-6;VIA=1.72e-8*1.6e-3/(math.pi*0.3e-3*25e-6)
def run(net,src_ref):
    nodes={};adj=collections.defaultdict(list)
    def nid(p):
        k=(round(p[0],3),round(p[1],3));nodes.setdefault(k,len(nodes));return k
    items=[]
    for t in g['tracks']:
        if t['net']==net:
            a,b=nid(t['a']),nid(t['b']);r=RHO*math.dist(t['a'],t['b'])*1e-3/(t['w']*1e-3*T)
            adj[a].append((b,r,t['w']));adj[b].append((a,r,t['w']));items.append((t,a,b))
    def sd(p,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];L=dx*dx+dy*dy;t=0 if L==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L))
        return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy),t
    ends=list(nodes)
    for t,a,b in items:
        R=RHO*math.dist(t['a'],t['b'])*1e-3/(t['w']*1e-3*T)
        for n in ends:
            if n in (a,b):continue
            d,u=sd(n,t['a'],t['b'])
            if d<t['w']/2 and 0<u<1:
                adj[n]+= [(a,R*u,t['w']),(b,R*(1-u),t['w'])];adj[a].append((n,R*u,t['w']));adj[b].append((n,R*(1-u),t['w']))
    pads=[(f['ref'],p) for f in g['fps'] for p in f['pads'] if p['net']==net]
    # join track ends and vias that land inside a pad bbox to a pad node (zero resistance)
    for ref,p in pads:
        k=('pad',ref,p['num'])
        for n in list(nodes):
            x0,y0,x1,y1=p['bbox']
            if x0-0.5<=n[0]<=x1+0.5 and y0-0.5<=n[1]<=y1+0.5: adj[k].append((n,0,9));adj[n].append((k,0,9))
    for v in g['vias']:
        if v['net']==net:
            k=nid(v['c'])
            for n in list(nodes):
                if n!=k and math.dist(n,k)<v['d']/2+0.5: adj[k].append((n,VIA/2,9));adj[n].append((k,VIA/2,9))
    starts=[('pad',r,p['num']) for r,p in pads if r==src_ref]
    dist={s:0 for s in starts};minw={s:9 for s in starts};pq=[(0,i,s) for i,s in enumerate(starts)];cnt=len(pq)
    while pq:
        d,_,u=heapq.heappop(pq)
        if d>dist[u]:continue
        for v,r,w in adj[u]:
            if d+r<dist.get(v,1e9):dist[v]=d+r;minw[v]=min(minw[u],w);cnt+=1;heapq.heappush(pq,(d+r,cnt,v))
    caps=sorted((dist[k],k[1],minw[k]) for k in dist if isinstance(k[0],str) and k[0]=='pad' and k[1][0]=='J')
    return caps[:8]
for net,ref in (('P12_OUT','RX12'),('P5_OUT','RX5'),('M12_OUT','Q55')):
    print(net,ref,'mohm to connector pad, min width mm:',[(round(d*1e3,1),r,w) for d,r,w in run(net,ref)])
