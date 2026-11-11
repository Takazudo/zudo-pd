# D1 servo and dead-zone criteria — pre-registered 2026-11-11

Fixed before the servo-node extraction run (#235). Diagnostic only: electrical_acceptance
stays NOT ESTABLISHED, the recorded 2 us failures stay failures, and no threshold here is a
contract tolerance. `servo_criteria.py` implements exactly these rules and a test keeps the
numbers in step.

The run uses the same pinned identity and identity control as run 43087070975. It adds one
output-only line per deck and changes no parameter:

`wrdata {case}-servo.txt v(p5_drv) v(trk5) v(p5_cs) v(m12_drv) v(trk12n_fb) v(m12_cs) v(ctz)`

## Prediction already visible in the retained gate data

The saved gate nodes (behind 10 kΩ from each driver) suggest both servos were parked at their
low supply and left it well before the pass pair conducted: `p5_g` last sits within 0.1 V of
0 V at about 127.67 ms (+5 conduction about 139.62 ms) and `m12_g` leaves the band at
−12.142 V at about 126.77 ms (−12 conduction about 137.65 ms). If the driver nodes confirm
this, the expected outcome is windup present, recovery not coincident with the excursion and
a dead zone set by the conduction threshold after windup. The run measures the drivers
directly; this prediction is stated so the criteria are not tuned to the result.

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
- Driver exit = the first bin after the last in-band bin before t_on (extended forward) that
  is outside the band.
- Servo input error = + input − − input (U13B: RAMP_P5 − `trk5`; U9B: `trk12n` − `trk12n_fb`,
  with `trk12n` computed from RAMP_M12 and the −12 output through RT12NA/RT12NB). A negative
  error drives the driver toward its lower supply.
- Vgs = gate node − executed gate offset (VO2/VO3) − FET source node (`p5_cs`/`m12_cs`).

## Verdicts

| Question | Rule |
| --- | --- |
| Servo wound up at a supply before conduction | **SUPPORTED** if the driver is in band for at least 10 us before t_on. **REFUTED** if it is never in band before t_on while the raw driver does enter the band somewhere in the record (so the band is reachable for this macromodel). Otherwise **UNRESOLVED**. |
| Windup induced by the pre-bias floor | When windup is supported: **SUPPORTED** if, in at least 90 % of the in-band bins, the servo input error pushes the driver toward the supply it is parked at (the output floor sits above the commanded output); **REFUTED** if that holds in at most 10 %; otherwise **UNRESOLVED**. Not applicable without windup. |
| Peak slope coincides with driver recovery | **YES** if the driver exit lies in [t_on − 100 us, failed segment start], else **NO**. |
| Dead zone set by | **PRE-BIAS FLOOR** if windup is supported and the exit coincides (the driver is held at the supply until conduction). **CONDUCTION THRESHOLD AFTER WINDUP** if windup is supported, the exit is earlier than t_on − 100 us, the driver stays out of the band from the exit to t_on and Vgs climbs at least 0.2 V over that span. **CONDUCTION THRESHOLD** if windup is refuted and Vgs climbs at least 0.2 V from t_lag to t_on with the driver out of the band. Otherwise **UNRESOLVED**. |

If the pass pair is not conducting at the failed segment, conduction starts before the
window, or the servo analysis cannot run, every verdict is **UNRESOLVED**. If the run's
identity control is NOT REPRODUCED, nothing is evaluated or adopted and the attempt is
reported as failed. No outcome adopts a correction; correction candidates go to the manager
as a proposal.
