#ifndef LAMP_APP_H
#define LAMP_APP_H
#include "board_l_io.h"
#include "noise_stage.h"
#include "thermal_gain.h"
#include "normalized_transfer.h"
/* Injected equivalents of the existing board API. Read returns normalized samples;
   calibration/conversion/freshness/thermal decisions stay in the actual adapter.
   No peripheral implementation, production defaults or physical OFF evidence. */
struct lamp_app_io {
    void *context;
    enum board_l_result (*initialize_off)(void *, const struct board_l_config *);
    enum board_l_result (*read_samples)(void *, struct lamp_samples *);
    enum board_l_result (*apply_command)(void *, uint32_t);
    void (*force_off)(void *);
};
enum lamp_app_status {
    LAMP_APP_OK, LAMP_APP_CORE_OFF, LAMP_APP_UNCONFIGURED,
    LAMP_APP_ADAPTER_ERROR, LAMP_APP_REINITIALIZE_REQUIRED, LAMP_APP_BAD_ARGUMENT,
    LAMP_APP_TRANSFORM_ERROR, LAMP_APP_FRAME_OFF,
    LAMP_APP_STARTUP_PENDING, LAMP_APP_ACQUISITION_UNQUALIFIED
};
/* Optional closed preparation lifecycle. Same context as io. Epoch0 invalid.
   Progress returns PREPARING/ACQUISITION_UNQUALIFIED/error, NEVER permission OK. */
struct lamp_app_preparation {
    uint64_t (*epoch)(void *);
    enum board_l_result (*advance)(void *,uint64_t);
};
struct lamp_app_noise {
    bool enabled;
    struct noise_config config;
    struct noise_source source;
};
struct lamp_frame { bool qualified; }; /* explicit animation-frame admission */
struct lamp_app_gain_path {
    bool enabled;
    /* Same context as app.io; result belongs to the SAME sample read. */
    enum board_l_result (*read_graded)(void *,struct lamp_samples *,struct thermal_gain *);
};
struct lamp_app_report {
    enum lamp_app_status status;
    enum lamp_status core_status;
    enum board_l_result cause, last_apply_result;
    uint32_t command; /* applied software request; never PWM/physical evidence */
    uint32_t core_command; /* separate unmodulated ramp accumulator */
    enum noise_status noise_status;
    bool noise_enabled, noise_attempted;
    bool gain_enabled, gain_valid;
    uint32_t gain, pre_thermal_command;
    uint32_t post_thermal_command;
    bool transfer_enabled,transfer_attempted;
    enum transfer_status transfer_status;
    bool board_ready, reinitialize_required;
    bool startup_pending, acquisition_unqualified;
    uint64_t startup_epoch;
    bool apply_attempted, force_off_requested;
    bool have_first_invalid_sample;
    struct lamp_samples first_invalid_sample;
    bool physical_off_verified; /* always false: this API has no measurement input */
};
struct lamp_app {
    /* Lifetime diagnostic: explicit reinitialization does not erase it. */
    bool have_first_invalid_sample;
    struct lamp_samples first_invalid_sample;
    struct lamp_control core;
    struct lamp_app_io io;
    bool binding_locked, board_ready, reinitialize_required;
    struct lamp_app_preparation preparation;
    bool preparation_locked, startup_pending, acquisition_unqualified;
    uint64_t startup_epoch;
    struct noise_stage noise;
    bool noise_enabled;
    struct lamp_app_gain_path gain_path;
    struct normalized_transfer transfer;
    bool transfer_enabled;
};
/* Zero-initialize before first use. One owner, no concurrent/reentrant calls;
   callbacks must not modify this object. Binding is fixed once complete.
   Reinitialization uses the SAME callbacks/context and explicit board config.
   initialize_off==OK is the adapter's OFF/readiness contract, not a measurement.
   No nonzero apply occurs before successful board setup and zero application.
   Changing binding is refused and requests OFF through the old binding. */
struct lamp_app_report lamp_app_initialize(struct lamp_app *,
    const struct lamp_app_io *, const struct board_l_config *);
/* Explicit optional configuration copied on initialization; NULL/disabled is
   original behavior. No RNG call during init. Reinit resets all noise state. */
struct lamp_app_report lamp_app_initialize_with_noise(struct lamp_app *,
    const struct lamp_app_io *, const struct board_l_config *, const struct lamp_app_noise *);
/* Optional explicit graded reader. Legacy initializers disable this path;
   matched sample/binding graded configuration is required, no implicit unity. */
struct lamp_app_report lamp_app_initialize_with_thermal_gain(struct lamp_app *,
    const struct lamp_app_io *,const struct board_l_config *,const struct lamp_app_noise *,
    const struct lamp_app_gain_path *);
/* Optional final normalized transfer copied/validated, after thermal attenuation.
   NULL disables. Invalid supplied config is OFF/unconfigured, never bypassed. */
struct lamp_app_report lamp_app_initialize_with_transfer(struct lamp_app *,
    const struct lamp_app_io *,const struct board_l_config *,const struct lamp_app_noise *,
    const struct lamp_app_gain_path *,const struct transfer_config *);
/* Increment remains explicit per tick. Application sensor recovery is always
   LATCH, regardless of caller recovery selection. Sensor invalidity latches even
   with missing/invalid config. Normal values, knob zero and config changes cannot
   clear it. Only explicit initialize traverses existing initialization contracts;
   child errors/qualification gates are never reset here. First invalid normalized
   sample is retained for the lifetime of this zero-initialized object. */
struct lamp_app_report lamp_app_tick(struct lamp_app *, const struct lamp_config *);
/* Noise only at current core READY with valid positive base. RAMP keeps original
   unmodulated output. At READY, missing/unqualified frame resets noise and requests
   zero/OFF (FRAME_OFF), retaining current freshly-computed core accumulator.
   Legacy tick supplies no frame: never silently assumes animation qualification.
   Transform error uses existing app zero/reinitialize discipline. */
struct lamp_app_report lamp_app_tick_frame(struct lamp_app *, const struct lamp_config *, const struct lamp_frame *);
/* Opt-in closed preparation, no implicit gain/noise/transfer configuration. */
struct lamp_app_report lamp_app_initialize_with_preparation(struct lamp_app *,
    const struct lamp_app_io *,const struct board_l_config *,const struct lamp_app_preparation *);
#endif
