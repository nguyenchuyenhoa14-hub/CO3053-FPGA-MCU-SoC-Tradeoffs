/*
 * FIR 16-tap Q15 dung chung cho MCU (STM32F103) va SoC (Raspberry Pi 4).
 * Dac ta so hoc: y[n] = sat16(floor(sum h[k]*x[n-k] / 2^15)), xem e0_golden/gen_vectors.py
 */
#ifndef FIR_H
#define FIR_H

#include <stdint.h>
#include <stddef.h>
#include "fir_vectors.h"

/* Phien ban 1: dich duong tre moi mau + vong lap (cach viet "sach giao khoa") */
typedef struct {
    int16_t delay[FIR_NUM_TAPS];
} fir_shift_t;

/* Phien ban 2: bo dem vong lap doi (khong phai dich du lieu), MAC khai trien */
typedef struct {
    int16_t buf[2 * FIR_NUM_TAPS];
    unsigned pos;
} fir_circ_t;

void fir_shift_init(fir_shift_t *s);
void fir_shift_block(fir_shift_t *s, const int16_t *h, const int16_t *x, int16_t *y, size_t n);

void fir_circ_init(fir_circ_t *s);
void fir_circ_block(fir_circ_t *s, const int16_t *h, const int16_t *x, int16_t *y, size_t n);

/* So voi FIR_GOLDEN; tra ve so mau sai, ghi chi so sai dau tien vao *first_bad (-1 neu khong co) */
size_t fir_check(const int16_t *y, size_t n, long *first_bad);

#endif
