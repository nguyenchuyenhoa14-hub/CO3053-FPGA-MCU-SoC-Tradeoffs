#!/usr/bin/env python3
"""
Doc ket qua tu board qua SWD (ST-Link) hoac cong serial va luu JSON vao experiments/results/.

    python capture_serial.py mcu  swd              # STM32F103: doc SRAM truc tiep qua ST-Link SWD (khong can USB-UART)
    python capture_serial.py mcu  /dev/ttyUSB0     # STM32F103: doc USART1 (PA9) qua USB-UART
    python capture_serial.py fpga /dev/ttyUSB1     # Arty Z7-20: doc UART tu chan Pmod JA[0] (Y18)

Can pyserial khi doc qua cong serial (pip install pyserial).
"""
import glob
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def _print_mcu_summary(data, path):
    for v in data["variants"]:
        print(f"  {v['variant']:26s} correct={v['correct']}  {v['cycles_per_sample']:7.2f} chu ky/mau"
              f"  {v['ksps']:8.2f} kS/s")
    for r in data["irq_latency"]:
        print(f"  IRQ {r['scenario']:38s} min={r['min_cycles']} max={r['max_cycles']} chu ky"
              f" ({r['min_ns']:.0f}-{r['max_ns']:.0f} ns)")
    print(f"-> {path}")


def _find_pio_tool(pkg_dir, binary_name):
    home = os.path.expanduser("~")
    candidates = [
        shutil.which(binary_name),
        os.path.join(home, ".platformio", "packages", pkg_dir, "bin", binary_name),
        os.path.join(home, ".platformio", "packages", pkg_dir, "bin", binary_name + ".exe"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    sys.exit(f"Khong tim thay cong cu {binary_name} trong PATH hoac ~/.platformio/packages/{pkg_dir}")


def capture_mcu_swd():
    openocd = _find_pio_tool("tool-openocd", "openocd")
    nm_bin = _find_pio_tool("toolchain-gccarmnoneeabi", "arm-none-eabi-nm")

    elf_candidates = glob.glob(os.path.join(ROOT, "e1_mcu", ".pio", "build", "*", "firmware.elf"))
    if not elf_candidates:
        sys.exit("Chua co firmware.elf, chay: pio run -d e1_mcu -t upload")
    elf_path = max(elf_candidates, key=os.path.getmtime)

    nm_out = subprocess.check_output([nm_bin, "-n", elf_path], text=True)
    syms = {}
    for line in nm_out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            syms[parts[2]] = int(parts[0], 16)

    for req in ("SystemCoreClock", "cyc_overhead", "ps_min", "ps_max", "res", "lat_res"):
        if req not in syms:
            sys.exit(f"Khong tim thay symbol '{req}' trong {elf_path}")

    print("Reset STM32F103 qua ST-Link SWD va cho benchmark chay (~9 giay)...")
    subprocess.run([openocd, "-f", "interface/stlink.cfg", "-f", "target/stm32f1x.cfg",
                    "-c", "init; reset run; shutdown"], check=True)
    time.sleep(9.5)

    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tf:
        ram_file = tf.name.replace("\\", "/")

    try:
        subprocess.run([openocd, "-f", "interface/stlink.cfg", "-f", "target/stm32f1x.cfg",
                        "-c", f"init; halt; dump_image {ram_file} 0x20000000 0x2800; resume; shutdown"],
                       check=True)
        ram = open(ram_file, "rb").read()
    finally:
        if os.path.exists(ram_file):
            os.remove(ram_file)

    def u32_at(addr):
        off = addr - 0x20000000
        return struct.unpack("<I", ram[off:off + 4])[0]

    sys_clk = u32_at(syms["SystemCoreClock"])
    mhz = sys_clk // 1_000_000
    clk_src = "HSE8MHz_x9" if mhz == 72 else "HSI_div2_x16"
    cyc_overhead = u32_at(syms["cyc_overhead"])
    ps_min = u32_at(syms["ps_min"])
    ps_max = u32_at(syms["ps_max"])

    num_samples, num_taps = 1024, 16
    variant_names = ["c_shift_loop", "c_circular_unrolled", "cmsis_arm_fir_q15", "cmsis_arm_fir_fast_q15"]
    variants = []
    res_base = syms["res"] - 0x20000000
    for i, vname in enumerate(variant_names):
        off = res_base + i * 24
        _, c_min, c_med, c_max, mismatches, first_bad = struct.unpack("<IIIIii", ram[off:off + 24])
        cps = round(c_med / num_samples, 2)
        ns_ps = round((c_med * 1000.0) / (mhz * num_samples), 2)
        ksps = round(mhz * 1000.0 / cps, 2)
        variants.append({
            "variant": vname,
            "correct": mismatches == 0,
            "mismatches": mismatches,
            "first_bad": first_bad,
            "block_cycles_min": c_min,
            "block_cycles_median": c_med,
            "block_cycles_max": c_max,
            "cycles_per_sample": cps,
            "ns_per_sample": ns_ps,
            "ksps": ksps,
        })

    scen_names = ["idle_loop", "fir_load", "fir_load_plus_higher_prio_isr_20us"]
    latencies = []
    lat_base = syms["lat_res"] - 0x20000000
    for s, sname in enumerate(scen_names):
        off = lat_base + s * 280
        _, n, lat_min, lat_max, lat_sum, over = struct.unpack("<IIIIII", ram[off:off + 24])
        hist_raw = struct.unpack("<64I", ram[off + 24:off + 280])
        hist = {str(i * 4): hist_raw[i] for i in range(64) if hist_raw[i] > 0}
        latencies.append({
            "scenario": sname,
            "samples": n,
            "min_cycles": lat_min,
            "max_cycles": lat_max,
            "avg_cycles": round(lat_sum / (n if n else 1), 2),
            "min_ns": round(lat_min * 1000.0 / mhz, 2),
            "max_ns": round(lat_max * 1000.0 / mhz, 2),
            "over_255_cycles": over,
            "hist_bucket4": hist,
        })

    data = {
        "label": "đo",
        "experiment": "E1_mcu",
        "chip": "STM32F103 Cortex-M3",
        "board": "Blue Pill (STM32F103C6)",
        "clock_source": clk_src,
        "clock_mhz": mhz,
        "cycle_counter": "DWT_CYCCNT",
        "flash_wait_states": 2,
        "counter_overhead_cycles": cyc_overhead,
        "num_samples": num_samples,
        "num_taps": num_taps,
        "variants": variants,
        "per_sample_cycles_circular": {"min": ps_min, "max": ps_max},
        "irq_latency": latencies,
    }
    path = os.path.join(RESULTS, "e1_mcu.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _print_mcu_summary(data, path)


def capture_mcu(port):
    if port.lower() in ("swd", "stlink"):
        return capture_mcu_swd()

    import serial
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
        json.dump(data, f, indent=2, ensure_ascii=False)
    _print_mcu_summary(data, path)
    print("Board dang o pha do dong (RUN 20 s -> SLEEP 20 s -> STANDBY). Ghi so dong vao results/e1_mcu_power.json")


LINE_RE = re.compile(r"FIR16 (PASS|FAIL) N=([0-9A-F]{4}) ERR=([0-9A-F]{4}) LAT=([0-9A-F]{4}) "
                     r"CYC=([0-9A-F]{8}) FBAD=([0-9A-F]{4})")


def capture_fpga(port, clock_mhz=125.0):
    import serial
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
        "dsp_mode": "none (LUT-only)",
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
