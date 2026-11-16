#ifndef NORMALIZED_TRANSFER_H
#define NORMALIZED_TRANSFER_H
#include "lamp_control.h"
#include <stddef.h>
#define NORMALIZED_TRANSFER_MAX_POINTS 16u
struct transfer_point {uint32_t input,output;};
struct transfer_config {bool configured;const struct transfer_point *points;size_t count;};
struct normalized_transfer {
    bool configured;size_t count;
    struct transfer_point points[NORMALIZED_TRANSFER_MAX_POINTS];
};
enum transfer_status {TRANSFER_UNCONFIGURED,TRANSFER_OK,TRANSFER_BAD_INPUT,TRANSFER_BAD_ARGUMENT};
/* Owns copy, no retained caller pointer; no concurrent/reentrant mutation.
   Domain0..FULL, zero-preserving, monotone, nonamplifying piecewise-linear floor.
   No physical PWM/CTRL meaning or default gamma. See ../TRANSFER-CONTRACT.md. */
enum transfer_status transfer_initialize(struct normalized_transfer *,const struct transfer_config *);
enum transfer_status transfer_apply(const struct normalized_transfer *,uint32_t,uint32_t *);
#endif
