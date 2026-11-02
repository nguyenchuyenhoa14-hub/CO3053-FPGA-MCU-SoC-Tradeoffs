# CHUYÊN ĐỀ HỆ THỐNG NHÚNG — [HK261] CO3053
## ĐỀ TÀI 09: So sánh MCU – SoC – FPGA: Đánh đổi giữa Hiệu năng, Chi phí và Độ linh hoạt
### *(FPGA vs. MCU vs. SoC — Trade-offs in Performance, Cost, and Flexibility)*

---

## 📌 1. Câu Hỏi Nghiên Cứu & Nguyên Tắc Minh Bạch Số Liệu

Dự án trả lời câu hỏi cốt lõi trong thiết kế hệ thống nhúng: **Khi nào nên chọn Vi điều khiển (MCU), Hệ thống trên vi mạch (SoC chạy Linux), hay Mảng logic khả trình (FPGA) — hoặc phương án lai CPU + FPGA — xét theo hiệu năng, chi phí và độ linh hoạt?**

Tuân thủ phương pháp đánh giá hiệu năng (`pe2`, `pe3`), bài nghiên cứu không đặt mục tiêu thiên vị bất kỳ nền tảng nào. Mọi con số trong báo cáo, slide và biểu đồ đều mang **nhãn nguồn gốc minh bạch**:

| Nhãn | Ý nghĩa | Minh chứng trong dự án |
| :--- | :--- | :--- |
| **`[đo]`** | Nhóm tự đo trực tiếp trên phần cứng vật lý | Đếm chu kỳ `DWT->CYCCNT` & ngắt `TIM2` trên **STM32F103C6 (Blue Pill @ 72 MHz)**; tự kiểm trên chip **Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz)** qua JTAG `BSCANE2` |
| **`[mô phỏng]`** | Kết quả từ trình mô phỏng chu kỳ chính xác | Icarus Verilog (`tb_fir16.v`, `tb_top_arty.v`) kiểm tra 2 kịch bản liên tục và ngắt quãng |
| **`[ước lượng công cụ]`** | Báo cáo tổng hợp & phân tích từ công cụ EDA | AMD Vivado 2025.1.1 (`report_utilization`, `report_timing_summary`, `report_power` vector-less) |
| **`[tính]`** | Tính toán giải tích từ số đo/thông số kèm giả thiết | Tỉ lệ hiệu suất thực tế so với giả thiết lý thuyết $1\text{ MAC/chu kỳ}$ |
| **`[nguồn]`** | Trích dẫn từ tài liệu học thuật và datasheet hãng | STMicroelectronics, AMD/Xilinx, OpenBenchmarking, AC6, Arucu & Iliev (2025), Kou et al. (2023)... |

---

## 🔬 2. Kết Quả Thực Nghiệm Trên Phần Cứng Vật Lý (`experiments/`)

Ba nền tảng cùng thực thi một bài toán chuẩn duy nhất (**E0 — Golden Model**): **Bộ lọc số thông thấp FIR 16-tap định dạng dấu phẩy tĩnh Q15** (cửa sổ Hamming, $f_c = 0{,}2 f_s$, tổng hệ số $= 2^{15}$) với bộ bão hòa 16-bit chuẩn:
$$y[n] = \operatorname{sat}_{16}\!\left(\left\lfloor \frac{\sum_{k=0}^{15} h[k]\,x[n-k]}{2^{15}} \right\rfloor\right)$$
Bộ vector kiểm thử gồm **1 024 mẫu** (seed `3053`: xung đơn vị, bậc thang, biên $\pm 32767$, chuỗi ngẫu nhiên và chuỗi đối kháng gây bão hòa tại **60 mẫu đầu ra**). Mọi nền tảng bắt buộc phải khớp **từng mẫu (0 sai lệch / 1 024 mẫu)** với `golden_out.hex`.

### A. Thực nghiệm E1 — Vi điều khiển STM32F103C6 (Blue Pill, ARM Cortex-M3 @ 72 MHz) `[đo]`
- **Phần cứng & Công cụ:** Chip `STM32F103C6T6` (32 KB Flash, 10 KB SRAM), khóa pha PLL ở **72,0 MHz** từ thạch anh ngoài `HSE 8 MHz × 9` (`2 Flash wait states`). Biên dịch bằng `arm-none-eabi-gcc -O2` (PlatformIO bare-metal CMSIS), nạp và trích xuất dữ liệu trực tiếp từ SRAM qua **ST-Link V2 (SWD @ 950 kHz)**.
- **Đếm chu kỳ phần cứng:** Sử dụng thanh ghi `DWT->CYCCNT` (overhead đo = 28 chu kỳ) khi đã khóa ngắt, lấy trung vị (median) qua 7 lượt chạy.
- **Kết quả thông lượng 4 biến thể FIR (1 024 mẫu):**

| Biến thể thuật toán | Khớp Golden | Chu kỳ / khối (1024 mẫu) | Chu kỳ / mẫu | Thời gian / mẫu | Thông lượng |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`c_circular_unrolled` (Tối ưu nhất)** | **1024/1024 (0 lỗi)** | **221 454** | **216,26** | **3 003,66 ns** | **332,93 kS/s (0,33 MSPS)** |
| `cmsis_arm_fir_fast_q15` | 1024/1024 (0 lỗi) | 242 482 | 236,80 | 3 288,87 ns | 304,05 kS/s (0,30 MSPS) |
| `cmsis_arm_fir_q15` | 1024/1024 (0 lỗi) | 316 083 | 308,67 | 4 287,15 ns | 233,26 kS/s (0,23 MSPS) |
| `c_shift_loop` (Dịch mảng cơ bản) | 1024/1024 (0 lỗi) | 450 192 | 439,64 | 6 106,12 ns | 163,77 kS/s (0,16 MSPS) |

> **Nhận xét kỹ thuật:** Do lõi **ARM Cortex-M3 không có tập lệnh SIMD/DSP** (như lệnh nhân-cộng kép `SMLAD` trên Cortex-M4/M7), phiên bản bộ đệm vòng khai triển vòng lặp (`c_circular_unrolled`) đạt hiệu năng cao nhất (**0,33 MSPS**), tương đương **7%** so với cận trên lý thuyết "1 MAC/chu kỳ".

- **Kết quả đo độ trễ ngắt phần cứng (`TIM2` @ 10 kHz, 20 000 lần ngắt mỗi kịch bản):**

| Kịch bản tải hệ thống | Số mẫu | Nhỏ nhất | Trung bình | Xấu nhất (Max) | Quy đổi thời gian (Max) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. `idle_loop` (CPU rảnh)** | 20 000 | 19 chu kỳ | 19,00 chu kỳ | **19 chu kỳ** | **263,89 ns** (Jitter = 0) |
| **2. `fir_load` (CPU chạy FIR liên tục)** | 20 000 | 0 chu kỳ | 19,72 chu kỳ | **25 chu kỳ** | **347,22 ns** |
| **3. `fir_load_plus_higher_prio_isr_20us`** | 20 000 | 0 chu kỳ | 35,24 chu kỳ | **1 575 chu kỳ** | **21,88 µs** (331 lần > 255 chu kỳ) |

---

### B. Thực nghiệm E2 — FPGA Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz, Thuần LUT / 0 DSP) `[đo]` & `[ước lượng công cụ]`
- **Kiến trúc phần cứng RTL (`experiments/e2_fpga/rtl/fir16.v`):**
  - Thiết kế đường ống đồng bộ **7 tầng thanh ghi (`S0..S6`)**, nhận và xuất liên tục **1 mẫu / chu kỳ xung nhịp**.
  - Thực thi ở **chế độ thuần Soft-Logic (LUT-only, 0 khối DSP48E1)** bằng thuộc tính RTL `(* use_dsp = "no" *)` và cờ tổng hợp Vivado `-max_dsp 0`: toàn bộ 16 bộ nhân song song (tầng `S1`) và cây cộng nhị phân 4 mức 34-bit (`S2..S5`) được ánh xạ hoàn toàn lên mạng **Slice LUTs + chuỗi nhớ nhanh `CARRY4`**.
- **Mạch tự kiểm trên chip (`top_arty.v`):**
  - Chạy trực tiếp trên vùng logic khả trình **Artix-7 PL** của chip `xc7z020clg400-1` với nguồn xung nhịp gốc **125,0 MHz** (chân `H16`, chu kỳ $8{,}0\text{ ns}$).
  - Sau khi nạp bitstream, FSM tự động bơm 1 024 mẫu từ Block RAM vào bộ lọc FIR, đối chiếu từng mẫu đầu ra với `golden_out.hex` ngay trên chip và xuất kết quả qua giao diện **JTAG `BSCANE2` (`USER4`)** cùng cổng **UART 115200 8N1** (chân Pmod `JA[0]` = `Y18`).
- **Thông số đo thực tế trên board & Báo cáo Vivado 2025.1.1:**

| Chỉ số kỹ thuật | Giá trị thực tế | Nhãn nguồn gốc | Ghi chú chi tiết |
| :--- | :---: | :---: | :--- |
| **Chuỗi báo cáo từ chip** | `PASS N=0400 ERR=0000 LAT=0007 CYC=00000407 FBAD=FFFF` | **`[đo]`** | Đọc trực tiếp qua JTAG `USER4` từ board Arty Z7-20 |
| **Độ chính xác bit-accurate** | **PASS 1 024 / 1 024 mẫu (0 lỗi)** | **`[đo]`** | Khớp tuyệt đối 100% với golden model (kể cả 60 mẫu bão hòa) |
| **Độ trễ đường ống (Latency)** | **7 chu kỳ = 56,0 ns** | **`[đo]`** | Tiền định tuyệt đối theo chu kỳ xung nhịp (0 chu kỳ jitter) |
| **Tổng chu kỳ xử lý 1 024 mẫu** | **1 031 chu kỳ** ($1024 + 7$) | **`[đo]`** | Xử lý xong toàn bộ 1 024 mẫu trong $8{,}248\ \mu\text{s}$ |
| **Thông lượng trên board (@ 125 MHz)** | **1,0000 mẫu/chu kỳ = 125,00 MSPS** | **`[đo]`** | **Nhanh gấp 375× thông lượng** và **53,6× độ trễ** so với MCU |
| **Số khối DSP48E1 sử dụng** | **0 / 220 (0,00%)** | **`[ước lượng công cụ]`** | Thuần logic LUT (`use_dsp = "no"`, `-max_dsp 0`) |
| **Tài nguyên Slice LUTs (khối FIR)** | **1 672 / 53 200 (3,14%)** | **`[ước lượng công cụ]`** | 16 bộ nhân Q15 + cây cộng 34-bit bằng LUT + `CARRY4` |
| **Tài nguyên Thanh ghi FF (khối FIR)** | **1 046 / 106 400 (0,98%)** | **`[ước lượng công cụ]`** | 7 tầng thanh ghi pipeline |
| **Block RAM (`top_arty`)** | **2 / 140 tiles (1,43%)** | **`[ước lượng công cụ]`** | Lưu trữ `vectors_in.hex` và `golden_out.hex` |
| **Tần số tối đa khối FIR ($F_{\max}$)** | **$\approx 134,6\text{ MHz}$** ($\approx 134{,}6\text{ MSPS}$) | **`[ước lượng công cụ]`** | Phân tích định thời Out-of-Context của Vivado (`WNS = +0,326 ns` trên `top_arty` @ 125 MHz) |
| **Công suất toàn chip (@ 125 MHz)** | **0,124 W** (Dynamic `0,018 W` + Static `0,106 W`) | **`[ước lượng công cụ]`** | Tiêu tốn $\approx \mathbf{0{,}99\text{ nJ/mẫu}}$ (thấp hơn bản dùng DSP `0,129 W`) |

---

## 📊 3. Bảng Tổng Hợp Kiểm Chứng Chéo (E5)

File [`experiments/results/E5_crosscheck.md`](experiments/results/E5_crosscheck.md) và [`experiments/results/numbers.tex`](experiments/results/numbers.tex) được sinh tự động hoàn toàn từ `python experiments/e5_crosscheck/collect.py`:

| Câu hỏi kiểm chứng | Kết quả nhóm đo / tổng hợp | Số liệu trong tài liệu | Kết luận kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Hiệu suất thực tế của MCU so với giả thiết "1 MAC/chu kỳ"** | **216,3 chu kỳ/mẫu** (`c_circular_unrolled`) $\rightarrow$ đạt **7%** mức lý thuyết | `PLAN.md` `[tính]`: giả định 1 MAC/chu kỳ | Chi phí nạp toán hạng, cập nhật trễ và `2 Flash wait states` khiến con số lý thuyết chỉ là cận trên lạc quan |
| **Tương quan FPGA vs. MCU trên cùng bài FIR 16-tap** | **Thông lượng gấp 375×** (`125,0` vs `0,33 MSPS`); **độ trễ nhanh hơn 53,6×** (`56 ns` vs `3 004 ns`) | Kiến trúc song song không gian vs. tuần tự | FPGA giữ nguyên 1 mẫu/chu kỳ khi tăng số tap, còn MCU chậm đi tuyến tính theo số tap |
| **Độ trễ ngắt MCU bare-metal** | **264 ns** (rảnh) · **0–347 ns** (tải FIR) | AC6 `[nguồn]`: $1\text{–}3\ \mu\text{s}$ | Phần cứng Cortex-M3 phản hồi cực nhanh dưới $0{,}35\ \mu\text{s}$ |
| **MCU khi có ngắt ưu tiên cao hơn chiếm 20 µs** | Xấu nhất **21,88 µs** (1 575 chu kỳ) | — | **Worst-case của MCU do kiến trúc phần mềm quyết định**, không phải do phần cứng |
| **Tài nguyên FPGA ở chế độ thuần LUT (0 DSP)** | **0/220 DSP (0%)**, **1 672/53 200 LUT (3,14%)**, **1 046/106 400 FF (0,98%)** | $F_{\max} \approx 134{,}6\text{ MHz}$, công suất **0,124 W** | Chỉ dùng ~3,1% LUT của XC7Z020 đã đạt 125 MSPS, dành trọn 220 DSP48E1 cho các tác vụ khác |

---

## 📄 4. Báo Cáo Học Thuật & Slide Thuyết Trình (`report/`)

Toàn bộ số liệu từ `experiments/results/numbers.tex` và biểu đồ trong `experiments/results/charts/` được nhúng tự động vào hệ thống tài liệu XeLaTeX:

1. **Báo cáo chuyên đề (12 trang A4):** [`report/report.pdf`](report/report.pdf) (mã nguồn [`report/report.tex`](report/report.tex)).
2. **Slide thuyết trình chuẩn HCMUT (23 trang 16:9):** [`report/slides_hcmut.pdf`](report/slides_hcmut.pdf) (mã nguồn [`report/slides_hcmut.tex`](report/slides_hcmut.tex)).
3. **Slide thuyết trình bản tối giản (23 trang 16:9):** [`report/slides.pdf`](report/slides.pdf) (mã nguồn [`report/slides.tex`](report/slides.tex)).

---

## 🚀 5. Hướng Dẫn Chạy Lại Thực Nghiệm & Biên Dịch Báo Cáo

### A. Chạy bộ thực nghiệm phần cứng (`experiments/`)
```bash
# 1. Sinh lại vector kiểm thử & golden model (E0)
python experiments/e0_golden/gen_vectors.py

# 2. Build, nạp firmware STM32F103C6 qua ST-Link V2 và trích xuất kết quả từ SRAM qua SWD (E1)
pio run -d experiments/e1_mcu -e f103c6 -t upload
python experiments/tools/capture_serial.py mcu swd

# 3. Tổng hợp Vivado (thuần LUT, 0 DSP), nạp bitstream lên Arty Z7-20 và đọc kết quả qua JTAG (E2)
vivado -mode batch -source experiments/e2_fpga/vivado/build.tcl
vivado -mode batch -source experiments/e2_fpga/vivado/program.tcl

# 4. Cập nhật bảng kiểm chứng chéo E5, biểu đồ và macro số liệu LaTeX (E5)
python experiments/e5_crosscheck/collect.py
```

### B. Biên dịch Báo cáo và Slide (`report/`)
```bash
cd report
xelatex -interaction=nonstopmode report.tex
xelatex -interaction=nonstopmode slides.tex
xelatex -interaction=nonstopmode slides_hcmut.tex
```

---

## 📂 6. Cấu Trúc Thư Mục Dự Án

```text
CO3053-FPGA-MCU-SoC-Tradeoffs/
├── .gitignore                          # Quy tắc loại trừ file tạm, thư mục build (.pio, build, .Xil, LaTeX aux)
├── README.md                           # Tổng quan dự án, số liệu thực nghiệm phần cứng và hướng dẫn tái lập
├── PLAN.md                             # Đề cương nghiên cứu, nguồn tài liệu tham khảo và phân tích ứng dụng
├── PLAN_v2.md                          # Kế hoạch thực nghiệm E0–E5 và quy tắc dán nhãn nguồn gốc số liệu
├── experiments/                        # Bộ thực nghiệm phần cứng chuẩn hóa (E0–E5)
│   ├── Makefile                        # Điều phối tự động build, flash, capture và collect
│   ├── README.md                       # Tài liệu chi tiết từng bài thí nghiệm E0–E5
│   ├── Flash.md                        # Hướng dẫn nối dây và nạp từng board (STM32F103 & Arty Z7-20)
│   ├── common/fir/                     # Mã nguồn C FIR 16-tap Q15 và vector kiểm thử dùng chung
│   ├── e0_golden/gen_vectors.py        # Script sinh hệ số FIR, 1024 vector kiểm thử và golden model
│   ├── e1_mcu/                         # Firmware bare-metal CMSIS cho STM32F103 (Cortex-M3 @ 72 MHz)
│   │   ├── platformio.ini              # Cấu hình PlatformIO (env:f103c6 và env:f103)
│   │   └── src/main.c                  # Đo thông lượng 4 biến thể FIR (DWT) & độ trễ ngắt TIM2/TIM3
│   ├── e2_fpga/                        # Thiết kế RTL & kịch bản Vivado cho Digilent Arty Z7-20 (125 MHz)
│   │   ├── constr/arty_z7_20.xdc       # Ràng buộc chân và xung nhịp 125 MHz (H16) trên xc7z020clg400-1
│   │   ├── rtl/fir16.v                 # Pipeline FIR 7 tầng thuần LUT (use_dsp = "no", 0 DSP48E1)
│   │   ├── rtl/top_arty.v              # Mạch tự kiểm 1024 mẫu trên chip + đọc kết quả qua JTAG BSCANE2 / UART
│   │   ├── tb/                         # Testbench kiểm thử tự động (tb_fir16.v, tb_top_arty.v)
│   │   └── vivado/                     # Script tổng hợp (build.tcl, -max_dsp 0) và nạp/đọc JTAG (program.tcl)
│   ├── e3_soc/                         # Benchmark FIR và cyclictest cho SoC Linux (Raspberry Pi 4)
│   ├── e5_crosscheck/collect.py        # Tự động tổng hợp JSON -> E5_crosscheck.md, numbers.tex & charts
│   ├── tools/capture_serial.py         # Công cụ thu thập kết quả qua ST-Link SWD hoặc UART
│   └── results/                        # Dữ liệu thực nghiệm gốc (JSON), bảng kiểm chứng và biểu đồ
│       ├── e0_spec.json                # Đặc tả bộ lọc FIR 16-tap Q15 và 1024 mẫu chuẩn
│       ├── e1_mcu.json                 # Số liệu đo vật lý trên STM32F103C6 @ 72 MHz
│       ├── e2_fpga_sim.json            # Số liệu mô phỏng RTL Icarus Verilog
│       ├── e2_fpga_impl.json           # Số liệu tổng hợp Vivado 2025.1.1 (0 DSP, 1672 LUT, 1046 FF, 0.124 W)
│       ├── e2_fpga_board.json          # Số liệu chạy thật trên board Digilent Arty Z7-20 @ 125 MHz
│       ├── E5_crosscheck.md            # Bảng tổng hợp và kiểm chứng chéo tự động
│       ├── numbers.tex                 # Macro số liệu tự động nhúng vào báo cáo và slide LaTeX
│       └── charts/                     # Biểu đồ sinh tự động từ dữ liệu thực nghiệm
├── report/                             # Báo cáo học thuật và Slide thuyết trình (XeLaTeX)
│   ├── report.tex / report.pdf         # Báo cáo chuyên đề 12 trang
│   ├── slides_hcmut.tex / .pdf         # Slide thuyết trình mẫu HCMUT (23 trang)
│   ├── slides.tex / slides.pdf         # Slide thuyết trình bản tiêu chuẩn (23 trang)
│   ├── slides_body.tex                 # Nội dung slide dùng chung
│   ├── ket_qua.tex                     # File cấu hình ghi đè số liệu tùy chọn
│   └── figs/                           # Hình minh họa phần cứng, biểu đồ tài liệu và nguồn trích dẫn
└── demo/                               # Bộ mô phỏng ý tưởng ban đầu (lưu trữ tham khảo)
```
