#ifndef BOARD_POLICY_H
#define BOARD_POLICY_H
/* Portable boot policy (host-tested): reset-cause latch and option-byte gate.
 * PROPOSAL (PROPOSAL-CTRL-RESET-OPTIONS.md section 2-3); no bench evidence. */
#include <stdbool.h>
#include <stdint.h>

#define RESET_RECORD_MAGIC UINT32_C(0x4C52A5C3)

/* Lives in .noinit RAM: survives a reset while SRAM is retained (including a BOR or a
 * short supply dip), garbage after a power-off that loses SRAM (duration [DS]).
 * long_run: this boot has run for RESET_HEALTHY_TICKS (in normal operation or parked). */
struct reset_record {
    uint32_t magic, count, long_run, check;
};

enum reset_kind { RESET_POWER, RESET_ABNORMAL, RESET_NEUTRAL };

enum boot_refusal {
    BOOT_REFUSE_NONE = 0,
    BOOT_REFUSE_RESET_LATCH = 1u << 0,
    BOOT_REFUSE_BOR_DISABLED = 1u << 1,
    BOOT_REFUSE_BOR_LEVEL = 1u << 2,
    BOOT_REFUSE_CLOCK = 1u << 3
};

struct boot_decision {
    bool allow_light;
    uint32_t refusals;          /* enum boot_refusal bits */
    enum reset_kind reset;
    uint32_t reset_count;       /* consecutive abnormal resets after this boot */
    uint32_t option_notes;      /* diagnostic only: enum option_note bits */
};

enum option_note {
    OPTION_NOTE_BOOT_PIN = 1u << 0,      /* nBOOT_SEL = 0: BOOT0 taken from the pin */
    OPTION_NOTE_BOOT_SYSTEM = 1u << 1,   /* nBOOT0 = 0 with nBOOT_SEL = 1 */
    OPTION_NOTE_IWDG_SOFTWARE = 1u << 2, /* IWDG_SW = 1 (development setting) */
    OPTION_NOTE_NRST_NOT_IO = 1u << 3,   /* NRST_MODE != 3 */
    OPTION_NOTE_RDP_NOT_LEVEL0 = 1u << 4
};

/* Classifies RCC_CSR reset flags. PWRRSTF (POR/PDR or BOR on G0) wins; then IWDG/WWDG/
 * software/low-power resets are abnormal; pin-only or option-load resets are neutral. */
enum reset_kind reset_classify(uint32_t csr);
/* Updates the record for this boot and returns the consecutive abnormal count:
 *  - abnormal reset: +1;
 *  - PWRRSTF with a valid record whose previous boot did NOT reach the healthy run
 *    (a BOR or supply-dip reset loop, e.g. sag on each ramp): +1;
 *  - PWRRSTF after a long run, or with the record lost (a power cycle): cleared;
 *  - neutral: unchanged. An invalid record after a non-power reset is rebuilt as if
 *    one earlier abnormal reset had happened. Saturates at RESET_LATCH_COUNT. */
uint32_t reset_record_update(struct reset_record *, uint32_t csr);
/* Call from the main loop with the uptime in ticks. After RESET_HEALTHY_TICKS it
 * marks the run long; if running_normally, it also clears the count, which makes the
 * latch count CONSECUTIVE failures. A parked (refused) boot never clears the count. */
void reset_record_note_uptime(struct reset_record *, uint32_t uptime_ticks, bool running_normally);
/* Option-byte gate: required BOR settings -> refusal bits; others -> notes. */
uint32_t option_refusals(uint32_t optr, uint32_t *notes);
/* Full decision. clock_ok false or any refusal keeps the lamp OFF. */
struct boot_decision boot_decide(struct reset_record *, uint32_t csr, uint32_t optr, bool clock_ok);
/* What main does with a decision. The latch is checked first, so a latched board always
 * parks OFF (stable, diagnosable) even with a clock failure. A clock failure alone halts
 * without a watchdog refresh, so the retry is a counted reset. Other refusals park. */
enum boot_action { BOOT_RUN, BOOT_PARK_OFF, BOOT_HALT_OFF };
enum boot_action boot_action_for(const struct boot_decision *);
#endif
