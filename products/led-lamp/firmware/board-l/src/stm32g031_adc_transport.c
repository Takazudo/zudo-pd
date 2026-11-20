/* SOURCE ONLY. Never compile/run without a separately authorized next step. */
#include "stm32g031_adc_transport.h"
#include <limits.h>
#include <stddef.h>

#if !defined(__arm__) || !defined(__ARM_ARCH_6M__)
#error "This source candidate is restricted to the reviewed ARMv6-M target."
#endif

#define STM32G031_ADC_BASE UINT32_C(0x40012400)
#define STM32G031_ADC_ADSTART UINT32_C(0x00000004)

_Static_assert(CHAR_BIT == 8 && sizeof(uint32_t) == 4, "32-bit word access required");
_Static_assert(UINTPTR_MAX >= UINT32_C(0x400124b4), "address representation required");
_Static_assert((STM32G031_ADC_BASE & UINT32_C(3)) == 0, "aligned ADC base required");

static bool fail(struct stm32g031_adc_transport *t, enum stm32g031_adc_error error,
                 enum stm32g031_adc_operation operation, uint32_t offset)
{
    if (t && t->first_error == STM32G031_ADC_NO_ERROR) {
        t->first_error = error;
        t->first_operation = operation;
        t->first_offset = offset;
    }
    return false;
}

static bool allowed_offset(enum adc_register_offset offset)
{
    switch (offset) {
    case ADC_REG_ISR:     return (uint32_t)offset == UINT32_C(0x00);
    case ADC_REG_CR:      return (uint32_t)offset == UINT32_C(0x08);
    case ADC_REG_CFGR1:   return (uint32_t)offset == UINT32_C(0x0c);
    case ADC_REG_CFGR2:   return (uint32_t)offset == UINT32_C(0x10);
    case ADC_REG_SMPR:    return (uint32_t)offset == UINT32_C(0x14);
    case ADC_REG_CHSELR:  return (uint32_t)offset == UINT32_C(0x28);
    case ADC_REG_CALFACT: return (uint32_t)offset == UINT32_C(0xb4);
    default:             return false;
    }
}

static bool evidence_for(struct stm32g031_adc_transport *t,
                         enum stm32g031_adc_operation operation, uint32_t offset,
                         struct adc_field_evidence *out)
{
    struct adc_field_evidence supplied = {0};
    if (out) *out = (struct adc_field_evidence){0};
    if (!t || !out) return fail(t, STM32G031_ADC_ARGUMENT, operation, offset);
    if (t->first_error != STM32G031_ADC_NO_ERROR) return false;
    if (!t->configured || !t->providers.evidence || !t->providers.time)
        return fail(t, STM32G031_ADC_CONFIGURATION, operation, offset);
    if (!t->providers.evidence(t->providers.context, &supplied) ||
        !supplied.valid || !supplied.exclusive_owner || !supplied.clock_supply_qualified ||
        supplied.ownership_epoch != t->epoch || supplied.reset_channel_evidence_epoch != t->epoch)
        return fail(t, STM32G031_ADC_EVIDENCE, operation, offset);
    /* Do not replace no_channel_update_inflight with true: it can be false while
     * polling CCRDY. Existing baseline operations require it at their own boundary.
     */
    *out = supplied;
    return true;
}

static bool get_evidence(void *context, struct adc_field_evidence *out)
{
    return evidence_for(context, STM32G031_ADC_GET_EVIDENCE, 0, out);
}

static bool read_word(void *context, enum adc_register_offset offset, uint32_t *out)
{
    struct stm32g031_adc_transport *t = context;
    struct adc_field_evidence evidence = {0};
    uintptr_t address;
    if (out) *out = 0;
    if (!out) return fail(t, STM32G031_ADC_ARGUMENT, STM32G031_ADC_READ, (uint32_t)offset);
    if (!allowed_offset(offset))
        return fail(t, STM32G031_ADC_OFFSET, STM32G031_ADC_READ, (uint32_t)offset);
    if (!evidence_for(t, STM32G031_ADC_READ, (uint32_t)offset, &evidence)) return false;
    address = (uintptr_t)STM32G031_ADC_BASE + (uintptr_t)(uint32_t)offset;
    *out = *(volatile const uint32_t *)address;
    /* Returning true only describes reaching here. It cannot catch a bus fault,
     * prove peripheral readiness, or bound latency of the volatile load.
     */
    return true;
}

static bool write_word(void *context, enum adc_register_offset offset, uint32_t value)
{
    struct stm32g031_adc_transport *t = context;
    struct adc_field_evidence evidence = {0};
    uintptr_t address;
    if (!allowed_offset(offset))
        return fail(t, STM32G031_ADC_OFFSET, STM32G031_ADC_WRITE, (uint32_t)offset);
    if (offset == ADC_REG_CR && (value & STM32G031_ADC_ADSTART))
        return fail(t, STM32G031_ADC_CONVERSION_FORBIDDEN, STM32G031_ADC_WRITE, (uint32_t)offset);
    if (!evidence_for(t, STM32G031_ADC_WRITE, (uint32_t)offset, &evidence)) return false;
    if (offset == ADC_REG_CFGR2) {
        uint32_t cr,previous;struct adc_operation_descriptor descriptor;
        if (!evidence.operation_clock_plan_qualified || !evidence.no_channel_update_inflight ||
            !evidence.operation_range1_qualified ||
            !adc_operation_describe(&evidence.operation_clock_plan,&descriptor) ||
            (evidence.operation_clock_plan.clock_mode==ADC_OPERATION_PCLK && !evidence.operation_duty50_qualified))
            return fail(t, STM32G031_ADC_OPERATION_CONFIG, STM32G031_ADC_WRITE, (uint32_t)offset);
        cr = *(volatile const uint32_t *)((uintptr_t)STM32G031_ADC_BASE + UINT32_C(0x08));
        if (cr & ~UINT32_C(0x10000000))
            return fail(t, STM32G031_ADC_OPERATION_CONFIG, STM32G031_ADC_WRITE, (uint32_t)offset);
        previous = *(volatile const uint32_t *)((uintptr_t)STM32G031_ADC_BASE + UINT32_C(0x10));
        if (!adc_operation_cfgr2_write_allowed(&evidence.operation_clock_plan,
            evidence.operation_range1_qualified,evidence.operation_duty50_qualified,cr,previous,value))
            return fail(t, STM32G031_ADC_OPERATION_CONFIG, STM32G031_ADC_WRITE, (uint32_t)offset);
    }
    address = (uintptr_t)STM32G031_ADC_BASE + (uintptr_t)(uint32_t)offset;
    *(volatile uint32_t *)address = value;
    /* Exactly the requested word, no read-modify-write or hidden initialization.
     * No bus acknowledgement/fault recovery or bounded physical latency is claimed.
     */
    return true;
}

static bool get_time(void *context, struct adc_time_evidence *out)
{
    struct stm32g031_adc_transport *t = context;
    struct adc_field_evidence evidence = {0};
    struct adc_time_evidence supplied = {0};
    if (out) *out = (struct adc_time_evidence){0};
    if (!out) return fail(t, STM32G031_ADC_ARGUMENT, STM32G031_ADC_GET_TIME, 0);
    if (!evidence_for(t, STM32G031_ADC_GET_TIME, 0, &evidence)) return false;
    if (!t->providers.time(t->providers.context, &supplied) || !supplied.valid ||
        !supplied.qualified_monotonic || supplied.epoch != t->epoch ||
        supplied.earliest_us > supplied.latest_us)
        return fail(t, STM32G031_ADC_TIME, STM32G031_ADC_GET_TIME, 0);
    *out = supplied; /* no fabricated timestamp; V38 checks nondecreasing bounds */
    return true;
}

bool stm32g031_adc_transport_initialize(struct stm32g031_adc_transport *t,
    const struct stm32g031_adc_providers *providers, uint64_t epoch)
{
    if (!t) return false;
    if (t->configured || t->first_error != STM32G031_ADC_NO_ERROR)
        return fail(t, STM32G031_ADC_CONFIGURATION, STM32G031_ADC_INITIALIZE, 0);
    if (!providers || !providers->evidence || !providers->time || !epoch)
        return fail(t, STM32G031_ADC_CONFIGURATION, STM32G031_ADC_INITIALIZE, 0);
    t->providers = *providers;
    t->epoch = epoch;
    t->configured = true;
    return true;
}

struct adc_field_transport stm32g031_adc_register_transport(struct stm32g031_adc_transport *t)
{
    struct adc_field_transport transport = {t, get_evidence, read_word, write_word};
    return transport;
}

struct adc_preparation_transport stm32g031_adc_preparation_transport(struct stm32g031_adc_transport *t)
{
    struct adc_preparation_transport transport = {stm32g031_adc_register_transport(t), get_time};
    return transport;
}
