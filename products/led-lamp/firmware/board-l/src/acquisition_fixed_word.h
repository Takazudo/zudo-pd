#ifndef ACQUISITION_FIXED_WORD_H
#define ACQUISITION_FIXED_WORD_H
#include "acquisition_registers.h"
/* Pure descriptor validation; reuse V66 map, no caller address or width. */
bool acquisition_word_read_location(enum acquisition_register,struct acquisition_location *);
bool acquisition_word_store_location(enum acquisition_store,uint32_t,struct acquisition_location *);
/* TARGET SOURCE ONLY. Low-level seam, NOT independent permission. Supply only
 * to qualified V66 under its held scope. Never invoke in HOST or this task. */
struct acquisition_register_transport acquisition_fixed_word_transport(void);
#endif
