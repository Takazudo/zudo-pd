#ifndef CLOCK_H
#define CLOCK_H
#include <stdint.h>
enum clock_result { CLOCK_PLL_64MHZ, CLOCK_HSI16_NOT_RANGE1, CLOCK_HSI16_TIMEOUT };
enum clock_result clock_init_64mhz(void);
uint32_t clock_hclk_hz(enum clock_result r);
#endif
