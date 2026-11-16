#include "thermal_gain.h"
bool thermal_gain_apply(uint32_t input,const struct thermal_gain *gain,uint32_t *out) {
    if(!out)return false;
    *out=0;
    if(input>LAMP_FULL || !gain || !gain->valid || gain->value>LAMP_FULL)return false;
    *out=(uint32_t)(((uint64_t)input*gain->value)/LAMP_FULL);
    return true;
}
