#!/usr/bin/env python3
"""
Doc ket qua tu board qua cong serial va luu JSON vao experiments/results/.

    python capture_serial.py mcu  /dev/ttyUSB0     # STM32F103, USART1 qua USB-UART
    python capture_serial.py fpga /dev/ttyUSB1     # Arty Z7-20 (UART tu chan Pmod JA[0] = Y18)

Can pyserial (co san trong venv PlatformIO, hoac: pip install pyserial).
Nhan RESET (Blue Pill) hoac BTN0/BTN1 (Arty Z7-20) sau khi chay script.
"""
import json
import os
import re
import sys
import time

import serial

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def capture_mcu(port):
    out_raw = os.path.join(RESULTS, "e1_mcu_raw.txt")
    buf, in_json, raw = [], False, []
    print("Cho board... (nhan RESET tren Blue Pill)")
    with serial.Serial(port, 115200, timeout=1) as ser:
        t_end = time.time() + 120
        while time.time() < t_end:
            line = ser.readline().decode("ascii", "replace").rstrip("\r\n")
            if not line:
                continue
            raw.append(line)
            if line.startswith("@@"):
                print(line)
            if line == "@@JSON_BEGIN":
                in_json, buf = True, []
            elif line == "@@JSON_END":
                break
            elif in_json:
                buf.append(line)
    with open(out_raw, "w", encoding="utf-8") as f:
        f.write("\n".join(raw) + "\n")
    if not buf:
        sys.exit(f"Khong nhan duoc JSON, xem {out_raw}")
    data = json.loads("\n".join(buf))
    path = os.path.join(RESULTS, "e1_mcu.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    for v in data["variants"]:
        print(f"  {v['variant']:26s} correct={v['correct']}  {v['cycles_per_sample']:7.2f} chu ky/mau"
              f"  {v['ksps']:8.1f} kS/s")
    for r in data["irq_latency"]:
        print(f"  IRQ {r['scenario']:38s} min={r['min_cycles']} max={r['max_cycles']} chu ky"
              f" ({r['min_ns']:.0f}-{r['max_ns']:.0f} ns)")
    print(f"-> {path}")
    print("Board dang o pha do dong (RUN 20 s -> SLEEP 20 s -> STANDBY). Ghi so dong vao results/e1_mcu_power.json")


LINE_RE = re.compile(r"FIR16 (PASS|FAIL) N=([0-9A-F]{4}) ERR=([0-9A-F]{4}) LAT=([0-9A-F]{4}) "
                     r"CYC=([0-9A-F]{8}) FBAD=([0-9A-F]{4})")


def capture_fpga(port, clock_mhz=125.0):
    print("Cho board... (nhan BTN0 hoac BTN1 tren Arty Z7-20)")
    with serial.Serial(port, 115200, timeout=1) as ser:
        t_end = time.time() + 60
        while time.time() < t_end:
            line = ser.readline().decode("ascii", "replace").strip()
            m = LINE_RE.search(line)
            if m:
                print(line)
                break
        else:
            sys.exit("Khong nhan duoc dong FIR16 tu FPGA")
    status, n, err, lat, cyc, fbad = m.groups()
    n, err, lat, cyc, fbad = (int(x, 16) for x in (n, err, lat, cyc, fbad))
    data = {
        "label": "do",
        "experiment": "E2_fpga_on_board",
        "board": "Digilent Arty Z7-20",
        "part": "xc7z020clg400-1",
        "clock_mhz": clock_mhz,
        "pass": status == "PASS",
        "num_samples": n,
        "mismatches": err,
        "first_bad": None if fbad == 0xFFFF else fbad,
        "latency_cycles": lat,
        "cycles_first_in_to_last_out": cyc,
        "samples_per_cycle": round(n / (cyc - lat), 4),
        "throughput_msps": round(n / (cyc - lat) * clock_mhz, 2),
        "latency_ns": round(lat * 1000.0 / clock_mhz, 1),
        "raw": line,
    }
    path = os.path.join(RESULTS, "e2_fpga_board.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"  {status}: {n} mau, sai {err}, do tre {lat} chu ky ({data['latency_ns']} ns), {data['samples_per_cycle']} mau/chu ky ({data['throughput_msps']} MSPS)")
    print(f"-> {path}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("mcu", "fpga"):
        sys.exit(__doc__)
    os.makedirs(RESULTS, exist_ok=True)
    (capture_mcu if sys.argv[1] == "mcu" else capture_fpga)(sys.argv[2])
