#include "acquisition_fixed_word.h"
bool acquisition_word_read_location(enum acquisition_register reg,struct acquisition_location *out)
{
 struct acquisition_location location={0};
 if(out)*out=(struct acquisition_location){0};
 if(!out || !acquisition_register_location(reg,&location) || location.width!=4 || (location.address&3u))return false;
 *out=location;return true;
}
bool acquisition_word_store_location(enum acquisition_store operation,uint32_t value,struct acquisition_location *out)
{
 enum acquisition_register reg;
 if(out)*out=(struct acquisition_location){0};
 if(operation==ACQ_START_COMMAND && value==UINT32_C(0x10000004))reg=ACQ_CR;
 else if(operation==ACQ_CLEAR_EOS && value==UINT32_C(8))reg=ACQ_ISR;
 else return false;
 return acquisition_word_read_location(reg,out);
}
