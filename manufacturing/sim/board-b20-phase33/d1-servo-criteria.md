# D1 servo and dead-zone criteria — pre-registered 2026-11-11

Fixed before the servo-node extraction run (#235). Diagnostic only: electrical_acceptance
stays NOT ESTABLISHED, the recorded 2 us failures stay failures, and no threshold here is a
contract tolerance. `servo_criteria.py` implements exactly these rules and a test keeps the
numbers in step.

The run uses the same pinned identity and identity control as run 43087070975. It adds one
output-only line per deck and changes no parameter:

`wrdata {case}-servo.txt v(p5_drv) v(trk5) v(p5_cs) v(m12_drv) v(trk12n_fb) v(m12_cs) v(ctz)`

## Measurement

- Every quantity is a mean over 2 us bins (the refined maximum step), from 20 ms before to
  1 ms after the failed segment, so a sub-grid solver-timestep ring cannot decide a verdict.
- Lag = how far the output trails k × per-rail reference in the tracking direction
  (+5: k = 3.32 on RAMP_P5; −12: k = 8.0559 on RAMP_M12).
- Conduction onset t_on = start of the continuous run of bins, ending at the failed segment,
  with |source current| ≥ 5 mA.
- Dead zone = [t_lag, t_on], where t_lag starts the continuous run of bins before t_on with
  lag > 0.05 V.
- Driver saturated = driver (U13B `p5_drv`, supplies 0 V / VIN 20 V; U9B `m12_drv`, supplies
  M12_PRE −12.142 V / P5_SUP 4.98 V, read from the executed deck) within 0.1 V of a supply.
- Recovery = the first bin after the last saturated dead-zone bin (extended forward) that is
  outside the band.
- Vgs = gate node − executed gate offset (VO2/VO3) − FET source node (`p5_cs`/`m12_cs`).

## Verdicts

| Question | Rule |
| --- | --- |
| Servo saturation and windup recovery | **SUPPORTED** if the driver is saturated for ≥ 10 us inside the dead zone and recovery lies in [t_on − 100 us, failed segment start]. **REFUTED** if the driver is never saturated from t_lag to the segment. Otherwise **UNRESOLVED**. |
| Peak slope coincides with driver recovery | **YES** if recovery lies in [t_on − 100 us, failed segment start], else **NO**. |
| Dead zone set by | **PRE-BIAS FLOOR** if the driver is saturated at t_lag, for ≥ 10 us in the dead zone, and recovers in [t_on − 100 us, failed segment start] (the floor-induced error parked the servo until conduction). **MIXED** if it was saturated for ≥ 10 us but recovered earlier, and from recovery to t_on it stays out of the band while Vgs climbs ≥ 0.2 V. **CONDUCTION THRESHOLD** if the driver is never saturated in the dead zone, stays out of the band to t_on, and Vgs climbs ≥ 0.2 V from t_lag to t_on. Otherwise **UNRESOLVED**. |

If the pass pair is not conducting at the failed segment, or no lagging dead zone precedes
conduction inside the window, every verdict is **UNRESOLVED**. If the run's identity control
is NOT REPRODUCED, nothing is evaluated or adopted and the attempt is reported as failed.
Neither outcome adopts a correction; correction candidates go to the manager as a proposal.
