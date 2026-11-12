"""Reduced-order −12 V start-step model (paper check, not a verdict run); see d1-miller-rejected-20261112.md.

Needs adv_seg.npz, a 130–142 ms slice of run 43187732133 adv (adv.dat, adv-servo.txt, adv-ref.txt). The slice is kept in the project files, not in Git.
"""
import numpy as np
d=np.load('adv_seg.npz'); t=d['t']; out=d['out']; g=d['g']; cs=d['cs']
CL=180e-6
sl=np.gradient(out,t)
Id=-CL*sl
vgs=g-cs
# Id(Vgs) table from the rising part of the recorded step (monotone in vgs up to the peak)
m=(t>0.1370)&(t<0.13826)
V=vgs[m]; I=np.maximum(Id[m],1e-6)
o=np.argsort(V); V=V[o]; I=np.maximum.accumulate(I[o])
def fid(x, shift=0.0):
    x=x-shift
    lo,hi=V[0],V[-1]
    if x<=lo: return I[0]*np.exp((x-lo)/0.06)
    if x>=hi:  # extrapolate with the end log-slope
        k=np.log(I[-1]/I[-20])/(V[-1]-V[-20]); return I[-1]*np.exp(k*(x-hi))
    return np.exp(np.interp(x,V,np.log(I)))
def run(CM, Cg, scale_CM=1.0, shift=0.0, t0=0.1372, t1=0.1400, dt=2e-8, CLx=CL):
    tt=d['t']; rm=d['rm']
    k=np.searchsorted(tt,t0)
    o=out[k]; Vg=g[k]; csv=cs[k]
    Vp=(rm[k]*750+o*93.1)/843.1
    I_fb=Vp/4.7e3+(Vp+12.1)/10e6
    Vc=d['drv'][k]-Vp-I_fb*10e3
    ts=np.arange(t0,t1,dt); peak=0; peak_t=None; trace=[]
    C=CM*scale_CM
    for tn in ts:
        rmn=np.interp(tn,tt,rm); csn=np.interp(tn,tt,cs)
        Vp=(rmn*750+o*93.1)/843.1
        I_fb=Vp/4.7e3+(Vp+12.1)/10e6
        drv=Vp+I_fb*10e3+Vc
        drv=min(max(drv,-12.3),5.04)
        Ids=fid(Vg-csn,shift)
        dout=-Ids/CLx
        Igate=(drv-Vg)/10e3-(Vg-csn)/100e3
        dVg=(Igate+C*dout)/(C+Cg)
        Vc+=I_fb/10e-9*dt; o+=dout*dt; Vg+=dVg*dt
        s=-dout/1e3
        if abs(o)<0.75 and s>peak: peak=s; peak_t=tn
        trace.append((tn,o,Vg,drv,s))
    return peak,peak_t,np.array(trace)
