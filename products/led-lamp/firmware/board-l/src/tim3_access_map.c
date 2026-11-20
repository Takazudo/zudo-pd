#include "tim3_access.h"
bool tim3_access_location(enum tim3_preload_register reg,struct tim3_access_location *out)
{
 static const uint8_t offsets[]={0x00,0x08,0x0c,0x18,0x20,0x28,0x2c,0x34};
 if(out)*out=(struct tim3_access_location){0};
 if(!out || (unsigned)reg>=TP_REGISTER_COUNT)return false;
 *out=(struct tim3_access_location){UINT32_C(0x40000400)+offsets[reg],
 (reg==TP_SMCR || reg==TP_CCMR1)?4u:2u,reg==TP_CCR1};
 return (out->address%out->width)==0;
}
