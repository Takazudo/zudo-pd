#ifndef INPUT_CONVERSION_H
#define INPUT_CONVERSION_H
#include "lamp_control.h"
struct knob_calibration {
    bool configured;
    uint32_t adc_max, off_code, full_code;
};
/* Calibrated electrical request, NOT a linear mechanical-angle guarantee.
   Explicit endpoints permit either orientation. Outside endpoints saturates;
   outside ADC range is invalid. Failure clears output. No defaults. */
bool knob_request(uint32_t raw, const struct knob_calibration *cal, uint32_t *out);
/* RT1 to ground; R26 to supply. Inputs in microvolts and ohms.
   Caller must establish ADC reference/scaling/freshness and actual supply.
   Interior divider inversion only: rail codes are invalid, not fault diagnoses.
   No temperature, thermal_allow or sensor-valid decision is produced. */
bool ntc_resistance(uint32_t sense_uv, uint32_t supply_uv,
                    uint32_t pullup_ohm, double *out_ohm);
#endif
