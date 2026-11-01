#!/usr/bin/env python3
"""
E0 - Golden model cho FIR 16-tap Q15.

Nguon chuan duy nhat cho ca 3 nen tang: sinh he so, vector dau vao va ket qua
mong doi, roi xuat ra dinh dang cho C (MCU, Pi) va Verilog (FPGA).

Dac ta so hoc (moi implementation phai theo dung):
    acc  = sum_{k=0}^{15} h[k] * x[n-k]      (so nguyen, khong tran)
    y[n] = sat16(floor(acc / 2^15))          (dich phai so hoc, bao hoa 16-bit)
Trang thai ban dau x[n<0] = 0. Toan bo vector la MOT luong lien tuc.

Chi dung thu vien chuan Python de chay duoc tren may nao cung duoc.
"""

import json
import math
import os
import random

NUM_TAPS = 16
Q = 15
NUM_SAMPLES = 1024
SEED = 3053

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = {
    "c_header": os.path.join(ROOT, "common", "fir", "fir_vectors.h"),
    "vh_coeffs": os.path.join(ROOT, "e2_fpga", "rtl", "fir_coeffs.vh"),
    "hex_in": os.path.join(ROOT, "e2_fpga", "mem", "vectors_in.hex"),
    "hex_gold": os.path.join(ROOT, "e2_fpga", "mem", "golden_out.hex"),
    "spec": os.path.join(ROOT, "results", "e0_spec.json"),
}


def design_coeffs():
    """Low-pass windowed-sinc (Hamming), fc = 0.2*fs, he so khuech dai DC = 1."""
    fc = 0.2
    m = NUM_TAPS - 1
    h = []
    for n in range(NUM_TAPS):
        t = n - m / 2
        sinc = 2 * fc if t == 0 else math.sin(2 * math.pi * fc * t) / (math.pi * t)
        win = 0.54 - 0.46 * math.cos(2 * math.pi * n / m)
        h.append(sinc * win)
    s = sum(h)
    h = [v / s for v in h]
    hq = [int(round(v * (1 << Q))) for v in h]
    # Sua sai so lam tron o 2 tap giua (giu doi xung) de tong dung bang 2^15
    hq[NUM_TAPS // 2 - 1] += ((1 << Q) - sum(hq)) // 2
    hq[NUM_TAPS // 2] = hq[NUM_TAPS // 2 - 1]
    return hq


def sat16(v):
    return max(-32768, min(32767, v))


def fir_golden(h, x):
    delay = [0] * NUM_TAPS
    y = []
    for s in x:
        delay = [s] + delay[:-1]
        acc = sum(h[k] * delay[k] for k in range(NUM_TAPS))
        y.append(sat16(acc >> Q))  # >> cua Python la floor voi so am
    return y


def make_vectors(h):
    rnd = random.Random(SEED)
    sections = []

    def add(name, data):
        sections.append({"name": name, "start": sum(s["len"] for s in sections), "len": len(data)})
        return data

    x = []
    x += add("impulse_32767", [32767] + [0] * 31)
    x += add("step_1000", [1000] * 32)
    x += add("step_max", [32767] * 32)
    x += add("step_min", [-32768] * 32)
    # Mau "doi khang": dau cua mau trung dau he so -> |acc| lon nhat, ep bao hoa
    adv = [32767 if c >= 0 else -32768 for c in reversed(h)]
    x += add("adversarial_sat", adv * 2)
    x += add("alternating_max", [32767 if i % 2 == 0 else -32768 for i in range(32)])
    n_rand = NUM_SAMPLES - len(x)
    x += add("random_uniform", [rnd.randint(-32768, 32767) for _ in range(n_rand)])
    assert len(x) == NUM_SAMPLES
    return x, sections


def to_hex16(v):
    return f"{v & 0xFFFF:04x}"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write(text)


def main():
    h = design_coeffs()
    x, sections = make_vectors(h)
    y = fir_golden(h, x)
    n_sat = sum(1 for v in y if v in (32767, -32768))
    checksum = sum((v & 0xFFFF) for v in y) & 0xFFFFFFFF

    # --- C header (dung chung cho MCU va Pi) ---
    def c_array(name, data, per_line=12):
        lines = []
        for i in range(0, len(data), per_line):
            lines.append("    " + ", ".join(f"{v:6d}" for v in data[i:i + per_line]) + ",")
        return f"static const int16_t {name}[{len(data)}] = {{\n" + "\n".join(lines) + "\n};\n"

    hdr = [
        "/* TU DONG SINH boi experiments/e0_golden/gen_vectors.py - KHONG SUA TAY */",
        "#ifndef FIR_VECTORS_H",
        "#define FIR_VECTORS_H",
        "#include <stdint.h>",
        f"#define FIR_NUM_TAPS {NUM_TAPS}",
        f"#define FIR_NUM_SAMPLES {NUM_SAMPLES}",
        f"#define FIR_GOLDEN_CHECKSUM 0x{checksum:08X}u",
        c_array("FIR_COEFFS", h),
        c_array("FIR_INPUT", x),
        c_array("FIR_GOLDEN", y),
        "#endif",
        "",
    ]
    write(OUT["c_header"], "\n".join(hdr))

    # --- Verilog: he so + file hex cho $readmemh ---
    vh = ["// TU DONG SINH boi experiments/e0_golden/gen_vectors.py - KHONG SUA TAY"]
    for k, c in enumerate(h):
        sign = "-" if c < 0 else ""
        vh.append(f"localparam signed [15:0] H{k} = {sign}16'sd{abs(c)};")
    write(OUT["vh_coeffs"], "\n".join(vh) + "\n")
    write(OUT["hex_in"], "\n".join(to_hex16(v) for v in x) + "\n")
    write(OUT["hex_gold"], "\n".join(to_hex16(v) for v in y) + "\n")

    spec = {
        "label": "spec",
        "num_taps": NUM_TAPS,
        "q_format": "Q15",
        "num_samples": NUM_SAMPLES,
        "seed": SEED,
        "coeffs": h,
        "coeff_sum": sum(h),
        "coeff_abs_sum": sum(abs(c) for c in h),
        "sections": sections,
        "golden_checksum": f"0x{checksum:08X}",
        "saturated_outputs": n_sat,
        "arith": "y = sat16(floor(sum(h[k]*x[n-k]) / 2^15))",
    }
    write(OUT["spec"], json.dumps(spec, indent=2) + "\n")

    print(f"He so Q15: {h}")
    print(f"Tong he so = {sum(h)} (2^15 = 32768), tong |h| = {sum(abs(c) for c in h)}")
    print(f"{NUM_SAMPLES} mau, {n_sat} mau ra bi bao hoa, checksum = 0x{checksum:08X}")
    for k, p in OUT.items():
        print(f"  -> {os.path.relpath(p, ROOT)}")


if __name__ == "__main__":
    main()
