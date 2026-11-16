#ifndef LAMP_CONTROL_H
#define LAMP_CONTROL_H
#include <stdbool.h>
#include <stdint.h>
/* Representation only: not PWM duty or a physical brightness calibration. */
#define LAMP_FULL UINT32_C(65536)
enum lamp_recovery { LAMP_RECOVERY_UNSET, LAMP_RECOVERY_AUTO, LAMP_RECOVERY_LATCH };
enum lamp_status { LAMP_RESET_OFF, LAMP_UNCONFIGURED, LAMP_WAIT_VALID,
                   LAMP_LATCHED_OFF, LAMP_RAMP, LAMP_READY, LAMP_BAD_ARGUMENT };
struct lamp_config {
    uint32_t increment; /* abstract units per qualified caller tick; zero is unset */
    enum lamp_recovery recovery;
};
struct lamp_samples {
    uint32_t knob;
    bool knob_valid, thermal_valid, thermal_allows_light, fresh;
};
struct lamp_control {
    uint32_t command;
    bool initialized, latched;
    enum lamp_status status;
};
void lamp_reset(struct lamp_control *c);
/* Call only after target adapter has actually established OFF. Not a pin write. */
void lamp_initialize_off(struct lamp_control *c);
/* Every failed call with non-null c clears command. Null c returns BAD_ARGUMENT.
   Config is checked per call; explicit changes are supported, never clear a latch,
   and are not a selected product runtime policy. No concurrent calls supported.
   Latch recovery requires explicit initialize_off after hardware OFF, not knob=0. */
enum lamp_status lamp_step(struct lamp_control *c, const struct lamp_config *cfg,
                           const struct lamp_samples *s);
#endif
