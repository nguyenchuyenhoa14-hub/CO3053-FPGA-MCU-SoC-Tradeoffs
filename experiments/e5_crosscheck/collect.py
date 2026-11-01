#!/usr/bin/env python3
"""
E5 - Gom ket qua E0-E3 trong results/*.json -> bang kiem chung cheo + chart.

    /usr/bin/python3 e5_crosscheck/collect.py            # can matplotlib
    /usr/bin/python3 e5_crosscheck/collect.py --x86      # them laptop x86 lam tham chieu

Moi so deu mang nhan: do / mo phong / uoc luong cong cu / tinh / nguon.
Thieu file nao thi dong tuong ung ghi "chua co" - KHONG bao gio dien so gia dinh.
So "nguon" lay tu PLAN.md (co link trong do).
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get("E5_RESULTS", os.path.join(ROOT, "results"))   # bien moi truong chi de test
CHARTS = os.path.join(RES, "charts")


def load(name):
    p = os.path.join(RES, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def fmt(v, nd=2):
    if v is None:
        return "chưa có"
    if isinstance(v, float):
        return f"{v:,.{nd}f}".replace(",", " ")
    return str(v)


# ---------------------------------------------------------------- gom so lieu
def gather(include_x86):
    spec = load("e0_spec.json")
    taps = spec["num_taps"] if spec else 16
    rows_tp = []    # thong luong: (nen tang, cau hinh, MSPS, nhan, ghi chu)
    rows_lat = []   # do tre xau nhat: (nen tang, kich ban, ns, nhan, loai phep do)
    rows_en = []    # nang luong / mau

    mcu = load("e1_mcu.json")
    if mcu:
        for v in mcu["variants"]:
            rows_tp.append(("MCU", f"STM32F103 {mcu['clock_mhz']} MHz · {v['variant']}",
                            v["ksps"] / 1000.0, "đo", "đúng" if v["correct"] else "SAI"))
        for r in mcu["irq_latency"]:
            rows_lat.append(("MCU", f"ngắt TIM2 · {r['scenario']}", r["max_ns"], "đo",
                             "sự kiện timer → lệnh đầu ISR"))

    for f in sorted(glob.glob(os.path.join(RES, "e3_soc_fir_*.json"))):
        d = json.load(open(f))
        is_pi = d["machine"] == "aarch64"
        if not is_pi and not include_x86:
            continue
        plat = "SoC" if is_pi else "x86 (tham chiếu)"
        for v in d["variants"]:
            rows_tp.append((plat, f"{'Pi 4' if is_pi else 'laptop'} · {v['variant']} · {d.get('build_flags', '')}",
                            v["msps_median"], "đo", "đúng" if v["correct"] else "SAI"))

    for f in sorted(glob.glob(os.path.join(RES, "e3_cyclictest_*.json"))):
        d = json.load(open(f))
        kern = "PREEMPT_RT" if d["kernel"] == "rt" else "Linux thường"
        rows_lat.append(("SoC", f"Pi 4 · {kern} · {'có tải' if d['load'] == 'load' else 'rảnh'}",
                         d["max_us"] * 1000.0, "đo", "độ trễ lập lịch (cyclictest)"))

    sim = load("e2_fpga_sim.json")
    board = load("e2_fpga_board.json")
    impl = load("e2_fpga_impl.json")
    if board:
        rows_tp.append(("FPGA", "Arty A7-100T · 100 MHz trên board", board["throughput_msps"], "đo",
                        "PASS" if board["pass"] else "FAIL"))
        rows_lat.append(("FPGA", "pipeline FIR · 100 MHz", board["latency_ns"], "đo", "mẫu vào → mẫu ra"))
    elif sim:
        rows_tp.append(("FPGA", "RTL · giả định clock 100 MHz", sim["samples_per_cycle"] * 100.0, "mô phỏng",
                        "PASS" if sim["pass"] else "FAIL"))
        rows_lat.append(("FPGA", "pipeline FIR · 100 MHz", sim["continuous"]["latency_cycles"] * 10.0,
                         "mô phỏng", "mẫu vào → mẫu ra"))
    if impl:
        fmax = impl["fir16_ooc"]["fmax_mhz_est"]
        spc = (board or sim or {"samples_per_cycle": 1.0})["samples_per_cycle"]
        rows_tp.append(("FPGA", f"XC7A100T · Fmax ≈ {fmax:.0f} MHz", spc * fmax, "ước lượng công cụ",
                        "Vivado timing, chỉ khối FIR"))

    # Nang luong / mau (nJ) = P / thong luong
    mcu_pw = load("e1_mcu_power.json")
    if mcu and mcu_pw and mcu_pw.get("run_mA"):
        p_w = mcu_pw["run_mA"] * 1e-3 * mcu_pw.get("voltage_v", 3.3)
        best = max(v["ksps"] for v in mcu["variants"] if v["correct"]) * 1e3
        rows_en.append(("MCU", "STM32F103 khi chạy FIR", p_w, p_w / best * 1e9, "đo",
                        mcu_pw.get("where", "")))
    pi_pw = load("e3_pi_power.json")
    pi_tp = [r for r in rows_tp if r[0] == "SoC"]
    if pi_tp and pi_pw and pi_pw.get("fir_w"):
        best = max(r[2] for r in pi_tp) * 1e6
        rows_en.append(("SoC", "Pi 4 cả board khi chạy FIR", pi_pw["fir_w"], pi_pw["fir_w"] / best * 1e9, "đo",
                        pi_pw.get("where", "")))
    if impl and impl["top_100mhz"]["power_total_w"] not in (None, "null"):
        p_w = float(impl["top_100mhz"]["power_total_w"])
        spc = (board or sim or {"samples_per_cycle": 1.0})["samples_per_cycle"]
        rows_en.append(("FPGA", "XC7A100T cả chip @100 MHz", p_w, p_w / (spc * 100e6) * 1e9,
                        "ước lượng công cụ", "Vivado vector-less, gồm static"))

    return dict(spec=spec, taps=taps, mcu=mcu, sim=sim, board=board, impl=impl,
                tp=rows_tp, lat=rows_lat, en=rows_en)


# ---------------------------------------------------------------- kiem chung cheo
def crosscheck(d):
    out = []
    taps = d["taps"]
    mcu = d["mcu"]
    if mcu:
        best = max((v for v in mcu["variants"] if v["correct"]), key=lambda v: v["ksps"])
        ideal = mcu["clock_mhz"] * 1e6 / taps  # 1 MAC / chu ky
        eff = best["ksps"] * 1e3 / ideal * 100
        out.append(("Hiệu suất MCU so với giả thiết “1 MAC/chu kỳ” mà PLAN.md dùng cho H743",
                    f"{best['cycles_per_sample']:.1f} chu kỳ/mẫu ({best['variant']}) → đạt {eff:.0f}% mức lý thuyết",
                    "PLAN.md (tính): 1 MAC/chu kỳ",
                    "Nếu ≪100%, con số ≈0,48 G MAC/s của H743 trong PLAN là cận trên lạc quan"))
        lat = {r["scenario"]: r for r in mcu["irq_latency"]}
        if "fir_load" in lat:
            r = lat["fir_load"]
            out.append(("Độ trễ ngắt MCU bare-metal",
                        f"{r['min_ns']:.0f}–{r['max_ns']:.0f} ns (có tải FIR)",
                        "AC6 (nguồn): 1–3 µs",
                        "Đo từ sự kiện timer đến lệnh đầu tiên của ISR"))
        if "fir_load_plus_higher_prio_isr_20us" in lat:
            r = lat["fir_load_plus_higher_prio_isr_20us"]
            out.append(("MCU khi có ngắt ưu tiên cao hơn chạy 20 µs",
                        f"xấu nhất {r['max_ns'] / 1000:.1f} µs",
                        "—",
                        "Worst-case MCU do thiết kế phần mềm quyết định, không phải do chip"))

    pi_best = max((r[2] for r in d["tp"] if r[0] == "SoC"), default=None)
    fpga_meas = next((r for r in d["tp"] if r[0] == "FPGA" and r[3] in ("đo", "mô phỏng")), None)
    if pi_best and fpga_meas:
        out.append(("Tỉ lệ thông lượng FPGA / CPU Cortex-A",
                    f"{fpga_meas[2] / pi_best:.1f}× (FPGA 100 MHz, {fpga_meas[3]}) so với Pi 4 tốt nhất",
                    "Arucu & Iliev (nguồn): ≈27× so với Cortex-A9",
                    "Khác: chip CPU, số tap, cách đo"))
    for r in d["lat"]:
        if r[0] == "SoC":
            ref = "AC6 (nguồn): 30–80 µs" if "RT" in r[1] else "AC6 (nguồn): vài ms"
            out.append((f"Độ trễ xấu nhất {r[1]}", f"{r[2] / 1000:.0f} µs", ref, r[4]))
    if d["impl"]:
        o = d["impl"]["fir16_ooc"]
        out.append(("Tài nguyên DSP cho FIR 16-tap",
                    f"{o['dsp48e1']}/{o['dsp_available']} DSP48E1 ({o['dsp48e1'] / o['dsp_available'] * 100:.1f}%)",
                    "PLAN.md (tính): bài video cần ≈3,5% năng lực",
                    "Tap có hệ số 0 bị synthesis loại bỏ"))
    return out


# ---------------------------------------------------------------- markdown
def write_md(d, xc):
    L = ["# E5 · Kết quả thí nghiệm và kiểm chứng chéo", "",
         "Tự động sinh bởi `e5_crosscheck/collect.py`. Nhãn: **đo** (nhóm tự đo trên phần cứng), "
         "**mô phỏng**, **ước lượng công cụ** (Vivado), **tính**, **nguồn** (tài liệu trong PLAN.md).", ""]
    if d["spec"]:
        s = d["spec"]
        L += [f"Bài toán chung: FIR {s['num_taps']}-tap {s['q_format']}, {s['num_samples']} mẫu (seed {s['seed']}), "
              f"{s['saturated_outputs']} mẫu ra bão hòa; mọi nền tảng so từng mẫu với golden model.", ""]
    L += ["## Thông lượng", "", "| Nền tảng | Cấu hình | MSPS | Nhãn | Kiểm tra |", "| --- | --- | --- | --- | --- |"]
    L += [f"| {a} | {b} | {fmt(c)} | {e} | {f} |" for a, b, c, e, f in d["tp"]] or ["| — | chưa có số liệu | | | |"]
    L += ["", "## Độ trễ xấu nhất", "", "| Nền tảng | Kịch bản | Xấu nhất | Nhãn | Đại lượng đo |",
          "| --- | --- | --- | --- | --- |"]
    L += [f"| {a} | {b} | {fmt(c / 1000, 2)} µs | {e} | {f} |" for a, b, c, e, f in d["lat"]] or ["| — | chưa có | | | |"]
    L += ["", "Các dòng đo những đại lượng khác nhau (ngắt phần cứng, lập lịch Linux, pipeline), chỉ so bậc độ lớn.",
          "", "## Năng lượng mỗi mẫu", "", "| Nền tảng | Điều kiện | Công suất (W) | nJ/mẫu | Nhãn | Ghi chú |",
          "| --- | --- | --- | --- | --- | --- |"]
    L += [f"| {a} | {b} | {fmt(c, 3)} | {fmt(e, 2)} | {f} | {g} |" for a, b, c, e, f, g in d["en"]] or \
         ["| — | chưa có số đo công suất | | | | |"]
    L += ["", "## Kiểm chứng chéo với PLAN.md", "", "| Câu hỏi | Nhóm đo được | Tài liệu nói | Ghi chú |",
          "| --- | --- | --- | --- |"]
    L += [f"| {a} | {b} | {c} | {e} |" for a, b, c, e in xc] or ["| — | chưa đủ số liệu | | |"]
    path = os.path.join(RES, "E5_crosscheck.md")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


# ---------------------------------------------------------------- chart
COLORS = {"MCU": "#2a78d6", "SoC": "#eb6834", "FPGA": "#1baf7a", "x86 (tham chiếu)": "#8a8984"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def dot_chart(rows, value_idx, label_fn, xlabel, title, subtitle, fname, unit_scale=1.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r[value_idx])
    fig_h = 1.2 + 0.42 * len(rows)
    fig, ax = plt.subplots(figsize=(10, fig_h), dpi=200)
    fig.patch.set_facecolor(SURF)
    ax.set_facecolor(SURF)
    ys = range(len(rows))
    vals = [r[value_idx] * unit_scale for r in rows]
    for y, r, v in zip(ys, rows, vals):
        c = COLORS.get(r[0], INK2)
        ax.hlines(y, min(vals) / 3, v, color=GRID, linewidth=2, zorder=1)
        ax.scatter([v], [y], s=70, color=c, edgecolor=SURF, linewidth=2, zorder=3)
        ax.annotate(label_fn(r, v), (v, y), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.set_xscale("log")
    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"{r[0]} · {r[1]}" for r in rows], fontsize=8, color=INK)
    ax.set_xlim(min(vals) / 3, max(vals) * 60)   # cho nhan ben phai
    ax.set_xlabel(xlabel, fontsize=9, color=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0)
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    seen = [p for p in COLORS if any(r[0] == p for r in rows)]   # thu tu co dinh theo nen tang
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=COLORS.get(p, INK2), markersize=8) for p in seen]
    ax.legend(handles, seen, loc="lower right", frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK, fontweight="bold")
    ax.set_title(subtitle, loc="left", fontsize=8, color=INK2)
    fig.tight_layout()
    os.makedirs(CHARTS, exist_ok=True)
    path = os.path.join(CHARTS, fname)
    fig.savefig(path, facecolor=SURF)
    plt.close(fig)
    return path


def charts(d):
    out = []
    out.append(dot_chart(
        d["tp"], 2, lambda r, v: f"{v:,.1f} MSPS  [{r[3]}]".replace(",", " "),
        "Thông lượng (triệu mẫu/giây, thang log)",
        "Thông lượng FIR 16-tap Q15, cùng vector, cùng golden",
        "Nhãn trong ngoặc: nguồn gốc số liệu. Chỉ hiện kết quả đã kiểm tra đúng từng mẫu.",
        "e5_throughput.png"))
    out.append(dot_chart(
        d["lat"], 2, lambda r, v: f"{v:,.2f} µs  [{r[3]}]".replace(",", " "),
        "Độ trễ xấu nhất (µs, thang log)",
        "Độ trễ xấu nhất quan sát được",
        "MCU: sự kiện timer → lệnh đầu ISR · SoC: độ trễ lập lịch (cyclictest) · FPGA: mẫu vào → mẫu ra. Chỉ so bậc độ lớn.",
        "e5_worst_latency.png", unit_scale=1e-3))
    if d["en"]:
        out.append(dot_chart(
            d["en"], 3, lambda r, v: f"{v:,.2f} nJ/mẫu  [{r[4]}]".replace(",", " "),
            "Năng lượng mỗi mẫu (nJ, thang log)",
            "Năng lượng cho một mẫu FIR",
            "Công suất MCU/Pi: đo bằng đồng hồ; FPGA: Vivado ước lượng. Không cùng cách đo.",
            "e5_energy.png"))
    return [p for p in out if p]


# ---------------------------------------------------------------- macro LaTeX cho report/slide
def vn(v, nd=1):
    """So kieu Viet: dau phay thap phan, khoang hep ngan cach hang nghin."""
    s = f"{v:,.{nd}f}"
    return s.replace(",", "\\,").replace(".", "{,}")


def write_tex(d):
    m = {}
    NA = r"\chuado{}"
    mcu = d["mcu"]
    best = None
    if mcu:
        ok = [v for v in mcu["variants"] if v["correct"]]
        best = max(ok, key=lambda v: v["ksps"]) if ok else None
        shift = next((v for v in mcu["variants"] if v["variant"] == "c_shift_loop"), None)
        lat = {r["scenario"]: r for r in mcu["irq_latency"]}
        m["McuClock"] = str(mcu["clock_mhz"])
        if best:
            m["McuBestVariant"] = best["variant"].replace("_", r"\_")
            m["McuBestCps"] = vn(best["cycles_per_sample"])
            m["McuBestMsps"] = vn(best["ksps"] / 1000, 2)
            m["McuEff"] = vn(best["ksps"] * 1e3 / (mcu["clock_mhz"] * 1e6 / d["taps"]) * 100, 0)
        if shift:
            m["McuShiftCps"] = vn(shift["cycles_per_sample"])
        if "fir_load" in lat:
            m["McuIrqMin"] = vn(lat["fir_load"]["min_ns"], 0)
            m["McuIrqMax"] = vn(lat["fir_load"]["max_ns"], 0)
            m["McuIrqRange"] = m["McuIrqMin"] + "–" + m["McuIrqMax"]
        if "fir_load_plus_higher_prio_isr_20us" in lat:
            m["McuIrqHogMax"] = vn(lat["fir_load_plus_higher_prio_isr_20us"]["max_ns"] / 1000, 1)

    pi = [r for r in d["tp"] if r[0] == "SoC"]
    pi_best = max((r[2] for r in pi), default=None)
    if pi_best:
        m["PiBestMsps"] = vn(pi_best, 1)

    fpga = next((r for r in d["tp"] if r[0] == "FPGA" and r[3] in ("đo", "mô phỏng")), None)
    if fpga:
        m["FpgaMsps"] = vn(fpga[2], 1)
        m["FpgaLabel"] = fpga[3]
    src = d["board"] or d["sim"]
    if src:
        lat_c = src.get("latency_cycles") or src["continuous"]["latency_cycles"]
        m["FpgaLatCycles"] = str(lat_c)
        m["FpgaLatNs"] = vn(lat_c * 10.0, 0)
        m["FpgaPass"] = "PASS" if src["pass"] else "FAIL"
        m["FpgaSpc"] = vn(src["samples_per_cycle"], 2)
    if d["impl"]:
        o, t = d["impl"]["fir16_ooc"], d["impl"]["top_100mhz"]
        m["FpgaFmax"] = vn(o["fmax_mhz_est"], 0)
        m["FpgaDsp"] = str(o["dsp48e1"])
        if t["power_total_w"] not in (None, "null"):
            m["FpgaPower"] = vn(float(t["power_total_w"]), 3)
    if fpga and pi_best:
        m["RatioFpgaPi"] = vn(fpga[2] / pi_best, 1)
    if fpga and best:
        m["RatioFpgaMcu"] = vn(fpga[2] / (best["ksps"] / 1000), 0)

    for r in d["lat"]:
        if r[0] == "SoC" and "có tải" in r[1]:
            key = "LinuxRtMax" if "RT" in r[1] else "LinuxStdMax"
            m[key] = vn(r[2] / 1000, 0)

    keys = ["McuClock", "McuBestVariant", "McuBestCps", "McuBestMsps", "McuEff", "McuShiftCps",
            "McuIrqMin", "McuIrqMax", "McuIrqRange", "McuIrqHogMax", "PiBestMsps", "FpgaMsps", "FpgaLabel",
            "FpgaLatCycles", "FpgaLatNs", "FpgaPass", "FpgaSpc", "FpgaFmax", "FpgaDsp", "FpgaPower",
            "RatioFpgaPi", "RatioFpgaMcu", "LinuxStdMax", "LinuxRtMax"]
    lines = ["% TU DONG SINH boi experiments/e5_crosscheck/collect.py - KHONG SUA TAY",
             "% So chua do hien \\chuado{} (report dinh nghia macro nay)."]
    for k in keys:
        lines.append(f"\\newcommand{{\\exp{k}}}{{{m.get(k, NA)}}}")
    lines.append(f"\\newcommand{{\\expHaveMcu}}{{{'1' if mcu else '0'}}}")
    lines.append(f"\\newcommand{{\\expHavePi}}{{{'1' if pi_best else '0'}}}")
    path = os.path.join(RES, "numbers.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def main():
    d = gather("--x86" in sys.argv)
    xc = crosscheck(d)
    md = write_md(d, xc)
    print(f"-> {os.path.relpath(md, ROOT)}")
    print(f"-> {os.path.relpath(write_tex(d), ROOT)}")
    try:
        for p in charts(d):
            print(f"-> {os.path.relpath(p, ROOT)}")
    except ImportError:
        print("(bo qua chart: thieu matplotlib, chay bang /usr/bin/python3)")


if __name__ == "__main__":
    main()
