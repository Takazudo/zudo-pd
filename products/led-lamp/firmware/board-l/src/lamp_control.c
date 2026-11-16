#include "lamp_control.h"
void lamp_reset(struct lamp_control *c) {
    if (c) { c->command=0; c->initialized=false; c->latched=false; c->status=LAMP_RESET_OFF; }
}
void lamp_initialize_off(struct lamp_control *c) {
    lamp_reset(c);
    if (c) { c->initialized=true; c->status=LAMP_WAIT_VALID; }
}
static enum lamp_status off(struct lamp_control *c, enum lamp_status status) {
    c->command=0; c->status=status; return status;
}
enum lamp_status lamp_step(struct lamp_control *c, const struct lamp_config *cfg,
                           const struct lamp_samples *s) {
    uint32_t next;
    if (!c) return LAMP_BAD_ARGUMENT;
    if (!cfg || !cfg->increment || cfg->increment>LAMP_FULL ||
        (cfg->recovery!=LAMP_RECOVERY_AUTO && cfg->recovery!=LAMP_RECOVERY_LATCH))
        return off(c,LAMP_UNCONFIGURED);
    if (!c->initialized) return off(c,LAMP_RESET_OFF);
    if (!s) { c->latched=true; return off(c,LAMP_BAD_ARGUMENT); }
    if (c->latched) return off(c,LAMP_LATCHED_OFF);
    if (s->knob>LAMP_FULL || !s->knob_valid || !s->thermal_valid ||
        !s->thermal_allows_light || !s->fresh) {
        c->latched=(cfg->recovery==LAMP_RECOVERY_LATCH);
        return off(c,c->latched ? LAMP_LATCHED_OFF : LAMP_WAIT_VALID);
    }
    if (!s->knob) return off(c,LAMP_WAIT_VALID);
    /* Valid states and increment bound keep this sum <= 2*LAMP_FULL. */
    next=c->command+cfg->increment;
    c->command=next<s->knob ? next : s->knob;
    c->status=c->command==s->knob ? LAMP_READY : LAMP_RAMP;
    return c->status;
}
