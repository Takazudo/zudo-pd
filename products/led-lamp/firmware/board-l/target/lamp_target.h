#ifndef LAMP_TARGET_H
#define LAMP_TARGET_H
/* Off-by-default adapter between the V72 lamp_app and the Board L CTRL output.
 * Contract:
 *  - No output change before initialize_off() succeeds with a valid config;
 *    until then, and on any refused config or mapping, the port is forced OFF.
 *  - Zero maps to CCR 0; positive values map into [positive_min_ccr,
 *    positive_full_ccr] (V72 ctrl_timer_map), so the configured ceiling bounds duty.
 *  - force_off() leaves PA6 as GPIO-low. The next positive apply re-runs the
 *    0 % timer handover before writing any non-zero compare value.
 *  - Missing sample source = adapter error, which lamp_app turns into OFF.
 *  - The graded (thermal gain) read forwards the same sample port; with no
 *    read_graded callback it reports UNCONFIGURED, never unity gain.
 * Nothing here measures or proves physical OFF. */
#include "../src/lamp_app.h"
#include "../src/ctrl_timer_map.h"

struct board_l_config { struct ctrl_timer_config ctrl; };

struct ctrl_port {
    void (*force_off)(void);
    void (*pwm_init_zero)(uint32_t period_ticks);
    void (*write_ccr)(uint32_t ccr);
};
struct sample_port {
    void *context;
    enum board_l_result (*read)(void *, struct lamp_samples *);
    enum board_l_result (*read_graded)(void *, struct lamp_samples *, struct thermal_gain *);
};
struct lamp_target {
    struct ctrl_port port;
    struct sample_port samples;
    struct ctrl_timer_mapper mapper;
    bool bound, initialized, output_enabled;
};

/* Port callbacks are required; a NULL sample reader keeps the lamp OFF. */
bool lamp_target_bind(struct lamp_target *, const struct ctrl_port *, const struct sample_port *);
struct lamp_app_io lamp_target_io(struct lamp_target *);
/* Thermal-gain path for lamp_app_initialize_with_thermal_gain (same context as io). */
struct lamp_app_gain_path lamp_target_gain_path(void);
#endif
