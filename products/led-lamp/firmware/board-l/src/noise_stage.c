#include "noise_stage.h"
#include <stddef.h>

void noise_reset(struct noise_stage *s) {
    if (s) { s->slow_state=0; s->fast_state=0; }
}
enum noise_status noise_initialize(struct noise_stage *s,const struct noise_config *cfg,
                                   const struct noise_source *rng) {
    struct noise_config c={0};struct noise_source r={0};
    if (!s) return NOISE_BAD_ARGUMENT;
    if (cfg) c=*cfg;
    if (rng) r=*rng;
    *s=(struct noise_stage){0};
    if (!cfg || !rng || !r.read_pair || !c.configured || !c.denominator ||
        c.denominator>LAMP_FULL || c.slow_alpha>c.denominator || c.fast_alpha>c.denominator ||
        c.slow_depth>c.denominator || c.fast_depth>c.denominator ||
        c.noise_min>0 || c.noise_max<0 || c.noise_min<-(int32_t)LAMP_FULL ||
        c.noise_max>(int32_t)LAMP_FULL) return NOISE_UNCONFIGURED;
    s->config=c;s->source=r;s->initialized=true;return NOISE_READY;
}
static int32_t filtered(int32_t state,int32_t sample,uint32_t alpha,uint32_t denominator) {
    return (int32_t)((int64_t)state+((int64_t)sample-state)*alpha/denominator);
}
enum noise_status noise_step(struct noise_stage *s,const struct noise_input *in,struct noise_output *out) {
    struct noise_pair pair={0};
    int64_t value;
    if (out) *out=(struct noise_output){0};
    if (!s || !out) { noise_reset(s);return NOISE_BAD_ARGUMENT; }
    if (!s->initialized) { noise_reset(s);return NOISE_UNCONFIGURED; }
    if (!in || !in->base_valid || in->base>LAMP_FULL) {
        noise_reset(s);return NOISE_INPUT_INVALID;
    }
    if (!in->startup_complete || !in->frame_qualified) {noise_reset(s);return NOISE_INELIGIBLE;}
    if (!in->base) {noise_reset(s);out->valid=true;return NOISE_OFF;}
    if (!s->source.read_pair(s->source.context,&pair) || !pair.complete ||
        pair.slow<s->config.noise_min || pair.slow>s->config.noise_max ||
        pair.fast<s->config.noise_min || pair.fast>s->config.noise_max) {
        noise_reset(s);return NOISE_RNG_ERROR;
    }
    s->slow_state=filtered(s->slow_state,pair.slow,s->config.slow_alpha,s->config.denominator);
    s->fast_state=filtered(s->fast_state,pair.fast,s->config.fast_alpha,s->config.denominator);
    value=(int64_t)in->base+(int64_t)s->slow_state*s->config.slow_depth/s->config.denominator
                         +(int64_t)s->fast_state*s->config.fast_depth/s->config.denominator;
    if (value<0) value=0;
    if (value>LAMP_FULL) value=LAMP_FULL;
    out->value=(uint32_t)value;out->valid=true;
    return out->value?NOISE_VALID:NOISE_OFF;
}
