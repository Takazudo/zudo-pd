import sys,math,glob,json
res={}
for f in sorted(glob.glob(sys.argv[1]+'/*.dat')):
    rows=[]
    for line in open(f):
        p=line.split()
        if len(p)<3: continue
        try: fr,re_,im=float(p[0]),float(p[1]),float(p[2])
        except: continue
        rows.append((fr,complex(re_,im)))
    fc=pm=None; gm=None
    unwrap=[]; prev=None; off=0
    for fr,t in rows:
        ph=math.degrees(math.atan2(t.imag,t.real))
        if prev is not None:
            while ph+off-prev>180: off-=360
            while ph+off-prev<-180: off+=360
        ph+=off; prev=ph; unwrap.append((fr,abs(t),ph))
    for (f1,m1,p1),(f2,m2,p2) in zip(unwrap,unwrap[1:]):
        if fc is None and m1>=1>m2:
            k=math.log(m1)/(math.log(m1)-math.log(m2)); fc=f1*(f2/f1)**k; ph=p1+(p2-p1)*k; pm=180+ph
        if gm is None and fc is not None and p1>-180>=p2:
            gm=-20*math.log10(m1)
    res[f.split('/')[-1][:-4]]={'dc_gain_db':round(20*math.log10(unwrap[0][1]),1),'fc_khz':round(fc/1e3,2) if fc else None,'pm_deg':round(pm,1) if pm is not None else None,'gm_db':round(gm,1) if gm else None}
print(json.dumps(res,indent=1))
