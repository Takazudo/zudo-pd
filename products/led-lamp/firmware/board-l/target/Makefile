# Board L target skeleton build (STM32G031F8P6). Build only: there is no flash target.
# Toolchain: Ubuntu 24.04 package gcc-arm-none-eabi 15:13.2.rel1-2 (arm-none-eabi-gcc 13.2.1).
# Every image is an UNFLASHED bench candidate; build/board-l-skeleton.receipt.json records
# its identity. Incremental builds track headers (-MMD) and the build configuration
# (build/config.stamp) and this Makefile, so a header, option or Makefile change always rebuilds.
CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
SIZE := $(CROSS)size
OBJCOPY := $(CROSS)objcopy
PYTHON ?= python3
TOOLCHAIN_VERSION := 13.2.1
BUILD := build
V72 := ../src

# Compile-time board options, e.g. BOARD_DEFS=-DBOARD_L_PRODUCTION. Empty is the adopted
# default profile: CTRL_FULL_CCR 2407 from board_l_proposal.h for RS1 = 200 mOhm.
BOARD_DEFS ?=
DEFAULT_CTRL_FULL_CCR := 2407
PROFILE := $(if $(strip $(BOARD_DEFS)),custom,default-rs1-200mohm)

ARCH := -mcpu=cortex-m0plus -mthumb
CFLAGS := $(ARCH) -std=c11 -Os -g -Wall -Wextra -Werror -pedantic -ffreestanding \
          -ffunction-sections -fdata-sections $(BOARD_DEFS)
DEPFLAGS = -MMD -MP -MF $(@:.o=.d)
LDFLAGS := $(ARCH) --specs=nano.specs --specs=nosys.specs -nostartfiles -T stm32g031f8_flash.ld -Wl,--gc-sections \
           -Wl,-Map=$(BUILD)/board-l-skeleton.map -Wl,--print-memory-usage
SRCS := startup_stm32g031.c main.c clock.c board_ctrl.c lamp_target.c board_policy.c board_samples.c \
        board_iwdg.c board_adc.c
# V72 units linked into the image (unchanged sources).
V72_LINKED := lamp_app.c lamp_control.c noise_stage.c thermal_gain.c normalized_transfer.c ctrl_timer_map.c \
              sample_adapter.c input_conversion.c
OBJS := $(SRCS:%.c=$(BUILD)/%.o) $(V72_LINKED:%.c=$(BUILD)/v72/%.o)

# Portable V72 units: compiled for the target to check they build. Not linked.
V72_SRCS := $(filter-out $(V72)/test_input_app.c,$(wildcard $(V72)/*.c))
V72_OBJS := $(V72_SRCS:$(V72)/%.c=$(BUILD)/v72/%.o)
ELF := $(BUILD)/board-l-skeleton.elf
MAP := $(BUILD)/board-l-skeleton.map
RECEIPT := $(BUILD)/board-l-skeleton.receipt.json

HOST_TEST_SRCS := test_input_app.c input_composition.c acquisition_registers.c \
  acquisition_word_rules.c discontinuous_acquisition.c adc_completed_frame.c \
  completed_frame_bridge.c output_composition.c tim3_readiness.c tim3_profile.c \
  tim3_access.c tim3_access_map.c preload_lifecycle.c tim3_preload.c host_timer_output.c \
  ctrl_timer_map.c adc_channel_config.c sample_adapter.c input_conversion.c thermal_gain.c \
  board_binding.c adc_preparation.c lamp_app.c lamp_control.c noise_stage.c normalized_transfer.c

.PHONY: all toolchain-check cap-check v72-objects receipt host-test target-host-test \
        check-incremental verify-regs clean FORCE
all: $(RECEIPT)

toolchain-check:
	@v=$$($(CC) -dumpversion); if [ "$$v" != "$(TOOLCHAIN_VERSION)" ] && [ -z "$(ALLOW_TOOLCHAIN)" ]; then \
	  echo "arm-none-eabi-gcc $$v != pinned $(TOOLCHAIN_VERSION) (set ALLOW_TOOLCHAIN=1 to override)"; exit 1; fi

# The effective ceiling as the compiler sees it, so a -D override cannot pass unnoticed.
cap-check: | toolchain-check
	@cap=$$(printf '#include "board_l_proposal.h"\nCTRL_FULL_CCR\n' | \
	  $(CC) $(CFLAGS) -I. -I$(V72) -E -P -x c - | tail -n 1 | tr -d ' '); \
	if [ "$$cap" != "$(DEFAULT_CTRL_FULL_CCR)u" ] && [ -z "$(ACCEPT_NONDEFAULT_CAP)" ]; then \
	  echo "CTRL_FULL_CCR $$cap != adopted $(DEFAULT_CTRL_FULL_CCR)u for RS1 = 200 mOhm"; \
	  echo "(set ACCEPT_NONDEFAULT_CAP=1 only for a board with a measured RS1 change)"; exit 1; fi

# Identity of everything outside the sources that changes the objects. The stamp is
# rewritten only when that identity changes, so unchanged builds stay incremental.
BUILD_CONFIG := cc=$(CC) $(shell $(CC) -dumpfullversion 2>/dev/null) | cflags=$(CFLAGS) -I$(V72) | ldflags=$(LDFLAGS)
$(BUILD)/config.stamp: FORCE cap-check | $(BUILD)
	@printf '%s\n' '$(BUILD_CONFIG)' | cmp -s - $@ || { printf '%s\n' '$(BUILD_CONFIG)' > $@; \
	  echo "build configuration changed: rebuilding"; }

$(BUILD)/%.o: %.c $(BUILD)/config.stamp Makefile | $(BUILD)
	$(CC) $(CFLAGS) $(DEPFLAGS) -I$(V72) -c $< -o $@

$(ELF): $(OBJS) stm32g031f8_flash.ld $(BUILD)/config.stamp Makefile | $(BUILD)/v72
	$(CC) $(LDFLAGS) $(OBJS) -Wl,--start-group -lc_nano -lgcc -Wl,--end-group -o $@
	$(SIZE) $@

receipt: $(RECEIPT)
$(RECEIPT): $(ELF) tools/build_receipt.py
	$(PYTHON) -I tools/build_receipt.py --elf $(ELF) --map $(MAP) --config $(BUILD)/config.stamp \
	  --profile $(PROFILE) --board-defs='$(strip $(BOARD_DEFS))' --default-cap $(DEFAULT_CTRL_FULL_CCR) \
	  --cc '$(CC)' --size '$(SIZE)' --objcopy '$(OBJCOPY)' --pinned-toolchain $(TOOLCHAIN_VERSION) \
	  --allow-toolchain='$(ALLOW_TOOLCHAIN)' --accept-nondefault-cap='$(ACCEPT_NONDEFAULT_CAP)' \
	  --deps $(OBJS:.o=.d) --output $@

v72-objects: $(V72_OBJS)
$(BUILD)/v72/%.o: $(V72)/%.c $(BUILD)/config.stamp Makefile | $(BUILD)/v72
	$(CC) $(CFLAGS) $(DEPFLAGS) -I$(V72) -c $< -o $@

-include $(wildcard $(BUILD)/*.d $(BUILD)/v72/*.d)

# Clean vs incremental, header-change rebuild and option switching, on a scratch copy.
check-incremental:
	bash verify/check_incremental.sh

# Re-run the V72 host test with the host compiler, as recorded in ../provenance.
host-test: | $(BUILD)
	cd $(V72) && cc -std=c11 -O0 -g -Wall -Wextra -Werror -pedantic -I . $(HOST_TEST_SRCS) -o $(CURDIR)/$(BUILD)/host-test
	$(BUILD)/host-test

# Host tests of every OFF path: lamp_target wiring (fake CTRL port), boot policy
# (reset latch, option bytes, clock) and the ADC sample source through V72.
TARGET_TEST_COMMON := lamp_target.c board_policy.c board_samples.c $(V72_LINKED:%=$(V72)/%)
TARGET_TESTS := test_lamp_target test_board_policy test_board_samples
HOST_CC := cc -std=c11 -O0 -g -Wall -Wextra -Werror -pedantic -I . -I $(V72)
target-host-test: | $(BUILD)
	@set -e; for t in $(TARGET_TESTS); do \
	  $(HOST_CC) $(HOST_DEFS) test/$$t.c $(TARGET_TEST_COMMON) -lm -o $(BUILD)/$$t; \
	  $(BUILD)/$$t; done

# Cross-check stm32g031_regs.h against ST/ARM headers fetched outside the repo.
verify-regs:
	@test -n "$(ST_DEVICE_INC)" -a -n "$(ST_LL_INC)" -a -n "$(CMSIS_CORE_INC)" || \
	  { echo "set ST_DEVICE_INC, ST_LL_INC and CMSIS_CORE_INC (see SOURCES.md)"; exit 1; }
	$(CC) $(ARCH) -std=c11 -Werror -DSTM32G031xx -fsyntax-only -I$(ST_DEVICE_INC) -I$(ST_LL_INC) \
	  -I$(CMSIS_CORE_INC) verify/verify_regs.c
	@echo "PASS: stm32g031_regs.h matches the ST/ARM headers"

$(BUILD) $(BUILD)/v72:
	mkdir -p $@

clean:
	rm -rf ./$(BUILD)
