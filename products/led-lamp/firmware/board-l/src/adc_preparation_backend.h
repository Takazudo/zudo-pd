#ifndef ADC_PREPARATION_BACKEND_H
#define ADC_PREPARATION_BACKEND_H
#include "adc_field_backend.h"
/* Certified bounds around the actual sample instant, in microseconds.
   Includes quantization/clock uncertainty; earliest<=latest, same epoch.
   Exact equality is only for genuinely exact evidence (synthetic tests here). */
struct adc_time_evidence {uint64_t epoch,earliest_us,latest_us;bool valid,qualified_monotonic;};
struct adc_preparation_transport {
 struct adc_field_transport registers;
 bool (*time)(void *,struct adc_time_evidence *); /* same context; bounded */
};
enum adc_preparation_backend_error {ADC_PREP_NO_ERROR,ADC_PREP_CONFIG,ADC_PREP_CONTEXT,
 ADC_PREP_READ,ADC_PREP_WRITE,ADC_PREP_STATE,ADC_PREP_TIME,ADC_PREP_REQUEST};
struct adc_preparation_adapter {
 struct adc_preparation_transport transport;
 uint64_t epoch,regulator_started,last_time;
 bool configured,time_started,elapsed_qualified,calibration_started,calibration_completed;
 enum adc_preparation_backend_error first_error;
 enum adc_operation first_operation;
 enum adc_register_offset first_register;
 bool operation_config_enabled;struct adc_operation_config operation_config;
 struct adc_operation_descriptor operation_descriptor;
 bool write_effect_possible,first_write_effect_possible;
 enum adc_register_offset last_write_register;uint32_t last_write_value;
};
bool adc_preparation_adapter_initialize(struct adc_preparation_adapter *,
 const struct adc_preparation_transport *,uint64_t);
/* Explicit opt-in only; legacy initialize retains old preparation-only path.
 * No ADC acquisition permission, default clock or configuration during init. */
bool adc_preparation_adapter_initialize_operation(struct adc_preparation_adapter *,
 const struct adc_preparation_transport *,uint64_t,const struct adc_operation_config *);
struct adc_backend adc_preparation_adapter_backend(struct adc_preparation_adapter *);
#endif
