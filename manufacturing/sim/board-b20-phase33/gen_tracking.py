import sys
def net(name, d12, d5, dn, rload, disable_at=None, tstop='250m', maxstep='5u', start='uic', reenable_after=None, edge=50e-6,
        interlock=None):
    # d* = effective threshold shift (V) per pair; rload: True -> resistive load at I_TRANSIENT_MIN
    rl = ''
    if rload:
        rl = 'RL12 p12_out 0 6.0\nRL5 p5_out 0 12.625\nRLN 0 m12_out 6.316\n'
    dis = ''
    if disable_at:
        td = float(disable_at[:-1]) * 1e-3
        if reenable_after is None:
            dis = f'VDIS dis 0 PWL(0 0 {disable_at} 0 {td + edge:.6g} 5)\n'
        else:
            # phase 11 re-entry: EN_N high at td, low again reenable_after seconds later (inside the RAMP reset window)
            tr = td + reenable_after
            dis = f'VDIS dis 0 PWL(0 0 {td:.6g} 0 {td + edge:.6g} 5 {tr:.6g} 5 {tr + edge:.6g} 0)\n'
    else:
        dis = 'VDIS dis 0 0\n'
    if start == 'uic':
        # phase-7 start: stiff sources at their final values, transient from initial conditions
        supplies = 'VIN vin 0 20\nVSUP p5sup 0 4.98\nVREF ref25 0 2.5\n'
        vp12, vp5, vm12 = 'VP12 p12_src 0 12.172\n', 'VP5 p5_src 0 5.094\n', 'VM12 m12_src 0 -12.142\n'
        ic = ('.ic v(p12_pre)=12.172 v(p12_sh)=12.172 v(p5_pre)=5.094 v(p5_sh)=5.094 v(m12_pre)=-12.142 '
              'v(m12_sh)=-12.142 v(m12_cs)=-12.14 v(m12_g)=-12.142 v(m12_drv)=-12.1 v(m12_src)=-12.142\n')
        uic = ' uic'
        boffx = 'BOFFX offx0 0 V=v(enn)>2.5 ? 4.98 : -12.14\n'
    else:
        # ramp start: every source rises from 0 V over 2 ms from a DC operating point at zero (no uic)
        supplies = 'VIN vin 0 PWL(0 0 2m 20)\nVSUP p5sup 0 PWL(0 0 2m 4.98)\nVREF ref25 0 PWL(0 0 2m 2.5)\n'
        vp12, vp5, vm12 = ('VP12 p12_src 0 PWL(0 0 2m 12.172)\n', 'VP5 p5_src 0 PWL(0 0 2m 5.094)\n',
                           'VM12 m12_src 0 PWL(0 0 2m -12.142)\n')
        ic, uic = '', ''
        boffx = 'BOFFX offx0 0 V=v(enn)>2.5 ? v(p5sup) : v(m12_src)\n'
    if interlock is None:
        enable = 'BENN enn 0 V=max(v(enn0),v(dis))\n'
    else:
        # phase 12 minimum-off interlock (Q65/Q66, RHO1+RHO2 300k, CHO 1 uF) with a behavioural enable latch:
        # enq is the set/reset request (RDY/FAULT_N/EN_E in the drawn latch), lat high = latched enabled
        vth, c_eff = interlock
        enable = (f'BENQ enq 0 V=max(v(enn0),v(dis))\nRHO p5sup en_ho 300k\nCHO en_ho 0 {c_eff}\n'
                  'BHR en_ho 0 I=v(en_ho)*(1/3.5)*0.5*(1+tanh((v(lat)-4)*4))+v(en_ho)*1e-8\n'
                  'CLAT lat 0 10n\n'
                  # set through Q66 (EN_HO above VGS(th)), self-hold once past 1.5 V (Q33/Q34), clear by the request
                  f'BLAT 0 lat I=1e-5*(0.5*(1+tanh((2.5-v(enq))*4))*(0.5*(1+tanh((v(en_ho)-{vth})*20))'
                  '+0.5*(1+tanh((v(lat)-1.5)*4)))*(5-v(lat))-0.5*(1+tanh((v(enq)-2.5)*4))*v(lat))\n'
                  'BENN enn 0 V=5-v(lat)\n')
    return f"""* {name}: Board B20 phase-12 tracking start with the minimum-off interlock with start-order clamps and the 470 nF RAMP reset delay (vendor OPAx187 SBOMAB6, CSD18543Q3A SLPM286 models)
.include ../lib/opax187.lib
.include ../lib/csd18543q3a_ngspice.lib
.model DZ11 D(BV=10.8 IBV=1m RS=20 N=1.5)
.model DBODY D(IS=1e-12 RS=1 BV=50 CJO=20p)
.model SWM SW(VT=2.5 VH=0 RON=3.5 ROFF=100meg)
{supplies}* converters as stiff sources behind 20 mOhm output impedance (PA), shunts as drawn
{vp12}RP12S p12_src p12_pre 20m
CP12 p12_pre 0 57u
RSH12 p12_pre p12_sh 10m
{vp5}RP5S p5_src p5_pre 20m
CP5 p5_pre 0 57u
RSH5 p5_pre p5_sh 20m
{vm12}RM12S m12_src m12_pre 20m
CM12 0 m12_pre 57u
RSHN m12_sh m12_pre 10m
* enable: EN_N high until 1 ms, then low (enable); dis = later disable
VENN enn0 0 PWL(0 5 40m 5 40.05m 0)
{enable}* tracking reference
RRMP ref25 ramp 20k
CRMP ramp 0 1.47u
RDLY enn ennd 100k
CDLY ennd 0 470n
BRST ramp 0 I=v(ramp,0)*(1/3.5)*0.5*(1+tanh((v(ennd)-1.0)*8))+v(ramp,0)*1e-8
* Q24 drain node: P5_SUP while disabled, pulled to M12_PRE through 156k while enabled
{boffx}ROFFX offx0 offx 1k
* +12 tracking: U13A on VIN
XU13A ramp_p12 trk12 vin 0 p12_drv OPAx187
RT12A p12_out trk12 69.8k
RT12B trk12 0 10k
CT12 p12_drv trk12 10n
RT12O m12_pre trk12 10meg
RT12P offx dp12 100k
DP12 dp12 trk12 DBODY
RG1 p12_drv p12_g 10k
RG1P p12_g p12_cs 100k
DZ1 p12_cs p12_g DZ11
B10 p12_g 0 I=v(p12_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p12_g,0)*1e-8
VO1 p12_g p12_gi {d12}
XQ1 p12_sh p12_gi p12_cs csd18543q3a
XQ2 p12_out p12_gi p12_cs csd18543q3a
* +5 tracking: U13B on VIN
XU13B ramp_p5 trk5 vin 0 p5_drv OPAx187
RT5A p5_out trk5 23.2k
RT5B trk5 0 10k
CT5 p5_drv trk5 10n
RT5O m12_pre trk5 10meg
RT5P offx dp5 100k
DP5 dp5 trk5 DBODY
RG2 p5_drv p5_g 10k
RG2P p5_g p5_cs 100k
DZ2 p5_cs p5_g DZ11
B11 p5_g 0 I=v(p5_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p5_g,0)*1e-8
VO2 p5_g p5_gi {d5}
XQ3 p5_sh p5_gi p5_cs csd18543q3a
XQ4 p5_out p5_gi p5_cs csd18543q3a
* -12 tracking: U9B on P5_SUP / M12_PRE
XU9B trk12n trk12n_fb p5sup m12_pre m12_drv OPAx187
RT12NC trk12n_fb 0 4.7k
CT12N m12_drv ctz 10n
RCTZ ctz trk12n_fb 10k
RT12NO m12_pre trk12n_fb 10meg
RT12NP offx dpn 100k
DPN dpn trk12n_fb DBODY
RT12NA ramp_m12 trk12n 93.1k
RT12NB trk12n m12_out 750k
RG3 m12_drv m12_g 10k
RG3P m12_g m12_cs 100k
DZ3 m12_cs m12_g DZ11
* Q24 / Q25 level shifter modelled as an ideal switch to M12_PRE (no vendor BSS138/DMP3036 model)
B25 m12_g m12_pre I=v(m12_g,m12_pre)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(m12_g,m12_pre)*1e-8
VO3 m12_g m12_gi {dn}
XQ5 m12_sh m12_gi m12_cs csd18543q3a
* simulation-only convergence aid (not a board part): 100 Mohm across Q5, below the FET leakage scale
RCV1 m12_cs m12_sh 100meg
XQ6 m12_out m12_gi m12_cs csd18543q3a
* phase-9 start-order clamps (U15/U16 OPA2187 on P5_SUP / M12_PRE; BSS138 body diodes as DBODY)
XU15A 0 mabs_n p5sup m12_pre mabs OPAx187
RMA1 m12_out mabs_n 100k
RMA2 mabs_n mabs 15k
RLV1 mabs lvl12 9.76k
RLV2 lvl12 vx12 102k
RVX1 ref25 vx12 30.1k
RVX2 vx12 0 10k
XU15B lvl12 ramp_p12 p5sup m12_pre clp12 OPAx187
XU16A lvlm12 ramp_m12 p5sup m12_pre clpm12 OPAx187
XU16B mabs ramp_p5 p5sup m12_pre clp5 OPAx187
RLM1 p12_out lvlm12 64.9k
RLM2 lvlm12 0 10.2k
RCP1 ramp ramp_p12 1k
RCP2 ramp ramp_m12 1k
RCP3 ramp ramp_p5 1k
DQ62 ramp_p12 clp12 DBODY
DQ63 ramp_m12 clpm12 DBODY
DQ64 ramp_p5 clp5 DBODY
* OSC-side load: contract maximum capacitance, 50 mOhm ESR (PA)
CL12 p12_out cl12 180u
RCL12 cl12 0 50m
CL5 p5_out cl5 120u
RCL5 cl5 0 50m
CLN 0 cln 180u
RCLN cln m12_out 50m
{rl}{dis}
.options method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 rshunt=1e10
{ic}.tran 2u {tstop} 0 {maxstep}{uic}
.control
run
wrdata {name}.dat v(p12_out) v(p5_out) v(m12_out) v(ramp) i(VP12) i(VP5) i(VM12) v(p12_g) v(p5_g) v(m12_g) v(enn)
.endc
.end
"""
# phase 33: the phase 12 decks with the phase 32 in-stock divider values (RT12NA 93.1k, RT12NB 750k, RLV1 9.76k,
# RLV2 102k); nothing else changes.
# phase 12: the phase-10 start cases and the phase-11 re-entry cases, both with the drawn minimum-off interlock at
# its shortest hold (Q66 VGS(th) 0.5 V PA minimum, CHO effective 0.6 uF = -40 %, PA): 19 ms after a disable.
# Re-entry decks keep the phase-11 simulation-only softening (1 ms EN_N edges, gate pulldowns at 1/35 S).
SHORT = (0.5, '0.6u')
starts = {'nom': (0, 0, 0, False), 'adv': (-0.5, -0.5, 0.5, False), 'rev': (0.5, 0.5, -0.5, False),
          'nomR': (0, 0, 0, True), 'advR': (-0.5, -0.5, 0.5, True), 'revR': (0.5, 0.5, -0.5, True)}
reentry = {f'reR{n}': dict(reenable_after=n * 1e-3) for n in (6, 10, 14, 20)}
reentry.update({f'reB{n}': dict(reenable_after=n * 1e-3, td='200m', tstop='420m') for n in (6, 10, 14, 20)})
edge = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-3
for k, (a, b, c, r) in starts.items():
    deck = net(k, a, b, c, r, None, maxstep='5u', start='ramp', interlock=SHORT)
    deck = deck.replace('.options method=gear', '.options method=trap')
    open(f'{sys.argv[1]}/{k}.cir', 'w').write(deck)
for k, kw in reentry.items():
    kw = dict(kw); td = kw.pop('td', '150m'); tstop = kw.pop('tstop', '320m')
    deck = net(k, 0, 0, 0, True, td, tstop=tstop, maxstep='5u', start='ramp', edge=edge, interlock=SHORT, **kw)
    deck = deck.replace('*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))', '*(1/35)*0.5*(1+tanh((v(enn)-2.5)*4))')
    deck = deck.replace('.options method=gear', '.options method=trap')
    assert deck.count('(1/35)') == 3, k
    open(f'{sys.argv[1]}/{k}.cir', 'w').write(deck)
