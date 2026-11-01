# CHUYÊN ĐỀ HỆ THỐNG NHÚNG — [HK261] CO3053
## ĐỀ TÀI 09: FPGA và MCU và SoC — Đánh đổi Hiệu năng, Chi phí, Độ linh hoạt
### *(FPGA vs. MCU vs. SoC — Trade-offs in Performance, Cost, and Flexibility)*

---

## 📌 1. Tổng Quan Đề Tài & Mục Tiêu Nghiên Cứu

Trong kỷ nguyên bùng nổ của Trí tuệ nhân tạo biên (Edge AI), Robot tự hành và các hệ thống thời gian thực khắt khe, việc lựa chọn nền tảng điện toán phần cứng tối ưu đóng vai trò quyết định đến sự thành bại của một sản phẩm hệ thống nhúng. Dự án này tiến hành nghiên cứu đối sánh chuyên sâu giữa ba nền tảng phổ biến nhất:

1. **Vi điều khiển (Microcontroller Unit - MCU):** Kiến trúc tuần tự theo thời gian (*Temporal Computing*) dựa trên chu trình nạp - giải mã - thực thi chỉ lệnh (*Fetch – Decode – Execute*), tối ưu cho tiêu thụ điện chế độ nghỉ siêu thấp và chi phí linh kiện tối thiểu.
2. **Mảng logic khả trình (Field-Programmable Gate Array - FPGA):** Kiến trúc song song trên không gian phần cứng (*Spatial Computing*) cấu thành từ các khối CLB/LUT, DSP Slices và Block RAM, cung cấp thông lượng ở tốc độ đường truyền và tính tiền định chính xác theo chu kỳ xung nhịp (*Cycle-accurate determinism* với độ dao động ngắt Jitter bằng 0.00 ns).
3. **Hệ thống trên một vi mạch dị thể (Heterogeneous SoC):** Tích hợp phân hệ vi xử lý ứng dụng (Processing System - PS) và phân hệ logic khả trình (Programmable Logic - PL) trên cùng một đế bán dẫn nguyên khối (Monolithic Die), điển hình như AMD/Xilinx Zynq-7000 kết nối qua chuẩn bus nội mạch tốc độ cao **AMBA AXI4**.

---

## ⚖️ 2. Ma Trận Đánh Đổi Kỹ Thuật Đa Chiều

| Tiêu chí đánh giá | Vi điều khiển (MCU) | FPGA Độc lập | Heterogeneous SoC (Zynq) |
|:---|:---:|:---:|:---:|
| **Mô hình tính toán** | Tuần tự theo thời gian (*Temporal*) | Song song không gian (*Spatial*) | Lai: Tuần tự (PS) + Song song (PL) |
| **Độ trễ phản hồi vật lý** | Micro-giây ($1 - 10\ \mu\text{s}$) | Nano-giây ($< 10\ \text{ns}$) | Phân tầng: $\text{ns}$ tại PL / $\mu\text{s}$ tại PS |
| **Độ dao động ngắt (Jitter)** | Kèm Jitter do RTOS & ngắt | **0.00 ns (Tiền định 100%)** | 0.00 ns tại logic / $< 1\ \mu\text{s}$ qua DMA |
| **Thông lượng DSP (Throughput)** | $4.66 - 13.33\ \text{MSPS}$ | **$100.0\ \text{MSPS}$** | **$150.0\ \text{MSPS}$** |
| **Công suất chế độ nghỉ** | **Cực thấp ($\mu\text{A} - \text{nA}$)** | Trung bình - Cao (dòng rò SRAM) | Phụ thuộc chế độ Sleep của CPU |
| **Hiệu quả năng lượng DSP** | $18.64\ \text{MSamples/Joule}$ | **$83.33\ \text{MSamples/Joule}$** | $60.00\ \text{MSamples/Joule}$ |
| **Chi phí thiết kế ban đầu (NRE)**| Rất thấp (công cụ mở, dev C nhanh) | Rất cao (kỹ sư HDL, Timing Closure)| Cao (đòi hỏi Linux + Phần cứng số) |
| **Đơn giá linh kiện (Unit BOM)** | **Rất rẻ ($0.50 - $10)** | Trung bình - Đắt ($20 - $200+) | Trung bình - Cao ($30 - $350+) |
| **Thời gian ra thị trường (TTM)**| Rất ngắn (1 - 3 tháng) | Dài (6 - 12 tháng) | Trung bình (4 - 8 tháng) |

---

## 🔬 3. Bộ Thực Nghiệm Đối Sánh Định Lượng (`demo/`)

Để kiểm chứng lý thuyết bằng số liệu thực nghiệm định lượng, nhóm đã hiện thực bài toán kinh điển trong xử lý tín hiệu số: **Thuật toán bộ lọc số FIR 16-tap dạng dấu phẩy tĩnh Q15** ($y[n] = \lfloor \sum_{k=0}^{15} h[k] \cdot x[n-k] / 2^{15} \rfloor$) trên cả ba nền tảng:

### A. Vi điều khiển ARM Cortex-M (`demo/mcu_firmware/fir_mcu.c`)
- Hiện thực bằng C tối ưu với vòng lặp khai triển 16 bước nhân-cộng (Loop unrolling).
- Đo đạc chính xác chu kỳ CPU: mất trung bình **36 chu kỳ xung nhịp / mẫu** do chi phí nạp toán hạng từ SRAM, cập nhật trễ tuần tự và chia sẻ ALU.
- Thông lượng tối đa trên STM32F4 (168 MHz): **4.66 MSamples/s** (214.28 ns/mẫu).
- Thông lượng tối đa trên STM32H7 (480 MHz): **13.33 MSamples/s** (75.00 ns/mẫu).

### B. Mạch phần cứng FPGA Artix-7 (`demo/fpga_rtl/fir_filter_16tap.v`)
- Hiện thực bằng Verilog HDL với cấu trúc đường ống đồng bộ 5 tầng (5-Stage Pipelined Architecture).
- Tầng 1 gồm 16 bộ nhân DSP hoạt động song song đồng thời; Tầng 2–5 là cây cộng dồn nhị phân 4 mức ($16 \rightarrow 8 \rightarrow 4 \rightarrow 2 \rightarrow 1$).
- **Kiểm chứng tương đương mức bit (Bit-Accurate Verification):** Khi kích thích bằng xung bước nhảy $x[n] = 1000$, cả phần mềm C trên MCU và mạch RTL Verilog đều cho ra dãy 20 mẫu đáp ứng quá độ và xác lập **khớp nhau 100% với sai số 0 LSB**:
  $$y[1..20] = \{-4, 1, 12, 34, 72, 130, 205, 290, 375, 450, 508, 546, 568, 579, 584, 581, 581, 581, 581, 581\}$$
- Sau 5 chu kỳ khởi động đường ống (50 ns @ 100 MHz), mạch xuất ra **đúng 1 mẫu kết quả trên mỗi chu kỳ xung nhịp (Throughput = 100.0 MSPS)**, nhanh hơn **gấp 21.4 lần** so với Cortex-M4.

### C. Mô phỏng Heterogeneous SoC Zynq-7000 (`demo/soc_emulation/soc_axi_dma_sim.py`)
- Mô hình hóa cơ chế tăng tốc qua luồng truyền **AXI4-Stream DMA chồng lấp (`MM2S` $\rightarrow$ `FIR_16TAP` $\rightarrow$ `S2MM`)** giữa nhân ARM Cortex-A9 (PS) và bộ tăng tốc FPGA (PL).
- Phân tích chi phí mặt phẳng điều khiển cố định: $T_{\text{setup}} = 350\text{ ns}$ (ghi thanh ghi cấu hình qua AXI4-Lite) và $T_{\text{IRQ}} = 850\text{ ns}$ (độ trễ phản hồi ngắt GIC).
- **Kết quả đánh đổi theo kích thước gói $N$:**
  - Gói nhỏ ($N = 16$): Chi phí khởi tạo $1.20\ \mu\text{s}$ chiếm ưu thế $\rightarrow$ Tăng tốc chậm hơn CPU ($0.34\times$).
  - Ngưỡng hòa vốn: Đạt được tại $N \approx 48$ mẫu.
  - Gói lớn ($N \ge 1.024$): Đường ống AXI4-Stream phát huy tối đa thông lượng, tăng tốc **$3.78\times - 4.48\times$** so với Cortex-A9 667 MHz (và **$>30\times$** so với Cortex-M4), đồng thời **giải phóng 96.1% – 99.9% tải CPU** cho hệ điều hành Linux.

---

## 📊 4. Bộ Biểu Đồ Đối Sánh Khoa Học 300 DPI (`demo/outputs/charts/`)

| Tên tệp tin đồ thị | Nội dung thể hiện | Thông điệp kỹ thuật cốt lõi |
|:---|:---|:---|
| **`chart1_throughput_comparison.png`** | Đối sánh thông lượng xử lý mẫu (MSPS) trên 5 nền tảng | FPGA đạt 100 MSPS (nhanh gấp 21.4x lần Cortex-M4 @ 168 MHz) dù xung nhịp thấp hơn 40%. |
| **`chart2_latency_and_jitter.png`** | Độ trễ phản hồi vật lý và dao động Jitter thời gian thực (thang Log) | FPGA phản hồi trong 10.0 ns với Jitter 0.00 ns, vượt trội hoàn toàn so với Jitter micro-giây của MCU. |
| **`chart3_energy_efficiency.png`** | Hiệu quả năng lượng tính toán (Triệu mẫu xử lý / Joule) | FPGA đạt 83.3 MSamples/J (gấp 4.5x lần Cortex-M4) do không tốn điện nạp - giải mã lệnh tuần tự. |
| **`chart4_breakeven_cost_analysis.png`** | Phân tích kinh tế NRE vs. BOM và điểm hòa vốn sản xuất | Xác định điểm hòa vốn giữa FPGA và ASIC chuyên dụng tại quy mô $\approx 42.000$ thiết bị thương mại. |
| **`chart5_soc_dma_offload.png`** | Đánh đổi kích thước gói AXI4-Stream DMA và tỷ lệ giải phóng CPU | Gói nhỏ ($N < 48$) nên tính trên CPU; gói lớn ($N \ge 1024$) tăng tốc 4.48x và giải phóng 99% CPU cho Linux. |
| **`chart6_fpga_waveform_timing.png`** | Giản đồ xung nhịp mô phỏng RTL (clk, valid_in, data_in, valid_out, data_out) | Minh chứng trực quan độ trễ pipeline 5 chu kỳ (50 ns) và xuất 1 mẫu/chu kỳ khớp bit-accurate $y[n]$. |

---

## 🚀 5. Hướng Dẫn Chạy Thực Nghiệm 1-Click

Kho lưu trữ đã được cấu hình sẵn sàng để thực thi trên hệ điều hành Windows:

### Yêu cầu môi trường:
- Trình biên dịch C: `gcc` (MinGW / MSYS2 / TDM-GCC).
- Trình mô phỏng Verilog: `iverilog` (Icarus Verilog) và `vvp`.
- Môi trường Python: Python 3.8+ với các thư viện `numpy`, `matplotlib`.
- Trình xem dạng sóng (tùy chọn): `GTKWave`.

### Lệnh thực thi:
1. **Chạy toàn bộ quy trình tự động qua script Python:**
   ```bash
   cd demo
   python run_demo.py
   ```
2. **Hoặc nhấp đúp chuột vào file batch trên Windows:**
   ```cmd
   demo\run_demo.bat
   ```

Quy trình sẽ tự động thực hiện 4 bước liên hoàn:
- `[Bước 1/4]` Biên dịch mã nguồn C và đo chu kỳ thực thi trên MCU (`fir_mcu.exe`).
- `[Bước 2/4]` Tổng hợp và mô phỏng chu kỳ xung nhịp Verilog RTL (`iverilog` $\rightarrow$ `vvp`), xuất file dạng sóng `fir_simulation.vcd`.
- `[Bước 3/4]` Chạy mô phỏng truyền gói dữ liệu qua AXI4-Stream DMA trên Heterogeneous SoC Zynq.
- `[Bước 4/4]` Xuất toàn bộ 6 biểu đồ chất lượng cao 300 DPI vào thư mục `demo/outputs/charts/`.

---

## 📂 6. Cấu Trúc Thư Mục Dự Án

```
CO3053-FPGA-MCU-SoC-Tradeoffs/
├── .gitignore                          # Quy tắc loại trừ tệp tin biên dịch và cấu hình cục bộ
├── README.md                           # Báo cáo tổng quan dự án và cẩm nang kỹ thuật
└── demo/                               # Thư mục bộ thực nghiệm đối sánh định lượng
    ├── DEMO_PRESENTATION_GUIDE.md      # Cẩm nang thuyết trình phần demo 90 giây
    ├── run_demo.bat                    # Script 1-click chạy demo trên Windows
    ├── run_demo.py                     # Bộ điều phối tự động 4 bước thực nghiệm
    ├── fpga_rtl/                       # Mã nguồn thiết kế phần cứng FPGA
    │   ├── fir_filter_16tap.v          # Module phần cứng Verilog FIR 16-tap 5 tầng pipeline
    │   ├── tb_fir_filter.v             # Testbench kiểm thử chu kỳ và xuất dạng sóng VCD
    │   └── fir_simulation.vcd          # File dạng sóng xung nhịp mở trên GTKWave
    ├── mcu_firmware/                   # Mã nguồn phần mềm vi điều khiển
    │   ├── fir_mcu.c                   # Thuật toán FIR C đo đạc chu kỳ CPU và kiểm chứng bit-accurate
    │   └── mcu_benchmark.json          # Số liệu đo đạc hiệu năng trên MCU
    ├── soc_emulation/                  # Mô phỏng Heterogeneous SoC
    │   ├── soc_axi_dma_sim.py          # Mô phỏng đường truyền AXI4-Stream DMA (PS-PL)
    │   └── soc_benchmark.json          # Số liệu tăng tốc và giải phóng CPU theo kích thước gói
    ├── visualization/                  # Script đồ họa trực quan hóa
    │   └── plot_benchmark_results.py   # Script vẽ 6 biểu đồ khoa học chuẩn IEEE 300 DPI
    └── outputs/                        # Thư mục kết quả đầu ra
        ├── fir_simulation.vcd          # File dạng sóng phục vụ trình diễn
        ├── mcu_benchmark.json          # Báo cáo JSON MCU
        ├── soc_benchmark.json          # Báo cáo JSON SoC DMA
        └── charts/                     # Bộ 6 hình ảnh biểu đồ định dạng PNG 300 DPI
            ├── chart1_throughput_comparison.png
            ├── chart2_latency_and_jitter.png
            ├── chart3_energy_efficiency.png
            ├── chart4_breakeven_cost_analysis.png
            ├── chart5_soc_dma_offload.png
            └── chart6_fpga_waveform_timing.png
```
