#include <stddef.h>
#include "board_samples.h"

enum board_l_result ntc_thermal(void *ctx, uint32_t raw, struct sample_thermal *out)
{
    (void)ctx;
    if (!out)
        return BOARD_L_IO_ERROR;
    *out = (struct sample_thermal){0};
    if (raw >= NTC_OPEN_CODE || raw > KNOB_ADC_MAX)
        return BOARD_L_OK;                      /* unknown: open or out of range */
    out->known = true;
    out->allows_light = raw > NTC_CRITICAL_CODE;
    return BOARD_L_OK;
}

enum board_l_result ntc_gain(void *ctx, uint32_t raw, struct thermal_gain *out)
{
    (void)ctx;
    if (!out)
        return BOARD_L_IO_ERROR;
    *out = (struct thermal_gain){0};
    if (raw >= NTC_OPEN_CODE || raw <= NTC_CRITICAL_CODE)
        return BOARD_L_OK;                      /* invalid gain */
    out->valid = true;
    out->value = raw >= NTC_DERATE_CODE ? LAMP_FULL
        : (uint32_t)((uint64_t)(raw - NTC_CRITICAL_CODE) * LAMP_FULL /
                     (NTC_DERATE_CODE - NTC_CRITICAL_CODE));
    return BOARD_L_OK;
}

static enum board_l_result acquire(void *ctx, struct sample_frame *f)
{
    struct board_samples *s = ctx;
    struct raw_pair p = {0};
    uint64_t at;
    *f = (struct sample_frame){0};
    at = s->source.now(s->source.context);      /* capture tag = conversion start */
    if (!s->source.convert(s->source.context, &p) || !p.ok)
        return BOARD_L_IO_ERROR;
    s->sequence++;
    f->knob = (struct sample_channel){p.knob, s->sequence, at, true};
    f->thermal = (struct sample_channel){p.ntc, s->sequence, at, true};
    return BOARD_L_OK;
}

static enum board_l_result now_clock(void *ctx, struct sample_clock *c)
{
    struct board_samples *s = ctx;
    *c = (struct sample_clock){s->source.now(s->source.context), true};
    return BOARD_L_OK;
}

enum board_l_result board_samples_init(struct board_samples *s, const struct raw_source *src)
{
    static const struct sample_adapter_config cfg = {
        true, true, SAMPLE_MAX_AGE_TICKS,
        {true, KNOB_ADC_MAX, KNOB_OFF_CODE, KNOB_FULL_CODE}, KNOB_WINDOW};
    struct sample_adapter_hooks hooks;
    struct sample_gain_config gain = {true, NULL, ntc_gain};
    if (!s || !src || !src->convert || !src->now)
        return BOARD_L_UNCONFIGURED;
    *s = (struct board_samples){0};
    s->source = *src;
    hooks = (struct sample_adapter_hooks){s, acquire, now_clock, ntc_thermal};
    return sample_adapter_initialize_graded(&s->adapter, &cfg, &hooks, &gain);
}

enum board_l_result board_samples_read(void *ctx, struct lamp_samples *out)
{
    struct board_samples *s = ctx;
    if (out)
        *out = (struct lamp_samples){0};
    return s ? sample_adapter_read(&s->adapter, out) : BOARD_L_UNCONFIGURED;
}

enum board_l_result board_samples_read_graded(void *ctx, struct lamp_samples *out, struct thermal_gain *g)
{
    struct board_samples *s = ctx;
    if (out)
        *out = (struct lamp_samples){0};
    if (g)
        *g = (struct thermal_gain){0};
    return s ? sample_adapter_read_graded(&s->adapter, out, g) : BOARD_L_UNCONFIGURED;
}
