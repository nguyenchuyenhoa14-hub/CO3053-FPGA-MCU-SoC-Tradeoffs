/*
 * E3-sim: chuong trinh nho de dem so lenh ARMv8 thuc thi tren moi mau FIR.
 *   ./count_insn <variant 0|1> <so lan lap K>
 * Chay voi K=1 va K=2 duoi QEMU (che do 1 lenh/khoi), lay hieu so lenh / 1024
 * -> so lenh moi mau, da loai bo phan khoi dong libc va kiem tra ket qua.
 */
#include <stdio.h>
#include <stdlib.h>
#include "fir.h"

static int16_t out[FIR_NUM_SAMPLES];
static volatile int16_t sink;

int main(int argc, char **argv)
{
    int variant = argc > 1 ? atoi(argv[1]) : 1;
    int reps = argc > 2 ? atoi(argv[2]) : 1;
    fir_shift_t s1;
    fir_circ_t s2;
    fir_shift_init(&s1);
    fir_circ_init(&s2);
    for (int r = 0; r < reps; r++) {
        if (variant == 0) fir_shift_block(&s1, FIR_COEFFS, FIR_INPUT, out, FIR_NUM_SAMPLES);
        else              fir_circ_block(&s2, FIR_COEFFS, FIR_INPUT, out, FIR_NUM_SAMPLES);
        sink = out[r & (FIR_NUM_SAMPLES - 1)];
    }
    return 0;
}
