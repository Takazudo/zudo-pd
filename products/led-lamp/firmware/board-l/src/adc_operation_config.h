#ifndef ADC_OPERATION_CONFIG_H
#define ADC_OPERATION_CONFIG_H
#include <stdint.h>
#include <stdbool.h>
enum adc_operation_clock_mode {ADC_OPERATION_CLOCK_UNSELECTED,
 ADC_OPERATION_ASYNC,ADC_OPERATION_PCLK_DIV2,ADC_OPERATION_PCLK_DIV4,ADC_OPERATION_PCLK};
struct adc_operation_config {
 enum adc_operation_clock_mode clock_mode;
 uint32_t source_min_hz,source_max_hz;bool bounds_supplied;
};
struct adc_operation_descriptor {
 uint32_t cfgr1_mask,cfgr1_value,cfgr2_mask,cfgr2_value;
 uint32_t adc_min_hz,adc_max_hz;
};
/* Pure encoding/range check only. Source bounds are declarations; independent
 * clock-plan evidence must qualify their truth/Range1/duty/stability at runtime. */
bool adc_operation_describe(const struct adc_operation_config *,struct adc_operation_descriptor *);
bool adc_operation_cfgr2_valid(uint32_t);
bool adc_operation_cfgr2_write_allowed(const struct adc_operation_config *,bool range1,bool duty50,
 uint32_t cr,uint32_t previous,uint32_t requested);
#endif
