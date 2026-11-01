"""
===============================================================================
XUẤT BIỂU ĐỒ ĐỐI SÁNH ĐỊNH LƯỢNG CHUẨN IEEE (300 DPI)
Môn học: [HK261] CO3053 - Hệ thống nhúng | Đề tài 9
===============================================================================
Tạo ra 4 đồ thị khoa học sắc nét chèn trực tiếp vào Slide 18 và Báo cáo tóm tắt.
"""

import os
import sys
import matplotlib.pyplot as plt
import numpy as np

# Đảm bảo tương thích mã hóa trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Tạo thư mục xuất đồ thị nếu chưa có
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cấu hình phong cách đồ thị chuẩn khoa học IEEE
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

def plot_all():
    print("===============================================================")
    print("  DANG KHOI TAO & XUAT 4 BIEU DO DOI SANH DINH LUONG (300 DPI) ")
    print("===============================================================")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 1: THÔNG LƯỢNG XỬ LÝ (THROUGHPUT COMPARISON)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.4), dpi=300)
    platforms = [
        'ARM Cortex-M4\n(STM32F4, 168 MHz)',
        'ARM Cortex-M7\n(STM32H7, 480 MHz)',
        'ARM Cortex-A9\n(Zynq PS, 667 MHz)',
        'FPGA Artix-7\n(RTL Pipe, 100 MHz)',
        'SoC Zynq-7000\n(PL Accel, 150 MHz)'
    ]
    throughputs = [4.66, 13.33, 33.35, 100.00, 150.00] # MSamples/sec
    colors = ['#4A90E2', '#357ABD', '#2C3E50', '#E74C3C', '#27AE60']

    bars = ax.bar(platforms, throughputs, color=colors, width=0.52, edgecolor='#222', linewidth=1.2)
    ax.set_ylabel('Thông lượng tính toán (Mega-Samples / Giây)', fontsize=11, fontweight='bold', labelpad=10)
    ax.set_title('ĐỐI SÁNH THÔNG LƯỢNG BỘ LỌC FIR 16-TAP GIỮA CÁC NỀN TẢNG', fontsize=12, fontweight='bold', pad=15)
    ax.set_ylim(0, 180)
    ax.tick_params(axis='x', labelsize=9.5)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Thêm giá trị cụ thể trên từng cột
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f} MSPS',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Chú thích tỷ lệ tăng tốc (trỏ vào cạnh trái cột FPGA để không đè lên chữ 100.0 MSPS)
    ax.annotate('TĂNG TỐC 21.4x LẦN\n(so với Cortex-M4 @ 168 MHz)',
                xy=(2.73, 92), xytext=(1.05, 128),
                arrowprops=dict(facecolor='#E74C3C', shrink=0.06, width=2, headwidth=8),
                fontsize=9.5, fontweight='bold', color='#C0392B',
                bbox=dict(boxstyle="round,pad=0.4", fc="#FDEDEC", ec="#E74C3C", lw=1.2))

    plt.tight_layout()
    chart1_path = os.path.join(OUTPUT_DIR, "chart1_throughput_comparison.png")
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart1_path}")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 2: ĐỘ TRỄ PHẢN HỒI & DAO ĐỘNG JITTER (LATENCY & JITTER)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=300)
    categories = ['Độ trễ phản hồi (Response Latency)', 'Độ dao động ngắt (Timing Jitter)']
    mcu_values = [214.28, 2500.0]  # ns (RTOS interrupt jitter có thể lên tới 2.5 µs)
    fpga_values = [10.0, 0.05]      # ns (FPGA cycle-accurate, jitter ~ ps/0 ns)

    x = np.arange(len(categories))
    width = 0.34

    rects1 = ax.bar(x - width/2, mcu_values, width, label='Vi điều khiển MCU (Cortex-M4)', color='#4A90E2', edgecolor='#222')
    rects2 = ax.bar(x + width/2, fpga_values, width, label='FPGA Phần cứng (Artix-7)', color='#E74C3C', edgecolor='#222')

    ax.set_ylabel('Thời gian phản hồi (Nano-giây, Thang đo Log)', fontsize=11, fontweight='bold')
    ax.set_title('ĐỘ TRỄ PHẢN HỒI VẬT LÝ VÀ TÍNH TIỀN ĐỊNH THỜI GIAN (DETERMINISM)', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10.5, fontweight='bold')
    ax.set_yscale('log')
    ax.set_ylim(0.01, 15000)
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    ax.annotate('214.3 ns', xy=(x[0] - width/2, 214.28), xytext=(0, 5), textcoords="offset points", ha='center', fontweight='bold')
    ax.annotate('10.0 ns (1 chu kỳ)', xy=(x[0] + width/2, 10.0), xytext=(0, 5), textcoords="offset points", ha='center', fontweight='bold')
    ax.annotate('~2,500 ns (Jitter)', xy=(x[1] - width/2, 2500), xytext=(0, 5), textcoords="offset points", ha='center', fontweight='bold')
    ax.annotate('0.00 ns (Zero Jitter)', xy=(x[1] + width/2, 0.05), xytext=(0, 5), textcoords="offset points", ha='center', fontweight='bold', color='#C0392B')

    plt.tight_layout()
    chart2_path = os.path.join(OUTPUT_DIR, "chart2_latency_and_jitter.png")
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart2_path}")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 3: HIỆU QUẢ NĂNG LƯỢNG (ENERGY EFFICIENCY: SAMPLES / JOULE)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=300)
    ef_platforms = ['STM32F4\n(0.25 W)', 'STM32H7\n(0.45 W)', 'FPGA Artix-7\n(1.20 W)', 'SoC Zynq-7000\n(2.50 W)']
    ef_values = [18.64, 29.62, 83.33, 60.00]
    ef_colors = ['#7F8C8D', '#95A5A6', '#E67E22', '#27AE60']

    bars3 = ax.bar(ef_platforms, ef_values, color=ef_colors, width=0.48, edgecolor='#222')
    ax.set_ylabel('Hiệu quả năng lượng (Triệu mẫu xử lý / Joule)', fontsize=11, fontweight='bold')
    ax.set_title('HIỆU QUẢ NĂNG LƯỢNG TÍNH TOÁN KHI THỰC HIỆN CÙNG TÁC VỤ DSP', fontsize=12, fontweight='bold', pad=15)
    ax.set_ylim(0, 108)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar in bars3:
        height = bar.get_height()
        ax.annotate(f'{height:.1f} M/J',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Đặt hộp chú thích bên trái và trỏ mũi tên vào sườn cột FPGA để không đè lên nhãn 83.3 M/J
    ax.annotate('HIỆU QUẢ GẤP 4.5 LẦN!\n(FPGA không lãng phí điện nạp lệnh tuần tự)',
                xy=(1.75, 76), xytext=(0.12, 84),
                arrowprops=dict(facecolor='#E67E22', shrink=0.06, width=2, headwidth=7),
                fontsize=9.5, fontweight='bold', color='#D35400',
                bbox=dict(boxstyle="round,pad=0.4", fc="#FEF5E7", ec="#E67E22", lw=1.2))

    plt.tight_layout()
    chart3_path = os.path.join(OUTPUT_DIR, "chart3_energy_efficiency.png")
    plt.savefig(chart3_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart3_path}")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 4: ĐIỂM HÒA VỐN KINH TẾ (BREAK-EVEN COST ANALYSIS)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.2), dpi=300)
    volumes = np.logspace(1, 6, 200) # Từ 10 đến 1.000.000 sản phẩm

    # MCU: NRE = 5,000 USD, BOM = 3 USD
    cost_mcu = 5000 + (3.0 * volumes)
    # FPGA: NRE = 80,000 USD, BOM = 35 USD
    cost_fpga = 80000 + (35.0 * volumes)
    # Custom ASIC (Tham chiếu): NRE = 1,500,000 USD, BOM = 1.2 USD
    cost_asic = 1500000 + (1.2 * volumes)

    # Dùng USD thay vì 2 ký tự $ để không kích hoạt chế độ MathText làm nghiêng và dính chữ
    ax.plot(volumes, cost_mcu, label='Phương án 1: Vi điều khiển MCU (NRE = 5K USD, BOM = 3 USD)', color='#2980B9', linewidth=2.5)
    ax.plot(volumes, cost_fpga, label='Phương án 2: FPGA / SoC (NRE = 80K USD, BOM = 35 USD)', color='#C0392B', linewidth=2.5, linestyle='--')
    ax.plot(volumes, cost_asic, label='Phương án 3: ASIC Chuyên dụng (NRE = 1.5M USD, BOM = 1.2 USD)', color='#27AE60', linewidth=2.5, linestyle=':')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Sản lượng sản xuất (Số lượng thiết bị thương mại)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Tổng chi phí vòng đời dự án (USD, Thang Log)', fontsize=11, fontweight='bold')
    ax.set_title('PHÂN TÍCH ĐIỂM HÒA VỐN KINH TẾ: NRE vs. UNIT BOM COST', fontsize=12, fontweight='bold', pad=15)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=9.5, loc='upper left')

    # Điểm giao cắt ASIC vs FPGA: 80,000 + 35*V = 1,500,000 + 1.2*V => V ≈ 42,012
    v_breakeven = (1500000 - 80000) / (35.0 - 1.2)
    c_breakeven = 80000 + 35.0 * v_breakeven
    ax.scatter([v_breakeven], [c_breakeven], color='#27AE60', s=85, zorder=5)
    ax.annotate('Điểm hòa vốn FPGA vs. ASIC\n(~42,000 thiết bị)',
                xy=(v_breakeven, c_breakeven), xytext=(55000, 380000),
                arrowprops=dict(arrowstyle="->", color='#27AE60', lw=1.8),
                fontweight='bold', fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.3", fc="#EAFAF1", ec="#27AE60", lw=1))

    plt.tight_layout()
    chart4_path = os.path.join(OUTPUT_DIR, "chart4_breakeven_cost_analysis.png")
    plt.savefig(chart4_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart4_path}")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 5: HIỆU NĂNG TĂNG TỐC AXI4-STREAM DMA & GIẢI PHÓNG CPU TRÊN SOC ZYNQ
    # -------------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(9.0, 5.2), dpi=300)
    batch_sizes = np.array([16, 64, 256, 1024, 4096, 16384, 65536])
    speedups = np.array([0.34, 1.12, 2.56, 3.78, 4.30, 4.45, 4.48])
    cpu_offloads = np.array([0.0, 37.5, 84.4, 96.1, 99.0, 99.8, 99.9])

    color_speedup = '#C0392B'
    color_offload = '#2980B9'

    line1 = ax1.plot(batch_sizes, speedups, marker='o', markersize=7, color=color_speedup,
                     linewidth=2.5, label='Hệ số tăng tốc phần cứng (Speedup vs. Cortex-A9 667 MHz)')
    ax1.axhline(1.0, color='#7F8C8D', linestyle=':', linewidth=1.5, label='Ngưỡng hòa vốn tốc độ (Speedup = 1.0x)')
    ax1.set_xscale('log', base=2)
    ax1.set_xlabel('Kích thước gói dữ liệu truyền qua AXI4-Stream DMA (Số mẫu N)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Hệ số tăng tốc (Speedup - Lần)', fontsize=11, fontweight='bold', color=color_speedup)
    ax1.tick_params(axis='y', labelcolor=color_speedup)
    ax1.set_ylim(0, 5.4)
    ax1.set_xticks(batch_sizes)
    ax1.set_xticklabels([str(n) for n in batch_sizes], fontweight='bold')
    ax1.grid(True, which="both", ls="--", alpha=0.45)

    for n_val, sp_val in zip(batch_sizes, speedups):
        y_offset = -16 if n_val >= 4096 else 9
        ax1.annotate(f'{sp_val:.2f}x', xy=(n_val, sp_val), xytext=(0, y_offset),
                     textcoords="offset points", ha='center', fontsize=9, fontweight='bold', color=color_speedup)

    ax2 = ax1.twinx()
    line2 = ax2.plot(batch_sizes, cpu_offloads, marker='s', markersize=6.5, color=color_offload,
                     linewidth=2.2, linestyle='--', label='Tỷ lệ giải phóng tải CPU (CPU Offload %)')
    ax2.set_ylabel('Tỷ lệ giải phóng CPU cho Linux (%)', fontsize=11, fontweight='bold', color=color_offload)
    ax2.tick_params(axis='y', labelcolor=color_offload)
    ax2.set_ylim(0, 118)
    for n_val, off_val in zip(batch_sizes[2:], cpu_offloads[2:]):
        ax2.annotate(f'{off_val:.1f}%', xy=(n_val, off_val), xytext=(0, 8),
                     textcoords="offset points", ha='center', fontsize=8.5, fontweight='bold', color=color_offload)

    # Gộp chung chú thích của 2 trục
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=9.2)
    ax1.set_title('ĐÁNH ĐỔI KÍCH THƯỚC GÓI AXI4-STREAM DMA TRÊN HETEROGENEOUS SOC ZYNQ-7000',
                  fontsize=11.5, fontweight='bold', pad=15)

    ax1.annotate('Gói nhỏ (N=16): Chậm hơn CPU (0.34x)\ndo chi phí Setup DMA + Ngắt = 1.20 µs',
                 xy=(16, 0.34), xytext=(64, 0.32),
                 arrowprops=dict(arrowstyle="->", color='#333', lw=1.5),
                 fontsize=8.8, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.35", fc="#FDEDEC", ec="#C0392B", lw=1))

    plt.tight_layout()
    chart5_path = os.path.join(OUTPUT_DIR, "chart5_soc_dma_offload.png")
    plt.savefig(chart5_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart5_path}")

    # -------------------------------------------------------------------------
    # ĐỒ THỊ 6: DẠNG SÓNG TIMING CHU KỲ CHÍNH XÁC CỦA MẠCH FPGA FIR 16-TAP
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(5, 1, figsize=(9.5, 5.8), dpi=300, sharex=True,
                             gridspec_kw={'height_ratios': [1, 1, 1.2, 1.15, 1.5]})
    cycles = np.arange(0, 22)
    t_sub = np.linspace(0, 22, 880)
    clk_wave = 0.5 * (1 + np.sign(np.sin(2 * np.pi * t_sub)))

    valid_in_wave = np.where((t_sub >= 1.0) & (t_sub < 21.0), 1.0, 0.0)
    valid_out_wave = np.where((t_sub >= 6.0) & (t_sub < 22.0), 1.0, 0.0)

    y_vals = [0, 0, 0, 0, 0, 0, -4, 1, 12, 34, 72, 130, 205, 290, 375, 450, 508, 546, 568, 579, 584, 581]

    axes[0].plot(t_sub, clk_wave, color='#2C3E50', lw=1.5)
    axes[0].set_ylabel('clk\n(100MHz)', fontweight='bold', fontsize=9)
    axes[0].set_yticks([0, 1])
    axes[0].set_ylim(-0.2, 1.3)

    axes[1].step(t_sub, valid_in_wave, where='post', color='#2980B9', lw=2.0)
    axes[1].set_ylabel('valid_in', fontweight='bold', fontsize=9)
    axes[1].set_yticks([0, 1])
    axes[1].set_ylim(-0.2, 1.3)

    axes[2].set_ylabel('data_in\n(Q15)', fontweight='bold', fontsize=9)
    axes[2].set_ylim(-0.2, 1.2)
    axes[2].set_yticks([])
    axes[2].fill_between([1, 21], 0.15, 0.85, color='#D6EAF8', edgecolor='#2980B9', lw=1.5)
    axes[2].text(11.0, 0.5, 'x[n] = 1000 (Bơm liên tục 1 mẫu / chu kỳ xung nhịp)',
                 ha='center', va='center', fontweight='bold', fontsize=9.5, color='#1B4F72')

    axes[3].step(t_sub, valid_out_wave, where='post', color='#27AE60', lw=2.0)
    axes[3].set_ylabel('valid_out', fontweight='bold', fontsize=9)
    axes[3].set_yticks([0, 1])
    axes[3].set_ylim(-0.2, 1.35)
    axes[3].annotate('', xy=(6.0, 0.85), xytext=(1.0, 0.85),
                     arrowprops=dict(arrowstyle="<->", color='#C0392B', lw=1.8))
    axes[3].text(3.5, 0.42, 'Trễ đường ống = 5 chu kỳ (50 ns)',
                 ha='center', va='center', fontsize=8.8, fontweight='bold', color='#C0392B',
                 bbox=dict(boxstyle="round,pad=0.25", fc="#FDEDEC", ec="#C0392B", lw=1))

    axes[4].step(cycles, y_vals, where='post', color='#E74C3C', lw=2.2)
    axes[4].set_ylabel('data_out\ny[n]', fontweight='bold', fontsize=9)
    axes[4].set_xlabel('Chu kỳ xung nhịp phần cứng (Clock Cycles @ 10 ns/cycle)', fontweight='bold', fontsize=10.5)
    axes[4].set_ylim(-90, 760)
    axes[4].set_xticks(np.arange(0, 22, 1))
    for c_idx in [6, 8, 10, 12, 14, 16, 21]:
        axes[4].scatter([c_idx], [y_vals[c_idx]], color='#C0392B', s=28, zorder=5)
        axes[4].annotate(f'{y_vals[c_idx]}', xy=(c_idx, y_vals[c_idx]), xytext=(0, 6),
                         textcoords='offset points', ha='center', fontsize=8.5, fontweight='bold')

    for ax_i in axes:
        ax_i.grid(True, axis='x', linestyle='--', alpha=0.5)
        ax_i.set_xlim(0, 21.8)

    fig.suptitle('GIẢN ĐỒ XUNG NHỊP MÔ PHỎNG RTL: THÔNG LƯỢNG 1 MẪU / CHU KỲ (BIT-ACCURATE)',
                 fontsize=11.5, fontweight='bold', y=0.98)
    plt.tight_layout()
    chart6_path = os.path.join(OUTPUT_DIR, "chart6_fpga_waveform_timing.png")
    plt.savefig(chart6_path, dpi=300)
    plt.close()
    print(f" -> Da xuat: {chart6_path}")

    print("\n=> HOAN TAT XUAT TOAN BO 4 BIEU DO VAO THU MUC: demo/outputs/charts/")

if __name__ == "__main__":
    plot_all()
