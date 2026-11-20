/* Host tests: V72 lamp_app wired to lamp_target.c through a fake CTRL port.
 * "Light-capable" means the fake pin is on the timer (AF) with a non-zero CCR. */
#include <stdio.h>
#include <stdlib.h>
#include "board_l_proposal.h"

enum pin { PIN_RESET, PIN_GPIO_LOW, PIN_AF };
static struct { enum pin pin; uint32_t ccr, period, inits, offs, max_ccr; } hw;

static void fake_force_off(void) { hw.pin = PIN_GPIO_LOW; hw.ccr = 0; hw.offs++; }
static void fake_init_zero(uint32_t period) { fake_force_off(); hw.period = period; hw.ccr = 0; hw.pin = PIN_AF; hw.inits++; }
static void fake_write(uint32_t ccr)
{
    if (hw.pin != PIN_AF) { fprintf(stderr, "CCR write while pin not on timer\n"); exit(2); }
    hw.ccr = ccr;
    if (ccr > hw.max_ccr) hw.max_ccr = ccr;
}
static int light(void) { return hw.pin == PIN_AF && hw.ccr > 0; }

static struct lamp_samples g_s;
static enum board_l_result g_read_result;
static enum board_l_result fake_read(void *ctx, struct lamp_samples *out)
{
    (void)ctx;
    *out = g_s;
    return g_read_result;
}
static const struct ctrl_port port = {fake_force_off, fake_init_zero, fake_write};
static const struct lamp_config policy = {LAMP_RAMP_INCREMENT, LAMP_RECOVERY_LATCH};
/* Full ramp plus margin, so tests follow LAMP_RAMP_INCREMENT. */
#define SETTLE_TICKS (LAMP_FULL / LAMP_RAMP_INCREMENT + 200u)
static int failures, checks;
#define CHECK(c) do { checks++; if (!(c)) { failures++; printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #c); } } while (0)

static void good(uint32_t knob)
{
    g_s = (struct lamp_samples){knob, true, true, true, true};
    g_read_result = BOARD_L_OK;
}

struct rig { struct lamp_target t; struct lamp_app app; struct lamp_app_io io; struct board_l_config cfg; };
static void rig_init(struct rig *r, int with_samples, uint32_t full_ccr)
{
    struct sample_port sp = {0, fake_read, NULL};
    hw = (__typeof__(hw)){0};
    *r = (struct rig){0};
    CHECK(lamp_target_bind(&r->t, &port, with_samples ? &sp : NULL));
    r->io = lamp_target_io(&r->t);
    r->cfg = board_l_proposed_config(full_ccr);
}
static void ticks(struct rig *r, int n, int expect_light_never)
{
    for (int i = 0; i < n; i++) {
        (void)lamp_app_tick(&r->app, &policy);
        if (expect_light_never) CHECK(!light());
    }
}

static void test_startup_off(void)
{
    struct rig r;
    rig_init(&r, 1, CTRL_FULL_CCR);
    CHECK(hw.pin == PIN_GPIO_LOW);                 /* bind forces OFF */
    good(LAMP_FULL);
    ticks(&r, 5, 1);                               /* not initialized: stays OFF */
    CHECK(hw.inits == 0);
    struct lamp_app_report rep = lamp_app_initialize(&r.app, &r.io, NULL);
    CHECK(rep.status == LAMP_APP_UNCONFIGURED && !light() && hw.inits == 0);
    struct board_l_config bad = r.cfg; bad.ctrl.positive_full_ccr = CTRL_PERIOD_TICKS + 1;
    rep = lamp_app_initialize(&r.app, &r.io, &bad);
    CHECK(rep.status != LAMP_APP_CORE_OFF && !light());
    ticks(&r, 5, 1);
    struct rig r2;
    rig_init(&r2, 1, CTRL_FULL_CCR);
    rep = lamp_app_initialize(&r2.app, &r2.io, &r2.cfg);
    CHECK(rep.status == LAMP_APP_CORE_OFF && !light() && hw.inits == 1 && hw.period == CTRL_PERIOD_TICKS);
    /* No sample source at all (current target build): never lights. */
    struct rig r3;
    rig_init(&r3, 0, CTRL_FULL_CCR);
    (void)lamp_app_initialize(&r3.app, &r3.io, &r3.cfg);
    ticks(&r3, 2000, 1);
}

static void running(struct rig *r, uint32_t full)
{
    rig_init(r, 1, full);
    (void)lamp_app_initialize(&r->app, &r->io, &r->cfg);
    good(LAMP_FULL);
    ticks(r, SETTLE_TICKS, 0);
    CHECK(light());
}

static void test_knob_zero_off(void)
{
    struct rig r;
    running(&r, CTRL_FULL_CCR);
    good(0);
    ticks(&r, 1, 0);
    CHECK(!light());
    ticks(&r, 50, 1);
    good(LAMP_FULL / 2);                           /* knob zero is not a latch */
    ticks(&r, SETTLE_TICKS, 0);
    CHECK(light());
}

static void test_thermal_invalid_off(void)
{
    struct rig r;
    running(&r, CTRL_FULL_CCR);
    g_s.thermal_valid = false;
    ticks(&r, 1, 0);
    CHECK(!light());
    good(LAMP_FULL);                               /* latched until re-initialize */
    ticks(&r, 200, 1);
    running(&r, CTRL_FULL_CCR);
    g_s.thermal_allows_light = false;
    ticks(&r, 1, 0);
    CHECK(!light());
    good(LAMP_FULL);
    ticks(&r, 200, 1);
    CHECK(lamp_app_initialize(&r.app, &r.io, &r.cfg).status == LAMP_APP_CORE_OFF);
    ticks(&r, SETTLE_TICKS, 0);
    CHECK(light());                                /* explicit re-init recovers */
}

static void test_fault_off(void)
{
    struct rig r;
    running(&r, CTRL_FULL_CCR);
    g_read_result = BOARD_L_IO_ERROR;              /* adapter fault */
    ticks(&r, 1, 0);
    CHECK(!light());
    g_read_result = BOARD_L_OK;
    ticks(&r, 200, 1);
    running(&r, CTRL_FULL_CCR);
    g_s.fresh = false;                             /* stale sample */
    ticks(&r, 1, 0);
    CHECK(!light());
    running(&r, CTRL_FULL_CCR);
    g_s.knob = LAMP_FULL + 1;                      /* out-of-range input */
    ticks(&r, 1, 0);
    CHECK(!light());
    running(&r, CTRL_FULL_CCR);
    r.io.force_off(r.io.context);                  /* fault-handler style OFF */
    CHECK(!light() && hw.pin == PIN_GPIO_LOW);
}

static void test_ceiling(void)
{
    struct rig r;
    running(&r, CTRL_FULL_CCR);
    CHECK(hw.max_ccr == CTRL_FULL_CCR);
    good(1);
    ticks(&r, SETTLE_TICKS, 0);
    CHECK(light() && hw.ccr == CTRL_MIN_CCR);      /* lowest positive -> floor */
}

static void test_adapter_direct(void)
{
    struct rig r;
    rig_init(&r, 1, CTRL_FULL_CCR);
    CHECK(r.io.apply_command(r.io.context, LAMP_FULL) == BOARD_L_UNCONFIGURED && !light());
    CHECK(r.io.initialize_off(r.io.context, NULL) == BOARD_L_UNCONFIGURED && !light());
    CHECK(r.io.initialize_off(r.io.context, &r.cfg) == BOARD_L_OK && !light());
    CHECK(r.io.apply_command(r.io.context, LAMP_FULL + 1) == BOARD_L_IO_ERROR && hw.pin == PIN_GPIO_LOW);
    uint32_t inits = hw.inits;
    CHECK(r.io.apply_command(r.io.context, LAMP_FULL) == BOARD_L_OK);
    CHECK(hw.inits == inits + 1 && hw.ccr == CTRL_FULL_CCR); /* re-handover at 0 % first */
    CHECK(r.io.apply_command(r.io.context, 0) == BOARD_L_OK && !light());
}

static void test_default_ceiling_and_graded_off(void)
{
    struct rig r;
    /* The single ceiling constant: default protects an unchanged RS1 = 200 mOhm board. */
#ifndef BOARD_L_TEST_CEILING_OVERRIDE
    CHECK(CTRL_FULL_CCR == 2407u);
#endif
    CHECK((uint64_t)CTRL_FULL_CCR * 10000u / CTRL_PERIOD_TICKS <= 7522u || CTRL_FULL_CCR != 2407u);
    /* Register-write check (board_ctrl_write_ccr) against the compile-time ceiling. */
    CHECK(ctrl_ccr_within_ceiling(0u) && ctrl_ccr_within_ceiling(CTRL_FULL_CCR));
    CHECK(!ctrl_ccr_within_ceiling(CTRL_FULL_CCR + 1u) && !ctrl_ccr_within_ceiling(UINT32_MAX));
    /* Graded (thermal gain) path with no graded reader: UNCONFIGURED, never lights. */
    rig_init(&r, 1, CTRL_FULL_CCR);
    struct lamp_app_gain_path gain = lamp_target_gain_path();
    struct lamp_app_report rep = lamp_app_initialize_with_thermal_gain(&r.app, &r.io, &r.cfg, NULL, &gain);
    CHECK(rep.status == LAMP_APP_CORE_OFF && !light());
    good(LAMP_FULL);
    ticks(&r, SETTLE_TICKS, 1);
}

int main(void)
{
    test_default_ceiling_and_graded_off();
    test_adapter_direct();
    test_startup_off();
    test_knob_zero_off();
    test_thermal_invalid_off();
    test_fault_off();
    test_ceiling();
    printf("%s %d checks, %d failures (lamp_target off-by-default contract)\n",
           failures ? "FAIL" : "PASS", checks, failures);
    return failures ? 1 : 0;
}
