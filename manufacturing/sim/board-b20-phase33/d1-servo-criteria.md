# D1 servo and dead-zone criteria — pre-registered 2026-11-11

Fixed before the servo-node extraction run (#235); see the revision history below. Diagnostic only: electrical_acceptance
stays NOT ESTABLISHED, the recorded 2 us failures stay failures, and no threshold here is a
contract tolerance. `servo_criteria.py` implements exactly these rules and a test keeps the
numbers in step.

The run uses the same pinned identity and identity control as run 43087070975. It adds one
output-only line per deck and changes no parameter:

`wrdata {case}-servo.txt v(p5_drv) v(trk5) v(p5_cs) v(m12_drv) v(trk12n_fb) v(m12_cs) v(ctz)`

## Revision history and predictions (this is not a blind test)

The first version (commit 0ee91cc) timed the dead zone from the ideal-lag start and would have
called windup REFUTED for both rails. An independent review then inspected the retained gate
nodes, which sit behind 10 kΩ from each driver: `p5_g` last sits within 0.1 V of 0 V at about
127.67 ms (+5 conduction about 139.62 ms) and `m12_g` leaves the band at −12.142 V at about
126.77 ms (−12 conduction about 137.65 ms). The criteria were revised on 2026-11-11 after that
inspection: windup is judged by the driver's last supply exit, REFUTED needs the lower supply's
band to be reachable after the supplies settle, the floor question is judged by the release
timing, and the class CONDUCTION THRESHOLD AFTER WINDUP was added. The run therefore tests the
gate-to-driver inference, not a blind hypothesis.

Predicted from the gate data, for both rails: windup SUPPORTED; peak coincides with recovery
NO; dead zone CONDUCTION THRESHOLD AFTER WINDUP. Release when the reference passes the floor
is predicted **not SUPPORTED** (REFUTED or UNRESOLVED): the gates leave their supplies about
10 ms before k × reference visibly rises past the output floor, so something other than the
reference (for example a clamp or enable transition) may release the windup. The servo error
was not saved, so this one is the least certain prediction.

## Measurement

- Every quantity is a mean over 2 us bins (the refined maximum step), from 20 ms before to
  1 ms after the failed segment, so a sub-grid solver-timestep ring cannot decide a verdict.
  Durations are counted inside this window only.
- Conduction onset t_on = start of the continuous run of bins, ending at the failed segment,
  in which the rail's supply current (i(VP5) or i(VM12); i(VM12) includes about 0.5 mA of
  op-amp quiescent current) is at least 5 mA in magnitude.
- Ideal lag = how far the output trails k × per-rail reference in the tracking direction
  (+5: k = 3.32 on RAMP_P5; −12: k = 8.0559 on RAMP_M12); its start t_lag (the continuous run
  of bins before t_on with lag above 0.05 V) is reported for information only. It ignores the
  RT5O/RT12NO setpoint shift, so it does not mark when the integrator started to unwind.
- Driver in band = driver (U13B `p5_drv`, supplies 0 V / VIN 20 V; U9B `m12_drv`, supplies
  M12_PRE −12.142 V / P5_SUP 4.98 V, read from the executed deck) within 0.1 V of a supply.
- Lower band reachable = the driver's 2 us bin mean comes within 0.1 V of its lower
  (pass-pair-off) supply somewhere after 2 ms, when the supply PWLs have settled.
- Driver exit = the first bin after the last in-band bin before t_on (extended forward) that
  is outside the band.
- Servo input error = + input − − input (U13B: RAMP_P5 − `trk5`; U9B: `trk12n` − `trk12n_fb`,
  with `trk12n` computed from RAMP_M12 and the −12 output through RT12NA/RT12NB). A negative
  error drives the driver toward its lower supply.
- Error rise = the last bin before t_on where the servo input error rises through zero
  (from drive-down to drive-up).
- Vgs = gate node − executed gate offset (VO2/VO3) − FET source node (`p5_cs`/`m12_cs`).

## Verdicts

| Question | Rule |
| --- | --- |
| Servo wound up at a supply before conduction | **SUPPORTED** if the driver is in band for at least 10 us before t_on. **REFUTED** if it is never in band before t_on while the lower band is reachable. Otherwise **UNRESOLVED**. |
| Windup released when the reference passes the pre-bias floor | When windup is supported: **SUPPORTED** if the output stays within 5 mV of its exit value over the last 1 ms of parking and the driver exit follows the error rise by 0 to 200 us. **REFUTED** if the driver exits before the error rise (something other than the reference released it). Otherwise **UNRESOLVED**. Not applicable without windup. The share of parked bins whose error sign matches the parked direction is reported as a consistency check only. |
| Peak slope coincides with driver recovery | **YES** if the driver exit lies in [t_on − 100 us, failed segment start], else **NO**. |
| Dead zone set by | **HELD AT SUPPLY UNTIL CONDUCTION** if windup is supported and the exit coincides. **CONDUCTION THRESHOLD AFTER WINDUP** if windup is supported, the exit is earlier than t_on − 100 us, the driver stays out of the band from the exit to t_on and Vgs climbs at least 0.2 V over that span. **CONDUCTION THRESHOLD** if windup is refuted and Vgs climbs at least 0.2 V from t_lag to t_on with the driver out of the band. Otherwise **UNRESOLVED**. |

If the pass pair is not conducting at the failed segment, conduction starts before the
window, the servo vectors are missing or the servo analysis fails, every verdict is **UNRESOLVED**. If the run's
identity control is NOT REPRODUCED, nothing is evaluated or adopted and the attempt is
reported as failed. No outcome adopts a correction; correction candidates go to the manager
as a proposal.
