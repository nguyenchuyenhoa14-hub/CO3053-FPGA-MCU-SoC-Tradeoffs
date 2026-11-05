#!/usr/bin/env python3
"""
Ve lai cac bieu do tu SO LIEU DA CONG BO (khong chep hinh cua nguon).
Moi diem du lieu ghi kem khoa nguon; caption trong LaTeX ghi "Du lieu: ...".

    /usr/bin/python3 figs/make_lit_plots.py            # tieng Viet -> figs/plots/
    /usr/bin/python3 figs/make_lit_plots.py --lang en  # tieng Anh  -> figs/plots_en/
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

LANG = "en" if "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en" else "vi"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots_en" if LANG == "en" else "plots")

EN = {  # chuoi tieng Viet -> tieng Anh (chi dung khi --lang en)
    "Raspberry Pi 4 · 4×A72 1,8 GHz": "Raspberry Pi 4 · 4×A72 1.8 GHz",
    "STM32H743 · 1 MAC/chu kỳ × 480 MHz": "STM32H743 · 1 MAC/cycle × 480 MHz",
    "XC7A100T · hãng công bố tối đa": "XC7A100T · vendor peak",
    "tính": "calculated",
    "Linux PREEMPT_RT đã tinh chỉnh": "Linux PREEMPT_RT, tuned",
    "Linux thường": "Standard Linux",
    "“vài ms”": "“a few ms”",
    "300 nA × 3,3 V": "300 nA × 3.3 V",
    "2,43 µA × 3,3 V": "2.43 µA × 3.3 V",
    "Raspberry Pi 4 · rảnh (cả board)": "Raspberry Pi 4 · idle (whole board)",
    "cả board": "whole board",
    "1,431 W (đo)": "1.431 W (measured)",
    "50–100 W (tác giả ước tính)": "50–100 W (authors' estimate)",
    "5–10 W (tác giả ước tính)": "5–10 W (authors' estimate)",
    "13,9 ns": "13.9 ns",
    "CoreMark (càng cao càng nhanh, thang log)": "CoreMark (higher is faster, log scale)",
    "cần 1,68 G MAC/s (video 1080p, lọc 3×3)": "needed: 1.68 G MAC/s (1080p video, 3×3 filter)",
    "Thông lượng MAC tối đa (G MAC/s, thang log)": "Peak MAC throughput (G MAC/s, log scale)",
    "Độ trễ xấu nhất điển hình (thang log)": "Typical worst-case latency (log scale)",
    "Công suất khi nghỉ (thang log)": "Idle power (log scale)",
    "Thời gian xử lý FIR 27-tap (ms, càng thấp càng tốt)": "27-tap FIR processing time (ms, lower is better)",
}


def L(text):
    return EN.get(text, text) if LANG == "en" else text


def dec(text):
    """Dau thap phan: phay cho tieng Viet, cham cho tieng Anh."""
    return text if LANG == "en" else text.replace(".", ",")
C = {"MCU": "#2a78d6", "SoC": "#eb6834", "FPGA": "#1baf7a", "GPU": "#8a8984"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

# ---------------------------------------------------------------- du lieu (nguon)
COREMARK = [  # (nen tang, nhan, gia tri, nguon)
    ("MCU", "STM32F4 · M4 180 MHz", 608, "ST product overview"),
    ("MCU", "STM32H743 · M7 480 MHz", 2424, "ST STM32H743"),
    ("SoC", "STM32MP1 · A7 800 MHz", 4158, "ST product overview"),
    ("SoC", "Raspberry Pi 4 · 4×A72 1,8 GHz", 38200, "OpenBenchmarking"),
]
MAC_NEED = 1.68  # G MAC/s, Lee & Seshia 8.1 (video 1080p, 3×3, 3 kenh, 30 fps)
MAC = [
    ("MCU", "STM32H743 · 1 MAC/chu kỳ × 480 MHz", 0.48, "tính"),
    ("FPGA", "XC7A100T · 240 DSP × 200 MHz", 48.0, "tính"),
    ("FPGA", "XC7A100T · hãng công bố tối đa", 264.0, "datasheet"),
]
LATENCY = [  # (nen tang, nhan, min_s, max_s, chu thich)
    ("FPGA", "FPGA · tick-to-trade (STAC-T0)", 13.9e-9, 13.9e-9, "13,9 ns"),
    ("MCU", "MCU Cortex-M bare-metal", 1e-6, 3e-6, "1–3 µs"),
    ("SoC", "Linux PREEMPT_RT đã tinh chỉnh", 30e-6, 80e-6, "30–80 µs"),
    ("SoC", "Linux thường", 1e-3, 9e-3, "“vài ms”"),
]
IDLE = [  # W, (nen tang, nhan, gia tri, ghi chu)
    ("MCU", "STM32U5 · Standby (chip)", 300e-9 * 3.3, "300 nA × 3,3 V"),
    ("MCU", "STM32H743 · Standby (chip)", 2.43e-6 * 3.3, "2,43 µA × 3,3 V"),
    ("SoC", "Raspberry Pi 4 · rảnh (cả board)", 3.0, "cả board"),
]
ARUCU = [  # FIR 27-tap, thoi gian xu ly (s), cong suat
    ("FPGA", "FPGA Zynq XC7Z020", 0.004, "1,431 W (đo)"),
    ("GPU", "GPU Tesla K80", 0.008, "50–100 W (tác giả ước tính)"),
    ("SoC", "CPU Arm Cortex-A9", 0.107, "5–10 W (tác giả ước tính)"),
]


# ---------------------------------------------------------------- tien ich
def style(ax, xlabel):
    ax.set_facecolor(SURF)
    ax.set_xlabel(L(xlabel), fontsize=9, color=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0, labelsize=8)


def fig(h):
    f, ax = plt.subplots(figsize=(6.4, h), dpi=220)
    f.patch.set_facecolor(SURF)
    return f, ax


def save(f, name):
    os.makedirs(OUT, exist_ok=True)
    f.tight_layout()
    f.savefig(os.path.join(OUT, name), facecolor=SURF)
    plt.close(f)
    print("->", name)


def si(v, unit):
    """Doi sang tien to SI, 3 chu so co nghia, dau phay thap phan."""
    for div, p in ((1e-9, "n"), (1e-6, "µ"), (1e-3, "m"), (1, "")):
        if v / div < 999.5:
            return dec(f"{v / div:.3g} {p}{unit}")
    return dec(f"{v:.3g} {unit}")


def dots(ax, rows, vals, labels, colors):
    ys = range(len(rows))
    lo = min(vals) / 3
    for y, v, c in zip(ys, vals, colors):
        ax.hlines(y, lo, v, color=GRID, linewidth=2, zorder=1)
        ax.scatter([v], [y], s=60, color=c, edgecolor=SURF, linewidth=2, zorder=3)
    for y, v, t in zip(ys, vals, labels):
        ax.annotate(t, (v, y), xytext=(7, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([L(r[1]) for r in rows], fontsize=8, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(lo, max(vals) * 8)


# ---------------------------------------------------------------- bieu do
def coremark():
    f, ax = fig(2.3)
    dots(ax, COREMARK, [r[2] for r in COREMARK], [f"{r[2]:,}".replace(",", " " if LANG == "vi" else ",") for r in COREMARK],
         [C[r[0]] for r in COREMARK])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: dec(f"{v:g}")))
    style(ax, "CoreMark (càng cao càng nhanh, thang log)")
    save(f, "lit_coremark.png")


def mac():
    f, ax = fig(2.1)
    dots(ax, MAC, [r[2] for r in MAC], [dec(f"{r[2]:g} G") + f"  [{L(r[3])}]" for r in MAC],
         [C[r[0]] for r in MAC])
    ax.set_xlim(0.1, 264 * 20)
    ax.axvline(MAC_NEED, color=INK, linewidth=1)
    ax.annotate(L("cần 1,68 G MAC/s (video 1080p, lọc 3×3)"), (MAC_NEED, 0.5),
                xytext=(5, 0), textcoords="offset points", fontsize=7.5, color=INK, va="center")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: dec(f"{v:g}")))
    style(ax, "Thông lượng MAC tối đa (G MAC/s, thang log)")
    save(f, "lit_mac.png")


def latency():
    f, ax = fig(2.3)
    ys = range(len(LATENCY))
    for y, (p, _, lo, hi, txt) in zip(ys, LATENCY):
        if hi > lo:
            ax.hlines(y, lo, hi, color=C[p], linewidth=7, alpha=0.9 if "ms”" not in txt else 0.45, zorder=3)
        else:
            ax.scatter([lo], [y], s=60, color=C[p], edgecolor=SURF, linewidth=2, zorder=3)
        ax.annotate(L(txt), (hi, y), xytext=(8, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([L(r[1]) for r in LATENCY], fontsize=8, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(5e-9, 0.2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: si(v, "s")))
    style(ax, "Độ trễ xấu nhất điển hình (thang log)")
    save(f, "lit_latency.png")


def idle():
    f, ax = fig(1.9)
    dots(ax, IDLE, [r[2] for r in IDLE], [f"{si(r[2], 'W')}  ({L(r[3])})" for r in IDLE], [C[r[0]] for r in IDLE])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: si(v, "W")))
    style(ax, "Công suất khi nghỉ (thang log)")
    save(f, "lit_idle_power.png")


def arucu():
    f, ax = fig(1.9)
    ys = range(len(ARUCU))
    for y, (p, _, t, pw) in zip(ys, ARUCU):
        ax.barh(y, t * 1000, height=0.5, color=C[p], zorder=3)
        ax.annotate(dec(f"{t * 1000:g} ms") + f" · {L(pw)}", (t * 1000, y), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([L(r[1]) for r in ARUCU], fontsize=8, color=INK)
    ax.set_xlim(0, 0.107 * 1000 * 1.9)
    ax.invert_yaxis()
    style(ax, "Thời gian xử lý FIR 27-tap (ms, càng thấp càng tốt)")
    save(f, "lit_fir_arucu.png")


if __name__ == "__main__":
    coremark()
    mac()
    latency()
    idle()
    arucu()
