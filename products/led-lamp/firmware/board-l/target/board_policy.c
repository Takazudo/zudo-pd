#include "board_policy.h"
#include "board_l_proposal.h"
#include "stm32g031_regs.h"

#define ABNORMAL_FLAGS (RCC_CSR_IWDGRSTF_BIT | RCC_CSR_WWDGRSTF_BIT | RCC_CSR_SFTRSTF_BIT | \
                        RCC_CSR_LPWRRSTF_BIT)

enum reset_kind reset_classify(uint32_t csr)
{
    if (csr & RCC_CSR_PWRRSTF_BIT)
        return RESET_POWER;
    if (csr & ABNORMAL_FLAGS)
        return RESET_ABNORMAL;
    return RESET_NEUTRAL;
}

static uint32_t record_check(uint32_t count, uint32_t long_run)
{
    return ~(count ^ (long_run << 16));
}

static bool record_valid(const struct reset_record *r)
{
    return r->magic == RESET_RECORD_MAGIC && r->count <= RESET_LATCH_COUNT && r->long_run <= 1u &&
           r->check == record_check(r->count, r->long_run);
}

static void record_write(struct reset_record *r, uint32_t count, uint32_t long_run)
{
    r->magic = RESET_RECORD_MAGIC;
    r->count = count;
    r->long_run = long_run;
    r->check = record_check(count, long_run);
}

uint32_t reset_record_update(struct reset_record *r, uint32_t csr)
{
    enum reset_kind kind = reset_classify(csr);
    bool valid = record_valid(r);
    uint32_t count;
    bool counts = kind == RESET_ABNORMAL;
    if (kind == RESET_POWER) {
        if (!valid || r->long_run)
            count = 0u;                   /* power cycle: SRAM lost, or after a long run */
        else {
            count = r->count;             /* short-run BOR/dip: possible reset loop */
            counts = true;
        }
    } else if (!valid)
        /* SRAM state lost without a power reset: assume the worst plausible history. */
        count = counts ? 1u : 0u;
    else
        count = r->count;
    if (counts && count < RESET_LATCH_COUNT)
        count++;
    record_write(r, count, 0u);
    return count;
}

void reset_record_note_uptime(struct reset_record *r, uint32_t uptime_ticks, bool running_normally)
{
    if (!r || uptime_ticks < RESET_HEALTHY_TICKS || !record_valid(r))
        return;
    if (r->long_run && (!running_normally || r->count == 0u))
        return;
    record_write(r, running_normally ? 0u : r->count, 1u);
}

uint32_t option_refusals(uint32_t optr, uint32_t *notes)
{
    uint32_t refusals = 0u, n = 0u;
    uint32_t borr = (optr >> FLASH_OPTR_BORR_LEV_POS) & FLASH_OPTR_BOR_LEV_FIELD;
    uint32_t borf = (optr >> FLASH_OPTR_BORF_LEV_POS) & FLASH_OPTR_BOR_LEV_FIELD;
    if (!(optr & FLASH_OPTR_BOR_EN_BIT))
        refusals |= BOOT_REFUSE_BOR_DISABLED;
    if (borr != OPTION_BOR_LEVEL_FIELD || borf != OPTION_BOR_LEVEL_FIELD)
        refusals |= BOOT_REFUSE_BOR_LEVEL;
    if (!(optr & FLASH_OPTR_nBOOT_SEL_BIT))
        n |= OPTION_NOTE_BOOT_PIN;
    else if (!(optr & FLASH_OPTR_nBOOT0_BIT))
        n |= OPTION_NOTE_BOOT_SYSTEM;
    if (optr & FLASH_OPTR_IWDG_SW_BIT)
        n |= OPTION_NOTE_IWDG_SOFTWARE;
    if (((optr >> FLASH_OPTR_NRST_MODE_POS) & FLASH_OPTR_NRST_MODE_FIELD) != 3u)
        n |= OPTION_NOTE_NRST_NOT_IO;
    if ((optr & FLASH_OPTR_RDP_MSK) != 0xAAu)
        n |= OPTION_NOTE_RDP_NOT_LEVEL0;
    if (notes)
        *notes = n;
    return refusals;
}

struct boot_decision boot_decide(struct reset_record *r, uint32_t csr, uint32_t optr, bool clock_ok)
{
    struct boot_decision d = {0};
    d.reset = reset_classify(csr);
    d.reset_count = r ? reset_record_update(r, csr) : RESET_LATCH_COUNT;
    if (d.reset_count >= RESET_LATCH_COUNT)
        d.refusals |= BOOT_REFUSE_RESET_LATCH;
    d.refusals |= option_refusals(optr, &d.option_notes);
    if (!clock_ok)
        d.refusals |= BOOT_REFUSE_CLOCK;
    d.allow_light = d.refusals == BOOT_REFUSE_NONE;
    return d;
}

enum boot_action boot_action_for(const struct boot_decision *d)
{
    if (!d || (d->refusals & BOOT_REFUSE_RESET_LATCH))
        return BOOT_PARK_OFF;
    if (d->refusals & BOOT_REFUSE_CLOCK)
        return BOOT_HALT_OFF;
    return d->allow_light && d->refusals == BOOT_REFUSE_NONE ? BOOT_RUN : BOOT_PARK_OFF;
}
