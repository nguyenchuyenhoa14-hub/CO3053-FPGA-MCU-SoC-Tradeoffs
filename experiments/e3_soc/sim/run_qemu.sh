#!/usr/bin/env bash
# ============================================================================
# E3-sim: mo phong SoC (Cortex-A72, ARMv8) bang QEMU user-mode trong Docker.
#
#   ./run_qemu.sh            -> results/e3_soc_sim.json
#
# Chay trong container debian:bookworm-slim (x86) co san cross-compiler aarch64 va
# qemu-aarch64; goi QEMU truc tiep nen KHONG can dang ky binfmt tren may host.
#
# QEMU KHONG mo phong thoi gian cua Cortex-A72, nen script nay chi lay:
#   1. Tinh dung bit-exact cua fir_bench tren ISA ARMv8 (-mcpu=cortex-a72)  [mo phong]
#   2. So lenh thuc thi tren moi mau (dem bang log -singlestep -d exec)      [mo phong]
# Thong luong duoc collect.py UOC LUONG tu so lenh/mau va gia dinh IPC.
# So MSPS ma fir_bench in ra khi chay duoi QEMU la toc do mo phong cua may host,
# KHONG duoc dung.
# ============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
EXP="$(cd "$HERE/../.." && pwd)"
mkdir -p "$EXP/results"

docker run --rm -e HOST_ID="$(id -u):$(id -g)" -v "$EXP:/exp:ro" -v "$EXP/results:/out" debian:bookworm-slim bash -euo pipefail -c '
apt-get update -qq >/dev/null
apt-get install -y -qq --no-install-recommends gcc-aarch64-linux-gnu libc6-dev-arm64-cross \
    qemu-user >/dev/null 2>&1
mkdir -p /w && cd /w
CC=aarch64-linux-gnu-gcc
INC="-I/exp/common/fir"
SRC=/exp/common/fir/fir.c
QEMU="qemu-aarch64 -cpu cortex-a72"

for OPT in O2 O3; do
  FLAGS="-$OPT -mcpu=cortex-a72 -static"
  [ $OPT = O2 ] && FLAGS="$FLAGS -fno-tree-vectorize"
  $CC $FLAGS -Wall $INC -DBUILD_FLAGS="\"$FLAGS\"" /exp/e3_soc/fir_bench.c $SRC -o bench_$OPT
  $CC $FLAGS -Wall $INC /exp/e3_soc/sim/count_insn.c $SRC -o count_$OPT
  # 1) Tinh dung: chay fir_bench duoi QEMU, chi giu truong "correct"/"mismatches"
  $QEMU ./bench_$OPT 0 > bench_$OPT.json
  # 2) Dem lenh: K=1 va K=2 cho tung phien ban
  for V in 0 1; do
    for K in 1 2; do
      $QEMU -singlestep -d exec,nochain -D trace_${OPT}_${V}_${K}.log ./count_$OPT $V $K
      grep -c "^Trace" trace_${OPT}_${V}_${K}.log > n_${OPT}_${V}_${K}.txt
      rm trace_${OPT}_${V}_${K}.log
    done
  done
done

mkdir -p /out/e3_sim_raw
cp bench_*.json n_*.txt /out/e3_sim_raw/
echo "gcc $(aarch64-linux-gnu-gcc -dumpversion)" > /out/e3_sim_raw/toolchain.txt
qemu-aarch64 --version | head -1 >> /out/e3_sim_raw/toolchain.txt
chown -R "$HOST_ID" /out/e3_sim_raw
'
python3 "$HERE/summarize.py" "$EXP/results"
