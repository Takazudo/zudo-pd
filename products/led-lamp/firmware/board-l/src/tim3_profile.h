#ifndef TIM3_PROFILE_H
#define TIM3_PROFILE_H
#include "tim3_preload.h"
bool tim3_profile_config_valid(const struct tim3_preload_config *);
bool tim3_profile_expected(const struct tim3_preload_config *,enum tim3_preload_register,uint32_t *);
#endif
