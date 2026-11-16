#ifndef BOARD_BINDING_H
#define BOARD_BINDING_H
#include "lamp_app.h"
#include "sample_adapter.h"
#include "adc_preparation.h"
#include "adc_channel_config.h"

/* Contract in ../BACKEND-CONTRACT.md. Request acceptance != measured OFF.
   No target settings definition or normalized-to-PWM conversion here. */
struct lamp_output_backend {
    void *context; /* required, may differ from acquisition context */
    enum board_l_result (*initialize_off)(void *, const struct board_l_config *);
    enum board_l_result (*apply_normalized)(void *, uint32_t);
    void (*force_off)(void *);
};
struct lamp_board_setup {
    struct sample_adapter_config samples;
    struct sample_adapter_hooks acquisition;
    struct lamp_output_backend output;
};
/* Fixed field operations inside the existing disabled startup phase. All
   callbacks bounded/exclusive; every action must recheck disabled/idle and
   preserve calibration interlock. BASELINE verifies reset channel fields,
   valid reserved bits and known no-update-in-flight, not merely CCRDY=0. */
enum lamp_adc_field_operation {
 LAMP_ADC_BASELINE, LAMP_ADC_CLEAR_BEFORE_CFGR, LAMP_ADC_CLEARED_BEFORE_CFGR,
 LAMP_ADC_WRITE_CFGR, LAMP_ADC_CFGR_CCRDY, LAMP_ADC_READ_CFGR,
 LAMP_ADC_CLEAR_BEFORE_CHANNELS, LAMP_ADC_CLEARED_BEFORE_CHANNELS,
 LAMP_ADC_WRITE_CHANNELS, LAMP_ADC_CHANNELS_CCRDY, LAMP_ADC_READ_CHANNELS,
 LAMP_ADC_WRITE_SMPR, LAMP_ADC_READ_SMPR, LAMP_ADC_FINAL_DISABLED,
 LAMP_ADC_FIELD_COUNT
};
struct lamp_adc_field_backend {
 void *context;
 bool (*transact)(void *,enum lamp_adc_field_operation,
                  const struct adc_masked_field *,struct adc_reply *);
};
enum lamp_adc_field_error {LAMP_ADC_FIELD_OK,LAMP_ADC_FIELD_CALLBACK,
 LAMP_ADC_FIELD_BASELINE,LAMP_ADC_FIELD_PAYLOAD,LAMP_ADC_FIELD_TIMEOUT,LAMP_ADC_FIELD_READBACK};
struct lamp_board_binding {
    bool bound, initialized, zero_accepted;
    struct lamp_board_setup setup;
    struct sample_adapter adapter;
    bool preparation_enabled, preparation_active, output_initialized;
    uint64_t preparation_epoch;
    struct adc_backend adc_backend;
    struct adc_qualification adc_qualification;
    struct adc_preparation adc, previous_adc;
    bool channel_config_enabled, channel_config_complete;
    struct adc_channel_descriptor channel_descriptor;
    struct lamp_adc_field_backend field_backend;
    enum lamp_adc_field_error field_error, previous_field_error;
    unsigned field_step, previous_field_step;
    uint32_t field_observations, previous_field_observations;
    bool gain_enabled;
    struct sample_gain_config gain_config;
};
/* Zero initialize before first call; fixed owner/context/config for lifetime.
   Copies validated setup. A repeat bind is refused, clears readiness and asks
   OLD backend OFF; no new callback/context is touched. No callbacks on first
   invalid setup. Caller must handle lack of any usable OFF backend explicitly. */
enum board_l_result lamp_board_bind(struct lamp_board_binding *, const struct lamp_board_setup *);
enum board_l_result lamp_board_bind_graded(struct lamp_board_binding *,const struct lamp_board_setup *,const struct sample_gain_config *);
enum board_l_result lamp_board_read_graded(void *,struct lamp_samples *,struct thermal_gain *);
/* Stable callback addresses and binding context preserve lamp_app's lock.
   Can be obtained before bind; all operational callbacks then fail closed. */
struct lamp_app_io lamp_board_io(struct lamp_board_binding *);
/* Opt-in at first bind only; retained setup remains immutable. No sample adapter
   initialization/acquisition admission on this path. Separate epoch per explicit init. */
enum board_l_result lamp_board_bind_preparation(struct lamp_board_binding *,
    const struct lamp_board_setup *,const struct adc_backend *,const struct adc_qualification *);
struct lamp_app_preparation lamp_board_preparation(void);
/* Only reset-channel baseline supported: known CHSELR=0, CHSELRMOD/SCANDIR=0,
   valid reserved bits, no pending channel update. Other transitions rejected. */
enum board_l_result lamp_board_bind_channel_preparation(struct lamp_board_binding *,
 const struct lamp_board_setup *,const struct adc_backend *,const struct adc_qualification *,
 const struct adc_channel_choice *,const struct lamp_adc_field_backend *);
#endif
