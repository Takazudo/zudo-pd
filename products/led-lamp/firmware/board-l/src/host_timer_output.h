#ifndef HOST_TIMER_OUTPUT_H
#define HOST_TIMER_OUTPUT_H
#include "board_binding.h"
#include "ctrl_timer_map.h"
/* HOST-ONLY injection boundary. No active pin or physical OFF feedback exists. */
struct timer_sink_receipt {bool accepted;uint32_t accepted_ccr;};
struct host_timer_sink {
    void *context;
    enum board_l_result (*initialize_off)(void *,const struct board_l_config *);
    enum board_l_result (*ready)(void *,bool *);
    enum board_l_result (*write_preload)(void *,uint32_t,struct timer_sink_receipt *);
    void (*request_off)(void *);
};
struct host_timer_setup {struct ctrl_timer_config mapper;struct host_timer_sink sink;};
enum host_timer_error {
    HOST_TIMER_NO_ERROR,HOST_TIMER_CONFIG_ERROR,HOST_TIMER_INIT_ERROR,
    HOST_TIMER_READINESS_ERROR,HOST_TIMER_ZERO_REQUIRED,HOST_TIMER_MAPPING_ERROR,
    HOST_TIMER_WRITE_ERROR,HOST_TIMER_RECEIPT_ERROR,HOST_TIMER_REBIND_REFUSED
};
struct host_timer_report {
    uint32_t normalized_request,requested_ccr,accepted_ccr;
    bool transaction_accepted,off_requested,physical_off_verified;
};
struct host_timer_output {
    struct host_timer_setup setup;
    struct ctrl_timer_mapper mapper;
    struct host_timer_report last;
    enum host_timer_error first_error,previous_epoch_error;
    enum board_l_result first_result;
    bool bind_attempted,configured,initialized,zero_accepted,faulted;
    bool off_dispatched,rebind_refused;
};
/* Zero initialize once; immutable setup; no concurrent/external mutation.
   Bind performs no sink callbacks. Explicit app initialization starts new epoch,
   preserving prior epoch cause separately; no automatic restart or rebind. */
enum board_l_result host_timer_bind(struct host_timer_output *,const struct host_timer_setup *);
struct lamp_output_backend host_timer_backend(struct host_timer_output *);
#endif
