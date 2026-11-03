import sys,json,glob
def load(f):
    rows=[]
    for line in open(f):
        p=line.split()
        if len(p)<20: continue
        v=[float(x) for x in p]
        rows.append((v[0],v[1],v[3],v[5],v[7],v[9],v[11],v[13],v[15],v[17],v[19]))
    return rows
T0=40e-3; TD=85e-3
out={}
for f in sorted(glob.glob(sys.argv[1]+'/*.dat')):
    name=f.split('/')[-1][:-4]
    r=load(f); res={'t_end_ms':round(r[-1][0]*1e3,3)}
    on=[x for x in r if T0<=x[0]<TD-0.5e-3]
    plateau={}
    for nm,idx,sg,band in (('+12',1,1,12.00),('+5',2,1,5.05),('-12',3,-1,12.00)):
        pl=[x for x in on if x[0]<=50e-3][-1][idx]*sg
        plateau[nm]=pl
        st=next(x[0] for x in on if x[0]>50e-3 and sg*x[idx]>=pl+0.1)
        be=next((x[0] for x in on if sg*x[idx]>=band),None)
        # slopes over 100us windows in enable phase
        sl=0;j=0
        for i in range(len(on)):
            while on[i][0]-on[j][0]>1e-4: j+=1
            if on[i][0]-on[j][0]>5e-5: sl=max(sl,abs(on[i][idx]-on[j][idx])/(on[i][0]-on[j][0])/1e3)
        res[nm]={'prebias_plateau_v':round(pl,4),'ramp_start_ms':round((st-T0)*1e3,3),'band_entry_ms':round((be-T0)*1e3,3) if be else None,'max_slope_v_per_ms':round(sl,3),'v_before_disable':round(on[-1][idx],4)}
    res['peak_source_a']={'+12':round(max(-x[5] for x in on),3),'+5':round(max(-x[6] for x in on),3),'-12':round(max(x[7] for x in on),3)}
    res['steady_source_a']={'+12':round(-on[-1][5],3),'+5':round(-on[-1][6],3),'-12':round(on[-1][7],3)}
    res['max_p12_minus_absm12_v']=round(max(x[1]+x[3] for x in on),4)
    res['min_p12_minus_absm12_v']=round(min(x[1]+x[3] for x in on),4)
    sts=[res[k]['ramp_start_ms'] for k in ('+12','+5','-12')]
    bes=[res[k]['band_entry_ms'] for k in ('+12','+5','-12')]
    res['ramp_start_skew_ms']=round(max(sts)-min(sts),3)
    res['band_entry_skew_ms']=round(max(bes)-min(bes),3) if None not in bes else None
    res['p5_last']=None not in bes and bes[1]>=max(bes[0],bes[2])
    if 'dis' in name:
        g=[x for x in r if x[0]>TD]
        def off(idx,sgn):
            return next((round((x[0]-TD)*1e6,2) for x in g if abs(x[idx])<0.01),None)
        res['disconnect_us_to_10mA']={'+12':off(5,1),'+5':off(6,1),'-12':off(7,1)}
        def gate_off(idx,ref):
            return next((round((x[0]-TD)*1e6,2) for x in g if x[idx]-ref(x)<1.0),None)
        res['gate_below_1v_us']={'+12':gate_off(8,lambda x:x[1]),'+5':gate_off(9,lambda x:x[2])}
        res['rails_at_end']={'+12':round(r[-1][1],3),'+5':round(r[-1][2],3),'-12':round(r[-1][3],3)}
    else:
        w=[x for x in r if 90e-3<=x[0]<=99.9e-3]
        res['settled_pp_mv_90_100ms']={k:round((max(x[i] for x in w)-min(x[i] for x in w))*1e3,3) for k,i in (('+12',1),('+5',2),('-12',3))}
    out[name]=res
print(json.dumps(out,indent=1))
