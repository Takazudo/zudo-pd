#ifndef BOARD_ADC_H
#define BOARD_ADC_H
#include <stdbool.h>
#include <stdint.h>
#include "board_samples.h"
/* ADC1 on PA0 (BRIGHT_ADC, IN0) and PA4 (NTC_SENSE, IN4). delay_ms must be a
 * working millisecond delay (SysTick running). Returns false on any timeout. */
bool board_adc_init(void (*delay_ms)(uint32_t));
/* raw_source.convert: one software-started scan IN0 then IN4. */
bool board_adc_convert(void *, struct raw_pair *);
#endif
