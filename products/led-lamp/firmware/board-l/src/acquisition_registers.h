#ifndef ACQUISITION_REGISTERS_H
#define ACQUISITION_REGISTERS_H
#include "discontinuous_acquisition.h"
enum acquisition_register {ACQ_ISR,ACQ_CR,ACQ_DR,ACQ_REGISTER_COUNT};
enum acquisition_store {ACQ_START_COMMAND,ACQ_CLEAR_EOS};
struct acquisition_location {uint32_t address;unsigned width;};
bool acquisition_register_location(enum acquisition_register,struct acquisition_location *);
struct acquisition_register_transport {
 void *context;
 enum board_l_result (*read_word)(void *,enum acquisition_register,uint32_t *);
 /* Only two fixed operation kinds; adapter supplies exact command word.
  * No caller address, arbitrary register writer, configuration or actual MMIO. */
 enum board_l_result (*store_word)(void *,enum acquisition_store,uint32_t);
};
struct acquisition_register_providers {
 void *proof_context;enum board_l_result (*proof)(void *,struct da_proof *);
 void *clock_context;enum board_l_result (*clock)(void *,struct sample_clock *);
};
enum acquisition_register_error {AR_NONE,AR_CONFIG,AR_REBIND,AR_CONTEXT,AR_REENTRANT,
 AR_ARGUMENT,AR_PROOF_CALLBACK,AR_PROOF,AR_CLOCK_CALLBACK,AR_CLOCK,AR_READ,
 AR_STATE,AR_TRANSITION,AR_ORDER,AR_STORE,AR_DR_WORD,AR_POST_READ,AR_W1C};
enum acquisition_register_operation {AR_CONFIGURE,AR_PROOF_OP,AR_CLOCK_OP,AR_STATUS_OP,AR_START_OP,AR_READ_OP,AR_CLEAR_OP};
struct acquisition_registers {
 struct acquisition_registers *self;struct adc_channel_choice choice;
 struct acquisition_register_transport transport;struct acquisition_register_providers providers;
 uint64_t epoch,scope_until,last_clock;
 bool attempted,configured,busy,have_clock,started;
 unsigned next_rank;
 bool start_uncertain,store_uncertain,dr_consumption_uncertain;
 uint32_t last_cr,last_isr;
 enum acquisition_register_error first_error;
 enum acquisition_register_operation operation,first_operation;
 enum acquisition_register current_register,first_register;
 enum board_l_result first_callback;
 bool first_start_uncertain,first_store_uncertain,first_dr_uncertain;
};
bool acquisition_registers_configure(struct acquisition_registers *,const struct adc_channel_choice *,
 uint64_t epoch,uint64_t scope_until,const struct acquisition_register_providers *,const struct acquisition_register_transport *);
bool acquisition_registers_io(struct acquisition_registers *,struct da_io *);
#endif
