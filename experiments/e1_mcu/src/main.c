/*
 * E1 - Benchmark FIR 16-tap Q15 tren STM32F103 (Cortex-M3, 72 MHz), bare-metal.
 *
 * Phan 1  Thong luong: 4 phien ban FIR, kiem tra voi FIR_GOLDEN, dem chu ky bang
 *         DWT->CYCCNT (tat ngat khi do). Cortex-M3 KHONG co lenh SIMD/DSP (SMLAD),
 *         nen CMSIS-DSP chay nhanh ban C thuan, khong co tang toc SIMD nhu tren M4.
 * Phan 2  Do tre ngat: TIM2 10 kHz, ISR doc TIM2->CNT ngay dau ham -> so chu ky tu
 *         su kien timer den luc ISR chay. 3 kich ban: ranh / tai FIR / tai FIR + ngat
 *         uu tien cao hon (TIM3) chay ~20 us.
 * Phan 3  Cac pha de do dong bang dong ho van nang (RUN, SLEEP, STANDBY).
 *
 * Ket qua in qua USART1 (PA9, 115200 8N1) dang JSON giua @@JSON_BEGIN / @@JSON_END.
 */
#include "stm32f1xx.h"
#include "arm_math.h"
#include "fir.h"

/* ------------------------------------------------------------------ */
/* Clock, UART, bo dem chu ky                                          */
/* ------------------------------------------------------------------ */
static const char *clk_src = "?";

static void clock_init(void)
{
    /* 72 MHz tu HSE 8 MHz x 9. Neu HSE khong len (board khac), dung HSI/2 x 16 = 64 MHz */
    RCC->CR |= RCC_CR_HSEON;
    uint32_t t = 0;
    while (!(RCC->CR & RCC_CR_HSERDY) && ++t < 200000) { }
    int hse_ok = (RCC->CR & RCC_CR_HSERDY) != 0;

    FLASH->ACR = FLASH_ACR_PRFTBE | 2u;            /* 2 wait state cho 48-72 MHz */
    RCC->CFGR = RCC_CFGR_PPRE1_DIV2                 /* APB1 <= 36 MHz, timer APB1 = 2x */
              | (hse_ok ? (RCC_CFGR_PLLSRC | RCC_CFGR_PLLMULL9) : RCC_CFGR_PLLMULL16);
    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY)) { }
    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) { }
    if (!hse_ok) RCC->CR &= ~RCC_CR_HSEON;

    SystemCoreClock = hse_ok ? 72000000u : 64000000u;
    clk_src = hse_ok ? "HSE8MHz_x9" : "HSI_div2_x16";
}

static void uart_init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN | RCC_APB2ENR_IOPCEN | RCC_APB2ENR_USART1EN | RCC_APB2ENR_AFIOEN;
    GPIOA->CRH = (GPIOA->CRH & ~(0xFFu << 4)) | (0xBu << 4) | (0x4u << 8);  /* PA9 AF-PP, PA10 in */
    GPIOC->CRH = (GPIOC->CRH & ~(0xFu << 20)) | (0x2u << 20);                /* PC13 LED */
    USART1->BRR = (SystemCoreClock + 57600u) / 115200u;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE;
}

static void led(int on) { if (on) GPIOC->BRR = 1u << 13; else GPIOC->BSRR = 1u << 13; }

static void putc_(char c)
{
    while (!(USART1->SR & USART_SR_TXE)) { }
    USART1->DR = (uint8_t)c;
}
static void puts_(const char *s) { while (*s) putc_(*s++); }
static void put_u32(uint32_t v)
{
    char b[11]; int i = 10; b[i] = 0;
    do { b[--i] = (char)('0' + v % 10); v /= 10; } while (v);
    puts_(&b[i]);
}
static void put_i32(int32_t v) { if (v < 0) { putc_('-'); put_u32((uint32_t)-v); } else put_u32((uint32_t)v); }
static void put_fix2(uint32_t v100) { put_u32(v100 / 100); putc_('.'); putc_('0' + v100 / 10 % 10); putc_('0' + v100 % 10); }
static void kv_u(const char *k, uint32_t v, int comma) { puts_("\""); puts_(k); puts_("\": "); put_u32(v); if (comma) puts_(", "); }
static void kv_f(const char *k, uint32_t v100, int comma) { puts_("\""); puts_(k); puts_("\": "); put_fix2(v100); if (comma) puts_(", "); }
static void kv_s(const char *k, const char *v, int comma) { puts_("\""); puts_(k); puts_("\": \""); puts_(v); puts_("\""); if (comma) puts_(", "); }

/* DWT->CYCCNT; mot so chip "F103" nhai khong co DWT -> dung SysTick 24 bit thay the */
static int dwt_ok;
static void cyc_init(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    for (volatile int i = 0; i < 100; i++) { }
    dwt_ok = DWT->CYCCNT != 0;
    if (!dwt_ok) {
        SysTick->LOAD = 0xFFFFFFu;
        SysTick->VAL = 0;
        SysTick->CTRL = SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_ENABLE_Msk;
    }
}
static inline uint32_t cyc_now(void) { return dwt_ok ? DWT->CYCCNT : (0xFFFFFFu - SysTick->VAL); }
static inline uint32_t cyc_diff(uint32_t a, uint32_t b) { return dwt_ok ? b - a : ((b - a) & 0xFFFFFFu); }

/* ------------------------------------------------------------------ */
/* Phan 1: thong luong                                                 */
/* ------------------------------------------------------------------ */
#define N FIR_NUM_SAMPLES
#define RUNS 7

static int16_t y[N];
static fir_shift_t st_shift;
static fir_circ_t st_circ;
static arm_fir_instance_q15 st_cmsis;
static q15_t cmsis_state[FIR_NUM_TAPS + N];
static q15_t coeffs_rev[FIR_NUM_TAPS];   /* CMSIS can he so dao nguoc thoi gian */

typedef struct {
    const char *name;
    uint32_t cyc_min, cyc_med, cyc_max;    /* cho ca khoi N mau */
    uint32_t mismatches;
    int32_t first_bad;
} bench_t;

enum { V_SHIFT, V_CIRC, V_CMSIS, V_CMSIS_FAST, NV };
static bench_t res[NV] = {
    {"c_shift_loop"}, {"c_circular_unrolled"}, {"cmsis_arm_fir_q15"}, {"cmsis_arm_fir_fast_q15"}
};

static void run_variant(int v)
{
    switch (v) {
    case V_SHIFT: fir_shift_init(&st_shift); fir_shift_block(&st_shift, FIR_COEFFS, FIR_INPUT, y, N); break;
    case V_CIRC:  fir_circ_init(&st_circ);   fir_circ_block(&st_circ, FIR_COEFFS, FIR_INPUT, y, N); break;
    case V_CMSIS:
        arm_fir_init_q15(&st_cmsis, FIR_NUM_TAPS, coeffs_rev, cmsis_state, N);
        arm_fir_q15(&st_cmsis, (q15_t *)FIR_INPUT, y, N);
        break;
    case V_CMSIS_FAST:
        arm_fir_init_q15(&st_cmsis, FIR_NUM_TAPS, coeffs_rev, cmsis_state, N);
        arm_fir_fast_q15(&st_cmsis, (q15_t *)FIR_INPUT, y, N);
        break;
    }
}

static void sort_u32(uint32_t *a, int n)
{
    for (int i = 1; i < n; i++)
        for (int j = i; j > 0 && a[j - 1] > a[j]; j--) { uint32_t t = a[j]; a[j] = a[j - 1]; a[j - 1] = t; }
}

static uint32_t cyc_overhead;

static void bench_all(void)
{
    for (int k = 0; k < FIR_NUM_TAPS; k++) coeffs_rev[k] = FIR_COEFFS[FIR_NUM_TAPS - 1 - k];

    __disable_irq();
    uint32_t a = cyc_now(), b = cyc_now();
    cyc_overhead = cyc_diff(a, b);

    for (int v = 0; v < NV; v++) {
        uint32_t c[RUNS];
        for (int r = 0; r < RUNS; r++) {
            for (int i = 0; i < N; i++) y[i] = 0x5A5A;
            uint32_t t0 = cyc_now();
            run_variant(v);   /* gom ca init (rat nho so voi 1024 mau) */
            uint32_t t1 = cyc_now();
            c[r] = cyc_diff(t0, t1) - cyc_overhead;
        }
        long fb;
        res[v].mismatches = fir_check(y, N, &fb);
        res[v].first_bad = fb;
        sort_u32(c, RUNS);
        res[v].cyc_min = c[0];
        res[v].cyc_med = c[RUNS / 2];
        res[v].cyc_max = c[RUNS - 1];
    }
    __enable_irq();
}

/* Do tung mau mot cho ban circular: thoi gian xu ly co phu thuoc du lieu khong? */
static uint32_t ps_min = 0xFFFFFFFFu, ps_max;
static void per_sample_spread(void)
{
    __disable_irq();
    fir_circ_init(&st_circ);
    for (int i = 0; i < N; i++) {
        uint32_t t0 = cyc_now();
        fir_circ_block(&st_circ, FIR_COEFFS, &FIR_INPUT[i], &y[i], 1);
        uint32_t d = cyc_diff(t0, cyc_now()) - cyc_overhead;
        if (d < ps_min) ps_min = d;
        if (d > ps_max) ps_max = d;
    }
    __enable_irq();
}

/* ------------------------------------------------------------------ */
/* Phan 2: do tre ngat                                                 */
/* ------------------------------------------------------------------ */
#define LAT_SAMPLES 20000u        /* 2 s o 10 kHz */
#define LAT_BUCKETS 64            /* histogram theo buoc 4 chu ky: 0..255 chu ky */
#define HOG_CYCLES  1440u         /* TIM3 ISR ban ~20 us o 72 MHz */

static volatile uint32_t lat_n, lat_min, lat_max, lat_sum;
static volatile uint32_t lat_hist[LAT_BUCKETS], lat_over;
static volatile int lat_done;

void TIM2_IRQHandler(void)
{
    uint32_t c = TIM2->CNT;          /* chu ky ke tu su kien update (timer = HCLK) */
    TIM2->SR = ~TIM_SR_UIF;
    if (!lat_done) {
        if (c < lat_min) lat_min = c;
        if (c > lat_max) lat_max = c;
        lat_sum += c;
        if (c / 4 < LAT_BUCKETS) lat_hist[c / 4]++; else lat_over++;
        if (++lat_n >= LAT_SAMPLES) lat_done = 1;
    }
    (void)TIM2->SR;                  /* dam bao co da xoa truoc khi thoat ISR */
}

void TIM3_IRQHandler(void)
{
    TIM3->SR = ~TIM_SR_UIF;
    uint32_t t0 = cyc_now();
    while (cyc_diff(t0, cyc_now()) < HOG_CYCLES) { }
    (void)TIM3->SR;
}

typedef struct { const char *name; uint32_t n, min, max, sum, over; uint32_t hist[LAT_BUCKETS]; } lat_t;
static lat_t lat_res[3];

static void lat_run(int scenario)
{
    lat_n = 0; lat_min = 0xFFFFFFFFu; lat_max = 0; lat_sum = 0; lat_over = 0; lat_done = 0;
    for (int i = 0; i < LAT_BUCKETS; i++) lat_hist[i] = 0;

    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN | RCC_APB1ENR_TIM3EN;
    TIM2->CR1 = 0; TIM2->PSC = 0; TIM2->ARR = SystemCoreClock / 10000u - 1u;
    TIM2->EGR = TIM_EGR_UG; TIM2->SR = 0; TIM2->DIER = TIM_DIER_UIE;
    NVIC_SetPriority(TIM2_IRQn, 1);
    NVIC_ClearPendingIRQ(TIM2_IRQn);   /* xoa ngat treo tu kich ban truoc (gay mau CNT = 0) */
    NVIC_EnableIRQ(TIM2_IRQn);

    if (scenario == 2) {
        /* ~1 kHz, lech pha voi TIM2 de quet moi vi tri chen nhau */
        TIM3->CR1 = 0; TIM3->PSC = 1; TIM3->ARR = SystemCoreClock / 2000u + 11u;
        TIM3->EGR = TIM_EGR_UG; TIM3->SR = 0; TIM3->DIER = TIM_DIER_UIE;
        NVIC_SetPriority(TIM3_IRQn, 0);   /* uu tien CAO hon TIM2 */
        NVIC_ClearPendingIRQ(TIM3_IRQn);
        NVIC_EnableIRQ(TIM3_IRQn);
        TIM3->CR1 = TIM_CR1_CEN;
    }
    TIM2->CR1 = TIM_CR1_CEN;

    if (scenario == 0) {
        while (!lat_done) { __NOP(); }
    } else {
        fir_circ_init(&st_circ);
        while (!lat_done) fir_circ_block(&st_circ, FIR_COEFFS, FIR_INPUT, y, 64);
    }

    TIM2->CR1 = 0; TIM3->CR1 = 0;
    NVIC_DisableIRQ(TIM2_IRQn); NVIC_DisableIRQ(TIM3_IRQn);

    static const char *names[3] = {"idle_loop", "fir_load", "fir_load_plus_higher_prio_isr_20us"};
    lat_t *r = &lat_res[scenario];
    r->name = names[scenario];
    r->n = lat_n; r->min = lat_min; r->max = lat_max; r->sum = lat_sum; r->over = lat_over;
    for (int i = 0; i < LAT_BUCKETS; i++) r->hist[i] = lat_hist[i];
}

/* ------------------------------------------------------------------ */
/* Bao cao JSON                                                        */
/* ------------------------------------------------------------------ */
/* ns x 100 tu so chu ky */
static uint32_t ns100(uint32_t cycles) { return (uint32_t)((uint64_t)cycles * 100000u / (SystemCoreClock / 1000000u)); }

static void report(void)
{
    uint32_t mhz = SystemCoreClock / 1000000u;
    puts_("@@JSON_BEGIN\r\n{\r\n");
    puts_("\"label\": \"do\", \"experiment\": \"E1_mcu\", \"chip\": \"STM32F103 Cortex-M3\", ");
    kv_s("clock_source", clk_src, 1); kv_u("clock_mhz", mhz, 1);
    kv_s("cycle_counter", dwt_ok ? "DWT_CYCCNT" : "SysTick24", 1);
    kv_u("flash_wait_states", FLASH->ACR & 7u, 1);
    kv_u("counter_overhead_cycles", cyc_overhead, 1);
    kv_u("num_samples", N, 1); kv_u("num_taps", FIR_NUM_TAPS, 0);
    puts_(",\r\n\"variants\": [\r\n");
    for (int v = 0; v < NV; v++) {
        bench_t *b = &res[v];
        uint32_t cps100 = (uint32_t)((uint64_t)b->cyc_med * 100u / N);
        puts_(" {"); kv_s("variant", b->name, 1);
        puts_("\"correct\": "); puts_(b->mismatches ? "false, " : "true, ");
        kv_u("mismatches", b->mismatches, 1);
        puts_("\"first_bad\": "); put_i32(b->first_bad); puts_(", ");
        kv_u("block_cycles_min", b->cyc_min, 1); kv_u("block_cycles_median", b->cyc_med, 1);
        kv_u("block_cycles_max", b->cyc_max, 1);
        kv_f("cycles_per_sample", cps100, 1);
        kv_f("ns_per_sample", (uint32_t)((uint64_t)b->cyc_med * 100000u / ((uint64_t)mhz * N)), 1);
        kv_f("ksps", (uint32_t)((uint64_t)mhz * 100000u * 100u / cps100), 0);
        puts_(v == NV - 1 ? "}\r\n" : "},\r\n");
    }
    puts_("],\r\n\"per_sample_cycles_circular\": {");
    kv_u("min", ps_min, 1); kv_u("max", ps_max, 0);
    puts_("},\r\n\"irq_latency\": [\r\n");
    for (int s = 0; s < 3; s++) {
        lat_t *r = &lat_res[s];
        puts_(" {"); kv_s("scenario", r->name, 1);
        kv_u("samples", r->n, 1);
        kv_u("min_cycles", r->min, 1); kv_u("max_cycles", r->max, 1);
        kv_f("avg_cycles", (uint32_t)((uint64_t)r->sum * 100u / (r->n ? r->n : 1)), 1);
        kv_f("min_ns", ns100(r->min), 1); kv_f("max_ns", ns100(r->max), 1);
        kv_u("over_255_cycles", r->over, 1);
        puts_("\"hist_bucket4\": {");
        int first = 1;
        for (int i = 0; i < LAT_BUCKETS; i++) if (r->hist[i]) {
            if (!first) puts_(", ");
            first = 0;
            puts_("\""); put_u32(i * 4); puts_("\": "); put_u32(r->hist[i]);
        }
        puts_(s == 2 ? "}}\r\n" : "}},\r\n");
    }
    puts_("]\r\n}\r\n@@JSON_END\r\n");
}

/* ------------------------------------------------------------------ */
/* Phan 3: pha do dong                                                 */
/* ------------------------------------------------------------------ */
static volatile uint32_t ticks;
void SysTick_Handler(void) { ticks++; }

static void power_phases(void)
{
    puts_("@@PHASE RUN_FIR 20s: do dong ngay bay gio (CPU chay FIR lien tuc)\r\n");
    led(1);
    fir_circ_init(&st_circ);
    for (int q = 0; q < 80; q++) {          /* 80 x 0.25 s; 0.25 s an toan voi SysTick 24 bit */
        uint32_t t0 = cyc_now();
        while (cyc_diff(t0, cyc_now()) < SystemCoreClock / 4)
            fir_circ_block(&st_circ, FIR_COEFFS, FIR_INPUT, y, 64);
    }
    led(0);

    puts_("@@PHASE SLEEP 20s: WFI, chi SysTick 1 kHz danh thuc\r\n");
    while (!(USART1->SR & USART_SR_TC)) { }
    SysTick->LOAD = SystemCoreClock / 1000u - 1u;
    SysTick->VAL = 0;
    SysTick->CTRL = SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk;
    ticks = 0;
    while (ticks < 20000u) __WFI();
    SysTick->CTRL = 0;

    puts_("@@PHASE STANDBY: dong thap nhat, nhan RESET de chay lai\r\n");
    while (!(USART1->SR & USART_SR_TC)) { }
    RCC->APB1ENR |= RCC_APB1ENR_PWREN;
    PWR->CR |= PWR_CR_CWUF | PWR_CR_PDDS;
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __DSB();
    __WFI();
    while (1) { }
}

int main(void)
{
    clock_init();
    uart_init();
    cyc_init();
    led(0);

    puts_("\r\n@@E1 STM32F103 FIR16 benchmark, clock ");
    put_u32(SystemCoreClock / 1000000u); puts_(" MHz ("); puts_(clk_src); puts_(")\r\n");

    bench_all();
    per_sample_spread();
    puts_("@@phan 1 xong, dang do do tre ngat (~6 s)\r\n");
    for (int s = 0; s < 3; s++) lat_run(s);
    report();
    power_phases();
}
