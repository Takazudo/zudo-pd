#ifndef DISCONTINUOUS_ACQUISITION_H
#define DISCONTINUOUS_ACQUISITION_H
#include "adc_completed_frame.h"
/* Abstract operations, never addresses/register configuration. Single owner,
 * nonreentrant, immutable after one configure. External proof is factual and
 * independent of produced tags; no OVR==0 inference of loss freedom. */
struct da_limits {
 uint64_t ticks_per_second,adc_hz,step_ticks,frame_ticks,skew_ticks,max_age_ticks;
 uint64_t minimum_spacing_ticks,scope_until;
 uint32_t polls_per_conversion;
 bool qualified;
};
struct da_proof {
 uint64_t epoch,scope_until;
 struct adc_channel_choice choice;
 bool valid,exclusive,whole_consumer_scope,consumer_epoch_valid;
 bool clock_qualified,entry_qualified,configuration_qualified;
 bool normal_enable,discontinuous,software_only,lftrig;
 bool autoff,continuous,oversampling;
 bool sequence_integrity; /* independent absence of alien starts/hidden loss */
};
struct da_status { bool valid,adstart,eoc,eos,overrun,error; };
struct da_io {
 void *context;
 enum board_l_result (*proof)(void *,struct da_proof *);
 enum board_l_result (*clock)(void *,struct sample_clock *);
 enum board_l_result (*status)(void *,struct da_status *);
 enum board_l_result (*start)(void *); /* ADSTART request; may be uncertain on error */
 enum board_l_result (*read)(void *,uint32_t *); /* DR read consumes EOC */
 enum board_l_result (*clear_eos)(void *); /* EOS-only W1C, never clear OVR/EOC */
};
enum da_error {DA_NONE,DA_CONFIG,DA_REBIND,DA_ARGUMENT,DA_PROOF_CALLBACK,
 DA_PROOF,DA_CLOCK_CALLBACK,DA_CLOCK,DA_SCOPE,DA_TIME,DA_SPACING,DA_STATUS_CALLBACK,
 DA_STATUS,DA_OVERRUN,DA_POLL_LIMIT,DA_START_CALLBACK,DA_READ_CALLBACK,
 DA_CLEAR_CALLBACK,DA_FORMAT,DA_SEQUENCE_EXHAUSTED,DA_REENTRANT};
enum da_stage {DA_CONFIGURATION,DA_ENTRY,DA_START,DA_WAIT,DA_READ,DA_AFTER_READ,
 DA_CLEAR,DA_FINAL};
struct discontinuous_acquisition {
 struct adc_channel_choice choice;
 struct da_limits limits;
 struct da_io io;
 uint64_t epoch,next_sequence,last_clock,frame_begin,step_begin,last_begin;
 bool attempted,configured,have_clock,in_frame,have_frame,start_uncertain,busy;
 enum da_error first_error;
 enum da_stage stage,first_stage;
 enum board_l_result first_callback;
 unsigned rank,first_rank;
 uint32_t polls;
};
bool da_configure(struct discontinuous_acquisition *,const struct adc_channel_choice *,
 uint64_t epoch,uint64_t first_sequence,const struct da_limits *,const struct da_io *);
/* V56-compatible producer. Synchronous, finite polls (2*N), no retry/recovery.
 * Never publishes partial/stale frame. One successful call consumes one sequence;
 * UINT64_MAX refused (no wrap). On any failure sticky stop, no more callbacks.
 * Tick and callback bounds/ownership must be true externally; source count bounds
 * cannot preempt a callback which blocks or a dishonest proof provider. */
enum board_l_result da_produce(void *,struct adc_completed_frame *);
#endif
