#include "lamp_target.h"

static enum board_l_result target_initialize_off(void *ctx, const struct board_l_config *cfg)
{
    struct lamp_target *t = ctx;
    if (!t || !t->bound)
        return BOARD_L_UNCONFIGURED;
    t->port.force_off();
    t->output_enabled = false;
    t->initialized = false;
    if (!cfg || ctrl_timer_initialize(&t->mapper, &cfg->ctrl) != CTRL_TIMER_CONDITIONAL)
        return BOARD_L_UNCONFIGURED;
    t->port.pwm_init_zero(t->mapper.config.period_ticks);
    t->output_enabled = true;
    t->initialized = true;
    return BOARD_L_OK;
}

static enum board_l_result target_read(void *ctx, struct lamp_samples *out)
{
    struct lamp_target *t = ctx;
    if (out)
        *out = (struct lamp_samples){0};
    if (!t || !out || !t->samples.read)
        return BOARD_L_UNCONFIGURED;
    return t->samples.read(t->samples.context, out);
}

static enum board_l_result target_read_graded(void *ctx, struct lamp_samples *out, struct thermal_gain *g)
{
    struct lamp_target *t = ctx;
    if (out)
        *out = (struct lamp_samples){0};
    if (g)
        *g = (struct thermal_gain){0};
    if (!t || !out || !g || !t->samples.read_graded)
        return BOARD_L_UNCONFIGURED;
    return t->samples.read_graded(t->samples.context, out, g);
}

static void target_force_off(void *ctx)
{
    struct lamp_target *t = ctx;
    if (!t || !t->bound)
        return;
    t->port.force_off();
    t->output_enabled = false;
}

static enum board_l_result target_apply(void *ctx, uint32_t command)
{
    struct lamp_target *t = ctx;
    struct ctrl_timer_result m;
    enum ctrl_timer_status st;
    if (!t || !t->bound)
        return BOARD_L_UNCONFIGURED;
    if (!t->initialized) {
        target_force_off(t);
        return BOARD_L_UNCONFIGURED;
    }
    st = ctrl_timer_map(&t->mapper, command, &m);
    if (st == CTRL_TIMER_OFF && m.ccr_valid) {
        if (t->output_enabled)
            t->port.write_ccr(0u);
        return BOARD_L_OK;
    }
    if (st != CTRL_TIMER_CONDITIONAL || !m.ccr_valid ||
        m.ccr > t->mapper.config.positive_full_ccr) {
        target_force_off(t);
        return BOARD_L_IO_ERROR;
    }
    if (!t->output_enabled) {
        t->port.pwm_init_zero(t->mapper.config.period_ticks);
        t->output_enabled = true;
    }
    t->port.write_ccr(m.ccr);
    return BOARD_L_OK;
}

bool lamp_target_bind(struct lamp_target *t, const struct ctrl_port *port, const struct sample_port *samples)
{
    if (!t || t->bound || !port || !port->force_off || !port->pwm_init_zero || !port->write_ccr)
        return false;
    *t = (struct lamp_target){0};
    t->port = *port;
    if (samples)
        t->samples = *samples;
    t->bound = true;
    t->port.force_off();
    return true;
}

struct lamp_app_io lamp_target_io(struct lamp_target *t)
{
    return (struct lamp_app_io){t, target_initialize_off, target_read, target_apply, target_force_off};
}

struct lamp_app_gain_path lamp_target_gain_path(void)
{
    return (struct lamp_app_gain_path){true, target_read_graded};
}
