#ifndef STM32G031_ADC_TRANSPORT_H
#define STM32G031_ADC_TRANSPORT_H

#include "adc_preparation_backend.h"

/* SOURCE CANDIDATE ONLY: object checks permitted; NEVER executed.
 * Providers attest real, externally qualified facts; no provider is implemented.
 * One owner, no concurrent/reentrant access, fixed context and epoch lifetime.
 */
struct stm32g031_adc_providers {
    void *context;
    bool (*evidence)(void *, struct adc_field_evidence *);
    bool (*time)(void *, struct adc_time_evidence *);
};

enum stm32g031_adc_error {
    STM32G031_ADC_NO_ERROR,
    STM32G031_ADC_CONFIGURATION,
    STM32G031_ADC_OFFSET,
    STM32G031_ADC_ARGUMENT,
    STM32G031_ADC_EVIDENCE,
    STM32G031_ADC_TIME,
    STM32G031_ADC_CONVERSION_FORBIDDEN,
    STM32G031_ADC_OPERATION_CONFIG
};

enum stm32g031_adc_operation {
    STM32G031_ADC_INITIALIZE,
    STM32G031_ADC_READ,
    STM32G031_ADC_WRITE,
    STM32G031_ADC_GET_EVIDENCE,
    STM32G031_ADC_GET_TIME
};

struct stm32g031_adc_transport {
    struct stm32g031_adc_providers providers;
    uint64_t epoch;
    bool configured;
    enum stm32g031_adc_error first_error;
    enum stm32g031_adc_operation first_operation;
    uint32_t first_offset;
};

/* Zero initialize once. Copies callbacks; never reads/writes MMIO or initializes
 * clock/reset/peripherals. Both external providers required. No rearm/reset API.
 */
bool stm32g031_adc_transport_initialize(struct stm32g031_adc_transport *,
    const struct stm32g031_adc_providers *, uint64_t);

/* Both factories retain the SAME transport context. No operation is performed.
 * Higher field/preparation adapters keep their existing register semantics.
 */
struct adc_field_transport stm32g031_adc_register_transport(struct stm32g031_adc_transport *);
struct adc_preparation_transport stm32g031_adc_preparation_transport(struct stm32g031_adc_transport *);

#endif
