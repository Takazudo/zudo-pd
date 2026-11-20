#ifndef BOARD_L_IO_H
#define BOARD_L_IO_H
#include "lamp_control.h"
/* Project connectivity only, NOT a verified STM32 peripheral mapping.
   scripts/schgen/board_l_spec.py NETS, STM32G031F8P6/C529334 U3:
   U3.7 PA0 BRIGHT_ADC; U3.11 PA4 NTC_SENSE; U3.13 PA6 PWM_DIM -> R20 -> CTRL.
   U3.12 PA5 legacy PDOK and U3.14 PA7 legacy ATT have local 10k pullups;
   shared HUSB Board P contacts 4/3 are NC. Never use these as admission inputs.
   U3.18 SWDIO, U3.19 SWCLK, U3.6 NRST. Debug is not power isolation.
*/
enum board_l_result { BOARD_L_OK, BOARD_L_UNCONFIGURED, BOARD_L_IO_ERROR, BOARD_L_PREPARING, BOARD_L_ACQUISITION_UNQUALIFIED };
/* Opaque, deliberately undefined. No production defaults provided.
   Future implementation must validate ADC endpoints/reference/settling/freshness,
   NTC conversion/fault/temperature thresholds, PWM mux/period/polarity,
   CTRL transfer and OFF guarantee, tick/ramp duration and recovery policy.
   NULL/incomplete config: report UNCONFIGURED and maintain physical OFF.
   These declarations do not implement or prove that physical OFF. */
struct board_l_config;
enum board_l_result board_l_initialize_off(const struct board_l_config *cfg);
enum board_l_result board_l_read_samples(struct lamp_samples *out);
/* Must reject uninitialized/unconfigured/out-of-range requests, force OFF on
   failure, and return error. Zero means OFF, not an assumed PWM polarity.
   Call on EVERY control tick including failures; cached output is forbidden. */
enum board_l_result board_l_apply_command(uint32_t command);
/* Must establish OFF even without calibration; implementation still missing. */
void board_l_force_off(void);
#endif
