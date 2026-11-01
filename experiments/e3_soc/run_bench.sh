#!/usr/bin/env bash
# E3a - Bien dich va chay benchmark FIR tren Raspberry Pi 4 (chay script NAY tren Pi).
# Ket qua: ../results/e3_soc_fir_<may>.json
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build ../results

MACHINE=$(uname -m)
if [ "$MACHINE" = "aarch64" ]; then
    CPUFLAGS="-mcpu=cortex-a72"
else
    CPUFLAGS="-march=native"   # chi de thu tren laptop, KHONG phai so lieu SoC
fi

run_variant() {
    local tag=$1; shift
    local flags="$*"
    gcc $flags $CPUFLAGS -Wall -Wextra -I../common/fir -DBUILD_FLAGS="\"$flags $CPUFLAGS\"" \
        fir_bench.c ../common/fir/fir.c -o "build/fir_bench_$tag"
    ./build/fir_bench_"$tag" 3 > "../results/e3_soc_fir_${MACHINE}_${tag}.json"
    echo "-> results/e3_soc_fir_${MACHINE}_${tag}.json"
}

# Ghi lai thong tin he thong de bao cao
{
    echo "== $(date -Is)"; uname -a
    [ -r /proc/device-tree/model ] && tr -d '\0' < /proc/device-tree/model && echo
    cat /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor 2>/dev/null || true
    cat /sys/devices/system/cpu/cpu3/cpufreq/scaling_cur_freq 2>/dev/null || true
    vcgencmd measure_temp 2>/dev/null || true
    vcgencmd get_throttled 2>/dev/null || true
} > "../results/e3_sysinfo_${MACHINE}.txt"

# O2 khong tu vector hoa; O3 cho phep GCC dung NEON tu dong
run_variant O2 -O2 -fno-tree-vectorize
run_variant O3 -O3
