/*
 * E3 - Benchmark FIR 16-tap Q15 tren SoC Linux (Raspberry Pi 4, Cortex-A72).
 *
 * 1. Kiem tra dung voi FIR_GOLDEN (cung vector voi MCU va FPGA).
 * 2. Do thong luong: xu ly lap lai khoi 1024 mau, ghim vao 1 loi, lay median.
 * In ket qua dang JSON ra stdout.
 */
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/utsname.h>
#include "fir.h"

#define REPEAT_BLOCKS 2000   /* 2000 x 1024 = ~2 trieu mau moi lan do */
#define RUNS 15

static int16_t out[FIR_NUM_SAMPLES];
static volatile int16_t sink;

static double now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}

static int cmp_double(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

typedef void (*block_fn)(void *state, const int16_t *x, int16_t *y, size_t n);
static void run_shift(void *s, const int16_t *x, int16_t *y, size_t n) { fir_shift_block(s, FIR_COEFFS, x, y, n); }
static void run_circ(void *s, const int16_t *x, int16_t *y, size_t n) { fir_circ_block(s, FIR_COEFFS, x, y, n); }

static void bench(const char *name, block_fn fn, void *state, void (*init)(void *), int last)
{
    /* Kiem tra dung */
    init(state);
    fn(state, FIR_INPUT, out, FIR_NUM_SAMPLES);
    long first_bad;
    size_t bad = fir_check(out, FIR_NUM_SAMPLES, &first_bad);

    /* Khoi dong (lam nong cache, CPU governor) */
    for (int i = 0; i < 200; i++) fn(state, FIR_INPUT, out, FIR_NUM_SAMPLES);

    double ns_per_sample[RUNS];
    for (int r = 0; r < RUNS; r++) {
        double t0 = now_ns();
        for (int b = 0; b < REPEAT_BLOCKS; b++) {
            fn(state, FIR_INPUT, out, FIR_NUM_SAMPLES);
            sink = out[b & (FIR_NUM_SAMPLES - 1)];
        }
        double t1 = now_ns();
        ns_per_sample[r] = (t1 - t0) / ((double)REPEAT_BLOCKS * FIR_NUM_SAMPLES);
    }
    qsort(ns_per_sample, RUNS, sizeof(double), cmp_double);
    double med = ns_per_sample[RUNS / 2];

    printf("    {\"variant\": \"%s\", \"correct\": %s, \"mismatches\": %zu, \"first_bad\": %ld,\n"
           "     \"ns_per_sample_min\": %.3f, \"ns_per_sample_median\": %.3f, \"ns_per_sample_max\": %.3f,\n"
           "     \"msps_median\": %.2f, \"mmac_per_s_median\": %.1f}%s\n",
           name, bad ? "false" : "true", bad, first_bad,
           ns_per_sample[0], med, ns_per_sample[RUNS - 1],
           1e3 / med, 1e3 / med * FIR_NUM_TAPS, last ? "" : ",");
}

static void init_shift(void *s) { fir_shift_init(s); }
static void init_circ(void *s) { fir_circ_init(s); }

int main(int argc, char **argv)
{
    int cpu = argc > 1 ? atoi(argv[1]) : 3;
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    int pinned = sched_setaffinity(0, sizeof(set), &set) == 0;

    struct utsname u;
    uname(&u);

    fir_shift_t s1;
    fir_circ_t s2;

    printf("{\n  \"label\": \"do\",\n  \"experiment\": \"E3_soc_fir\",\n");
    printf("  \"machine\": \"%s\", \"kernel\": \"%s %s\",\n", u.machine, u.release, u.version);
    printf("  \"pinned_cpu\": %d, \"pinned_ok\": %s,\n", cpu, pinned ? "true" : "false");
    printf("  \"samples_per_run\": %d, \"runs\": %d,\n", REPEAT_BLOCKS * FIR_NUM_SAMPLES, RUNS);
#ifdef BUILD_FLAGS
    printf("  \"build_flags\": \"%s\",\n", BUILD_FLAGS);
#endif
    printf("  \"variants\": [\n");
    bench("shift_loop", run_shift, &s1, init_shift, 0);
    bench("circular_unrolled", run_circ, &s2, init_circ, 1);
    printf("  ]\n}\n");
    return 0;
}
