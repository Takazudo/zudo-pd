import json
from analysis_inputs import START_CASES, load, run, selected_files, window, adjacent_slope_screen

T0=40e-3; TD=235e-3; TP=100e-3   # phase 10: RAMP reset releases about 75 ms after enable
def main():
    out={}
    for f in selected_files(START_CASES):
        name=f.stem
        r=load(f); res={'t_end_ms':round(r[-1][0]*1e3,3)}
        on=window(r, T0, TD-0.5e-3, str(f))
        plateau={}
        for nm,idx,sg,band in (('+12',1,1,12.00),('+5',2,1,5.05),('-12',3,-1,12.00)):
            pl=window(on, T0, TP + 1e-10, str(f))[-1][idx]*sg
            plateau[nm]=pl
            st=next((x[0] for x in on if x[0]>TP and sg*x[idx]>=pl+0.1), None)
            if st is None:
                raise ValueError(f'{f}: {nm} never starts its ramp after {TP:g} s')
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
            w=window(r, 225e-3, 234e-3 + 1e-10, str(f))
            res['settled_pp_mv_225_234ms']={k:round((max(x[i] for x in w)-min(x[i] for x in w))*1e3,3) for k,i in (('+12',1),('+5',2),('-12',3))}
        # voltage forms of the start-order rows (contract section 5)
        res['p12_max_while_absm12_lt_0v1']=round(max((x[1] for x in on if -x[3]<0.1),default=0),4)
        res['p12_max_while_absm12_lt_0v6']=round(max((x[1] for x in on if -x[3]<0.6),default=0),4)
        res['absm12_max_while_p12_le_0v5']=round(max((-x[3] for x in on if x[1]<=0.5),default=0),4)
        res['absm12_max_while_p12_lt_5v2']=round(max((-x[3] for x in on if x[1]<5.2),default=0),4)
        res['p5_max_while_min_analog_lt_1v5']=round(max((x[2] for x in on if min(x[1],-x[3])<1.5),default=0),4)
        res['p5_max_while_min_analog_lt_8v']=round(max((x[2] for x in on if min(x[1],-x[3])<8.0),default=0),4)
        res['adjacent_slope_screen'] = {
            rail: adjacent_slope_screen(on, idx, sign, limit, no_load=not name.endswith('R'), exception=exception)
            for rail, idx, sign, limit, exception in (
                ('+12', 1, 1, 1.23, None), ('+5', 2, 1, .51, (.45, .95, .114)),
                ('-12', 3, -1, 1.22, (.75, 1.47, .265)))}
        out[name]=res
    print(json.dumps(out,indent=1))

if __name__ == '__main__':
    run(main)
