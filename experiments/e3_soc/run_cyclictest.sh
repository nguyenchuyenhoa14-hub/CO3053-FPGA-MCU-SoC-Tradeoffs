#!/usr/bin/env bash
# E3b - Do do tre lap lich xau nhat tren Raspberry Pi 4 bang cyclictest (chay tren Pi, can sudo).
# Kiem chung chéo so lieu AC6 trong PLAN.md: Linux thuong "vai ms", PREEMPT_RT 30-80 us.
#
#   sudo apt install rt-tests stress-ng
#   sudo ./run_cyclictest.sh            # mac dinh 100000 vong x 2 kich ban
#   LOOPS=600000 sudo ./run_cyclictest.sh   # ~2 phut moi kich ban, nen dung cho so lieu cuoi
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../results

LOOPS=${LOOPS:-100000}
INTERVAL_US=200
KERNEL_TAG=$(uname -v | grep -q PREEMPT_RT && echo rt || echo std)

command -v cyclictest >/dev/null || { echo "Thieu cyclictest: sudo apt install rt-tests"; exit 1; }
command -v stress-ng  >/dev/null || { echo "Thieu stress-ng: sudo apt install stress-ng"; exit 1; }
[ "$(id -u)" -eq 0 ] || { echo "Can chay voi sudo (SCHED_FIFO + mlockall)"; exit 1; }

run_case() {
    local load=$1
    local out="../results/e3_cyclictest_${KERNEL_TAG}_${load}"
    local stress_pid=""
    if [ "$load" = "load" ]; then
        # Tai nang: CPU + bo nho + I/O + nhieu ngat, tren ca 4 loi
        stress-ng --cpu 4 --vm 2 --vm-bytes 256M --io 2 --timeout 0 >/dev/null 2>&1 &
        stress_pid=$!
        sleep 3
    fi
    echo "== cyclictest kernel=$KERNEL_TAG tai=$load loops=$LOOPS"
    # -m: mlockall, -p 95: SCHED_FIFO 95, -t1 -a3: 1 thread ghim loi 3, -h: histogram (us)
    cyclictest -m -p 95 -t1 -a3 -i "$INTERVAL_US" -l "$LOOPS" -h 2000 -q > "$out.hist"
    [ -n "$stress_pid" ] && kill "$stress_pid" && wait "$stress_pid" 2>/dev/null || true

    python3 - "$out.hist" "$out.json" "$KERNEL_TAG" "$load" "$LOOPS" "$INTERVAL_US" "$(uname -r)" <<'EOF'
import json, re, sys
hist, out, kernel, load, loops, interval, release = sys.argv[1:]
mn = mx = avg = ovf = None
buckets = {}
for line in open(hist):
    if line.startswith("# Min Latencies"): mn = int(line.split()[-1])
    elif line.startswith("# Avg Latencies"): avg = int(line.split()[-1])
    elif line.startswith("# Max Latencies"): mx = int(line.split()[-1])
    elif line.startswith("# Histogram Overflows"): ovf = int(line.split()[-1])
    elif re.match(r"^\d+\s+\d+", line):
        us, cnt = map(int, line.split()[:2])
        if cnt: buckets[us] = cnt
total = sum(buckets.values())
def pct(p):
    acc = 0
    for us in sorted(buckets):
        acc += buckets[us]
        if acc >= p * total: return us
res = {"label": "do", "experiment": "E3_cyclictest", "kernel": kernel, "kernel_release": release,
       "load": load, "loops": int(loops), "interval_us": int(interval),
       "min_us": mn, "avg_us": avg, "max_us": mx, "p99_us": pct(0.99), "p9999_us": pct(0.9999),
       "histogram_overflows": ovf, "histogram_us": buckets}
json.dump(res, open(out, "w"), indent=1)
print(f"   min={mn} avg={avg} p99={res['p99_us']} max={mx} us  -> {out}")
EOF
}

run_case idle
run_case load
