# E5 · Kết quả thí nghiệm và kiểm chứng chéo

Tự động sinh bởi `e5_crosscheck/collect.py`. Nhãn: **đo** (nhóm tự đo trên phần cứng), **mô phỏng**, **ước lượng công cụ** (Vivado), **tính**, **nguồn** (tài liệu trong PLAN.md).

Bài toán chung: FIR 16-tap Q15, 1024 mẫu (seed 3053), 60 mẫu ra bão hòa; mọi nền tảng so từng mẫu với golden model.

## Thông lượng

| Nền tảng | Cấu hình | MSPS | Nhãn | Kiểm tra |
| --- | --- | --- | --- | --- |
| MCU | STM32F103 72 MHz · c_shift_loop | 0.16 | đo | đúng |
| MCU | STM32F103 72 MHz · c_circular_unrolled | 0.33 | đo | đúng |
| MCU | STM32F103 72 MHz · cmsis_arm_fir_q15 | 0.23 | đo | đúng |
| MCU | STM32F103 72 MHz · cmsis_arm_fir_fast_q15 | 0.30 | đo | đúng |
| SoC | Pi 4 A72 · circular_unrolled · -O3 · QEMU 68 lệnh/mẫu, IPC 2 (1–3: 26–79) | 52.96 | ước lượng | đúng (QEMU) |
| FPGA | Arty Z7-20 · 125 MHz trên board | 125.00 | đo | PASS |
| FPGA | XC7Z020 · Fmax ≈ 135 MHz | 134.60 | ước lượng công cụ | Vivado timing, chỉ khối FIR |

## Độ trễ xấu nhất

| Nền tảng | Kịch bản | Xấu nhất | Nhãn | Đại lượng đo |
| --- | --- | --- | --- | --- |
| MCU | ngắt TIM2 · idle_loop | 0.26 µs | đo | sự kiện timer → lệnh đầu ISR |
| MCU | ngắt TIM2 · fir_load | 0.35 µs | đo | sự kiện timer → lệnh đầu ISR |
| MCU | ngắt TIM2 · fir_load_plus_higher_prio_isr_20us | 21.88 µs | đo | sự kiện timer → lệnh đầu ISR |
| SoC | Linux PREEMPT_RT · tài liệu AC6 (cận trên) | 80.00 µs | nguồn | độ trễ lập lịch, Cortex-A đã tinh chỉnh |
| FPGA | pipeline FIR · 125 MHz | 0.06 µs | đo | mẫu vào → mẫu ra |

Các dòng đo những đại lượng khác nhau (ngắt phần cứng, lập lịch Linux, pipeline), chỉ so bậc độ lớn.

## Năng lượng mỗi mẫu

| Nền tảng | Điều kiện | Công suất (W) | nJ/mẫu | Nhãn | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| FPGA | XC7Z020 cả chip @125 MHz | 0.124 | 0.99 | ước lượng công cụ | Vivado vector-less, gồm static |

## Kiểm chứng chéo với PLAN.md

| Câu hỏi | Nhóm đo được | Tài liệu nói | Ghi chú |
| --- | --- | --- | --- |
| Hiệu suất MCU so với giả thiết “1 MAC/chu kỳ” mà PLAN.md dùng cho H743 | 216.3 chu kỳ/mẫu (c_circular_unrolled) → đạt 7% mức lý thuyết | PLAN.md (tính): 1 MAC/chu kỳ | Nếu ≪100%, con số ≈0,48 G MAC/s của H743 trong PLAN là cận trên lạc quan |
| Độ trễ ngắt MCU bare-metal | 264–347 ns (có tải FIR) | AC6 (nguồn): 1–3 µs | Đo từ sự kiện timer đến lệnh đầu tiên của ISR; đã loại 1 mẫu dưới 12 chu kỳ (cờ pending sót lại) |
| MCU khi có ngắt ưu tiên cao hơn chạy 20 µs | xấu nhất 21.9 µs | — | Worst-case MCU do thiết kế phần mềm quyết định, không phải do chip |
| Tỉ lệ thông lượng và độ trễ FPGA / MCU (cùng bài FIR 16-tap) | Thông lượng gấp 375× (125.0 vs 0.33 MSPS); độ trễ nhanh hơn 53.6× (56 vs 3004 ns) | Kiến trúc song song không gian (1 mẫu/chu kỳ) vs tuần tự Cortex-M3 | FPGA giữ nguyên 1 mẫu/chu kỳ khi tăng số tap, còn MCU tăng tuyến tính theo số tap |
| SoC: FIR có chạy đúng trên tập lệnh ARMv8 (Cortex-A72)? | Đúng 100% ở cả 4 bản build (-O2/-O3 × 2 phiên bản), bản ít lệnh nhất 68 lệnh/mẫu | — | Mô phỏng QEMU user-mode; QEMU không mô phỏng thời gian |
| Tỉ lệ thông lượng FPGA / CPU Cortex-A | 2.4× (FPGA 125 MHz, đo) so với Pi 4 ước lượng 53 MSPS (IPC 2; IPC 1–3: 1.6–4.7×) | Arucu & Iliev (nguồn): ≈27× so với Cortex-A9 | Khác: chip CPU, số tap, cách đo |
| Tài nguyên logic cho FIR 16-tap (chế độ thuần LUT, 0 DSP) | 0/220 DSP48E1 (0%), 1672/53200 LUTs (3.1%) | Kiến trúc soft-logic thuần túy (0 DSP) | 16 nhân + bộ cộng dạng cây tổng hợp hoàn toàn trên LUT, Fmax ≈ 135 MHz |
