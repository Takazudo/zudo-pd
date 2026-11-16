#ifndef ADC_PREPARATION_H
#define ADC_PREPARATION_H
#include <stdbool.h>
#include <stdint.h>
enum adc_operation {
    ADC_QUALIFIED_CLOCK_SUPPLY_RUN_AND_EXCLUSIVE_OWNER,
    ADC_DISABLED_IDLE_NO_PENDING_COMMANDS,
    ADC_CONFIGURE_DISABLED_CALIBRATION_INTERLOCK,
    ADC_DISABLED_CONFIG_READBACK,
    ADC_ENABLE_ADC_REGULATOR,
    ADC_REGULATOR_STABLE_20US_ELAPSED,
    ADC_CALIBRATION_PRECONDITIONS,
    ADC_START_CALIBRATION,
    ADC_CALIBRATION_COMPLETE,
    ADC_RAW_CALFACT,
    ADC_ENABLE_PRECONDITIONS,
    ADC_CLEAR_ADRDY_W1C,
    ADC_ENABLE_NORMAL_ADC,
    ADC_ADRDY,
    ADC_ADEN_SET_ADSTART_CLEAR_INTERLOCK_HELD,
    ADC_CORRECTED_CALFACT,
    ADC_CORRECTED_CALFACT_READBACK,
    ADC_OPERATION_COUNT
};
enum adc_kind {ADC_OBSERVE, ADC_ACTION, ADC_READ, ADC_WRITE, ADC_VERIFY};
enum adc_status {ADC_NEW, ADC_RUNNING, ADC_PREPARED_TRIGGER_UNQUALIFIED, ADC_FAILED};
enum adc_error {ADC_NO_ERROR, ADC_CONFIG_ERROR, ADC_BACKEND_ERROR,
 ADC_INVALID_OBSERVATION, ADC_WAIT_LIMIT, ADC_INVALID_FACTOR,
 ADC_READBACK_MISMATCH, ADC_RESTART_REFUSED, ADC_CHANNEL_CONFIG_FAILURE};
struct adc_reply {bool valid; bool met; int32_t value;};
/* Callback MUST be bounded, exclusive-owner, nonblocking. No MMIO provided.
   valid must be explicitly set for observation/read/verify payloads.
   success return is distinct from payload; false discards plausible data. */
struct adc_backend {
 void *context;
 bool (*transact)(void *, enum adc_kind, enum adc_operation, uint8_t, struct adc_reply *);
};
struct adc_qualification {
 uint32_t observation_budget; /* 1..1000000 CALLS per gate, NOT microseconds */
 bool clock_supply_run_qualified, exclusive_owner, temporary_normal_enable;
};
struct adc_preparation {
 struct adc_backend backend;
 struct adc_qualification qualification;
 enum adc_status status;
 enum adc_error first_error;
 unsigned step;
 uint32_t observations;
 uint8_t factor;
 bool factor_valid, prepared, sample_ready, software_inhibited, restart_refused;
};
/* Zero initialize once; no in-place reset/rebind. Fields private to module.
   Prepared is NOT sample admission. sample_ready remains false forever. */
enum adc_status adc_begin(struct adc_preparation *, const struct adc_backend *, const struct adc_qualification *);
enum adc_status adc_advance(struct adc_preparation *);
const char *adc_operation_name(enum adc_operation);
/* Narrow abort hook for binding's disabled channel configuration. Never grants
   readiness, never overwrites an existing failure, performs no callbacks. */
enum adc_status adc_abort_channel_configuration(struct adc_preparation *);
#endif
