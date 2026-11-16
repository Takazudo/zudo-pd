#include "input_conversion.h"
bool knob_request(uint32_t raw, const struct knob_calibration *cal, uint32_t *out) {
    uint32_t span, position;
    if (!out) return false;
    *out=0;
    if (!cal || !cal->configured || !cal->adc_max || raw>cal->adc_max ||
        cal->off_code>cal->adc_max || cal->full_code>cal->adc_max ||
        cal->off_code==cal->full_code) return false;
    if (cal->full_code>cal->off_code) {
        if (raw<=cal->off_code) return true;
        if (raw>=cal->full_code) { *out=LAMP_FULL; return true; }
        span=cal->full_code-cal->off_code; position=raw-cal->off_code;
    } else {
        if (raw>=cal->off_code) return true;
        if (raw<=cal->full_code) { *out=LAMP_FULL; return true; }
        span=cal->off_code-cal->full_code; position=cal->off_code-raw;
    }
    *out=(uint32_t)(((uint64_t)position*LAMP_FULL)/span);
    return true;
}
bool ntc_resistance(uint32_t sense_uv, uint32_t supply_uv,
                    uint32_t pullup_ohm, double *out_ohm) {
    if (!out_ohm) return false;
    *out_ohm=0;
    if (!pullup_ohm || !sense_uv || sense_uv>=supply_uv) return false;
    *out_ohm=(double)pullup_ohm*(double)sense_uv/(double)(supply_uv-sense_uv);
    return true;
}
