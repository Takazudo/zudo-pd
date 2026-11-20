#ifndef THERMAL_GAIN_H
#define THERMAL_GAIN_H
#include "lamp_control.h"
/* Integer normalized gain, NOT temperature. No NaN/Inf representation: an
   external floating producer must validate BEFORE conversion into this API. */
struct thermal_gain {uint32_t value;bool valid;};
bool thermal_gain_apply(uint32_t input,const struct thermal_gain *,uint32_t *output);
#endif
