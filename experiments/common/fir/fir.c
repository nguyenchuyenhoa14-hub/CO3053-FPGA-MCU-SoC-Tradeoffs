#include <string.h>
#include "fir.h"

static inline int16_t sat16(int32_t v)
{
    if (v > 32767) return 32767;
    if (v < -32768) return -32768;
    return (int16_t)v;
}

/* Dich phai so hoc (floor). GCC tren ARM va x86 deu dich so hoc voi so am. */
static inline int16_t q15_out(int32_t acc)
{
    return sat16(acc >> 15);
}

void fir_shift_init(fir_shift_t *s)
{
    memset(s, 0, sizeof(*s));
}

void fir_shift_block(fir_shift_t *s, const int16_t *h, const int16_t *x, int16_t *y, size_t n)
{
    for (size_t i = 0; i < n; i++) {
        for (int k = FIR_NUM_TAPS - 1; k > 0; k--)
            s->delay[k] = s->delay[k - 1];
        s->delay[0] = x[i];

        int32_t acc = 0;
        for (int k = 0; k < FIR_NUM_TAPS; k++)
            acc += (int32_t)h[k] * s->delay[k];
        y[i] = q15_out(acc);
    }
}

void fir_circ_init(fir_circ_t *s)
{
    memset(s, 0, sizeof(*s));
}

/*
 * Ghi moi mau vao 2 vi tri (pos va pos+TAPS) de cua so 16 mau gan nhat luon
 * nam lien tuc trong bo nho: d[0] = x[n-15], ..., d[15] = x[n].
 */
void fir_circ_block(fir_circ_t *s, const int16_t *h, const int16_t *x, int16_t *y, size_t n)
{
    unsigned pos = s->pos;
    for (size_t i = 0; i < n; i++) {
        s->buf[pos] = x[i];
        s->buf[pos + FIR_NUM_TAPS] = x[i];
        pos = (pos + 1) & (FIR_NUM_TAPS - 1);
        const int16_t *d = &s->buf[pos];

        int32_t acc;
        acc  = (int32_t)h[15] * d[0];
        acc += (int32_t)h[14] * d[1];
        acc += (int32_t)h[13] * d[2];
        acc += (int32_t)h[12] * d[3];
        acc += (int32_t)h[11] * d[4];
        acc += (int32_t)h[10] * d[5];
        acc += (int32_t)h[9]  * d[6];
        acc += (int32_t)h[8]  * d[7];
        acc += (int32_t)h[7]  * d[8];
        acc += (int32_t)h[6]  * d[9];
        acc += (int32_t)h[5]  * d[10];
        acc += (int32_t)h[4]  * d[11];
        acc += (int32_t)h[3]  * d[12];
        acc += (int32_t)h[2]  * d[13];
        acc += (int32_t)h[1]  * d[14];
        acc += (int32_t)h[0]  * d[15];
        y[i] = q15_out(acc);
    }
    s->pos = pos;
}

size_t fir_check(const int16_t *y, size_t n, long *first_bad)
{
    size_t bad = 0;
    *first_bad = -1;
    for (size_t i = 0; i < n && i < FIR_NUM_SAMPLES; i++) {
        if (y[i] != FIR_GOLDEN[i]) {
            if (bad == 0) *first_bad = (long)i;
            bad++;
        }
    }
    return bad;
}
