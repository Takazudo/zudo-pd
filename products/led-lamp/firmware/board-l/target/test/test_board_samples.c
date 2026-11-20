/* Host tests: ADC sample source -> V72 sample_adapter (graded) -> lamp_app ->
 * lamp_target -> fake CTRL port. Every OFF path of the sample chain. */
#include <stdio.h>
#include <stdlib.h>
#include "board_l_proposal.h"
#include "board_samples.h"

enum pin { PIN_RESET, PIN_GPIO_LOW, PIN_AF };
static struct { enum pin pin; uint32_t ccr, max_ccr; } hw;
static void fake_force_off(void) { hw.pin = PIN_GPIO_LOW; hw.ccr = 0; }
static void fake_init_zero(uint32_t period) { (void)period; fake_force_off(); hw.pin = PIN_AF; }
static void fake_write(uint32_t ccr)
{
    if (hw.pin != PIN_AF) { fprintf(stderr, "CCR write while pin not on timer\n"); exit(2); }
    hw.ccr = ccr;
    if (ccr > hw.max_ccr) hw.max_ccr = ccr;
}
static int light(void) { return hw.pin == PIN_AF && hw.ccr > 0; }

/* Fake ADC + clock. */
static struct { uint32_t knob, ntc; bool fail, not_ok; uint64_t t; uint32_t jump, rollback; } adc;
static bool fake_convert(void *ctx, struct raw_pair *p)
{
    (void)ctx;
    *p = (struct raw_pair){adc.knob, adc.ntc, !adc.not_ok};
    adc.t += adc.jump;                    /* time spent converting */
    return !adc.fail;
}
static uint64_t fake_now(void *ctx)
{
    (void)ctx;
    if (adc.rollback) { adc.rollback = 0; adc.t -= 5; }
    return adc.t;
}

static int failures, checks;
#define CHECK(c) do { checks++; if (!(c)) { failures++; printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #c); } } while (0)
#define SETTLE (LAMP_FULL / LAMP_RAMP_INCREMENT + 200u)
#define NTC_25C 372u

struct rig { struct board_samples s; struct lamp_target t; struct lamp_app app; struct lamp_app_io io; };
static const struct ctrl_port port = {fake_force_off, fake_init_zero, fake_write};
static const struct lamp_config policy = {LAMP_RAMP_INCREMENT, LAMP_RECOVERY_LATCH};

static void rig_start(struct rig *r, uint32_t knob, uint32_t ntc)
{
    static const struct raw_source src = {NULL, fake_convert, fake_now};
    struct sample_port sp;
    struct board_l_config cfg = board_l_proposed_config(CTRL_FULL_CCR);
    struct lamp_app_gain_path gain = lamp_target_gain_path();
    hw = (__typeof__(hw)){0};
    adc = (__typeof__(adc)){knob, ntc, false, false, 100, 0, 0};
    *r = (struct rig){0};
    CHECK(board_samples_init(&r->s, &src) == BOARD_L_OK);
    sp = (struct sample_port){&r->s, board_samples_read, board_samples_read_graded};
    CHECK(lamp_target_bind(&r->t, &port, &sp));
    r->io = lamp_target_io(&r->t);
    CHECK(lamp_app_initialize_with_thermal_gain(&r->app, &r->io, &cfg, NULL, &gain).status == LAMP_APP_CORE_OFF);
    CHECK(!light());
}
static void run(struct rig *r, unsigned n)
{
    for (unsigned i = 0; i < n; i++) {
        adc.t++;
        (void)lamp_app_tick(&r->app, &policy);
        CHECK(hw.ccr <= CTRL_FULL_CCR);
    }
}

static void test_normal_and_ceiling(void)
{
    struct rig r;
    rig_start(&r, KNOB_FULL_CODE, NTC_25C);
    run(&r, 1);
    CHECK(hw.ccr < CTRL_FULL_CCR);                /* ramps, no step to full */
    run(&r, SETTLE);
    CHECK(light() && hw.ccr == CTRL_FULL_CCR && hw.max_ccr == CTRL_FULL_CCR);
}

static void test_knob_off(void)
{
    struct rig r;
    rig_start(&r, KNOB_FULL_CODE, NTC_25C);
    run(&r, SETTLE);
    adc.knob = KNOB_OFF_CODE;                     /* at/below off code -> 0 -> OFF */
    run(&r, SETTLE);
    CHECK(!light() && hw.pin == PIN_GPIO_LOW);
    adc.knob = 0;
    run(&r, 20);
    CHECK(!light());
    adc.knob = KNOB_FULL_CODE;                    /* knob zero is not a fault */
    run(&r, SETTLE);
    CHECK(light());
}

static void latched_off_after(struct rig *r, const char *what)
{
    run(r, 3);
    if (light() || hw.pin != PIN_GPIO_LOW)
        printf("  (%s)\n", what);
    CHECK(!light() && hw.pin == PIN_GPIO_LOW);
    adc = (__typeof__(adc)){KNOB_FULL_CODE, NTC_25C, false, false, adc.t, 0, 0};
    run(r, SETTLE);                               /* recovery needs a reset */
    CHECK(!light());
}

static void test_sensor_faults(void)
{
    struct rig r;
    const uint32_t bad_ntc[] = {NTC_OPEN_CODE, 4095u, NTC_CRITICAL_CODE, 10u, 0u};
    for (unsigned i = 0; i < sizeof bad_ntc / sizeof bad_ntc[0]; i++) {
        rig_start(&r, KNOB_FULL_CODE, NTC_25C);
        run(&r, SETTLE);
        adc.ntc = bad_ntc[i];
        latched_off_after(&r, "ntc");
    }
    rig_start(&r, KNOB_FULL_CODE, NTC_25C); run(&r, SETTLE);
    adc.fail = true;                              /* ADC timeout */
    latched_off_after(&r, "adc fail");
    rig_start(&r, KNOB_FULL_CODE, NTC_25C); run(&r, SETTLE);
    adc.not_ok = true;                            /* overrun / incomplete */
    latched_off_after(&r, "adc not ok");
    rig_start(&r, KNOB_FULL_CODE, NTC_25C); run(&r, SETTLE);
    adc.knob = KNOB_ADC_MAX + 1;                  /* out of ADC range */
    latched_off_after(&r, "knob range");
    rig_start(&r, KNOB_FULL_CODE, NTC_25C); run(&r, SETTLE);
    adc.jump = SAMPLE_MAX_AGE_TICKS + 1;          /* stale sample */
    latched_off_after(&r, "stale");
    rig_start(&r, KNOB_FULL_CODE, NTC_25C); run(&r, SETTLE);
    adc.rollback = 1;                             /* clock rollback */
    latched_off_after(&r, "rollback");
    /* Bad sensor from the very first sample: never lights. */
    rig_start(&r, KNOB_FULL_CODE, NTC_OPEN_CODE);
    run(&r, SETTLE);
    CHECK(!light() && hw.max_ccr == 0);
}

static void test_ntc_thermal_gate(void)
{
    /* The thermal gate and the gain are separate layers; each must refuse alone. */
    struct sample_thermal t;
    CHECK(ntc_thermal(NULL, NTC_25C, &t) == BOARD_L_OK && t.known && t.allows_light);
    CHECK(ntc_thermal(NULL, NTC_CRITICAL_CODE + 1, &t) == BOARD_L_OK && t.known && t.allows_light);
    CHECK(ntc_thermal(NULL, NTC_CRITICAL_CODE, &t) == BOARD_L_OK && t.known && !t.allows_light);
    CHECK(ntc_thermal(NULL, 0u, &t) == BOARD_L_OK && t.known && !t.allows_light);
    CHECK(ntc_thermal(NULL, NTC_OPEN_CODE - 1, &t) == BOARD_L_OK && t.known && t.allows_light);
    CHECK(ntc_thermal(NULL, NTC_OPEN_CODE, &t) == BOARD_L_OK && !t.known && !t.allows_light);
    CHECK(ntc_thermal(NULL, 5000u, &t) == BOARD_L_OK && !t.known);
    CHECK(ntc_thermal(NULL, NTC_25C, NULL) == BOARD_L_IO_ERROR);
}

static void test_derate(void)
{
    struct rig r;
    struct thermal_gain g;
    uint32_t prev = LAMP_FULL + 1;
    for (uint32_t code = NTC_CRITICAL_CODE; code <= NTC_DERATE_CODE + 2; code++) {
        CHECK(ntc_gain(NULL, code, &g) == BOARD_L_OK);
        if (code <= NTC_CRITICAL_CODE) { CHECK(!g.valid); continue; }
        CHECK(g.valid && g.value <= LAMP_FULL);
        if (code >= NTC_DERATE_CODE) CHECK(g.value == LAMP_FULL);
        if (prev <= LAMP_FULL) CHECK(g.value >= prev);   /* monotonic: cooler -> more */
        prev = g.value;
    }
    rig_start(&r, KNOB_FULL_CODE, NTC_25C);
    run(&r, SETTLE);
    uint32_t cool = hw.ccr;
    adc.ntc = (NTC_DERATE_CODE + NTC_CRITICAL_CODE) / 2u;   /* ~72 C: about half gain */
    run(&r, 5);
    CHECK(light() && hw.ccr < cool);
}

static void test_knob_window(void)
{
    /* KNOB_WINDOW really averages KNOB_WINDOW samples at one sample per tick. */
    struct board_samples s;
    static const struct raw_source src = {NULL, fake_convert, fake_now};
    struct lamp_samples out;
    struct thermal_gain g;
    uint32_t lo = 1000u, hi = 3000u, final_hi, prev = 0;
    CHECK(SAMPLE_MAX_AGE_TICKS + 1u >= KNOB_WINDOW);
    adc = (__typeof__(adc)){lo, NTC_25C, false, false, 100, 0, 0};
    CHECK(board_samples_init(&s, &src) == BOARD_L_OK);
    for (int i = 0; i < 40; i++) { adc.t++; CHECK(board_samples_read_graded(&s, &out, &g) == BOARD_L_OK); }
    CHECK(s.adapter.knob_count == KNOB_WINDOW);
    {
        struct knob_calibration cal = {true, KNOB_ADC_MAX, KNOB_OFF_CODE, KNOB_FULL_CODE};
        CHECK(knob_request(hi, &cal, &final_hi));
    }
    adc.knob = hi;
    for (unsigned k = 1; k <= KNOB_WINDOW; k++) {
        adc.t++;
        CHECK(board_samples_read_graded(&s, &out, &g) == BOARD_L_OK && out.knob_valid);
        CHECK(out.knob > prev);                       /* moves every tick ... */
        if (k < KNOB_WINDOW) CHECK(out.knob < final_hi); /* ... settles only at the window */
        prev = out.knob;
    }
    CHECK(out.knob == final_hi);
}

static void test_init_refusals(void)
{
    struct board_samples s;
    struct raw_source none = {NULL, NULL, fake_now};
    CHECK(board_samples_init(&s, &none) == BOARD_L_UNCONFIGURED);
    CHECK(board_samples_init(&s, NULL) == BOARD_L_UNCONFIGURED);
    struct lamp_samples out = {1, true, true, true, true};
    CHECK(board_samples_read(NULL, &out) == BOARD_L_UNCONFIGURED && !out.knob_valid);
}

int main(void)
{
    test_normal_and_ceiling();
    test_knob_off();
    test_sensor_faults();
    test_ntc_thermal_gate();
    test_derate();
    test_knob_window();
    test_init_refusals();
    printf("%s %d checks, %d failures (ADC sample source through V72 to CTRL)\n",
           failures ? "FAIL" : "PASS", checks, failures);
    return failures ? 1 : 0;
}
