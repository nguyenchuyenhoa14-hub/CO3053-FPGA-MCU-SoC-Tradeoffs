# Thí nghiệm của nhóm (E0–E5)

Bộ thí nghiệm viết lại theo [PLAN_v2.md](../PLAN_v2.md). Thư mục `demo/` cũ chỉ còn để tham khảo, không lấy số từ đó.

Bài toán chung là **FIR 16-tap Q15**: cùng hệ số, cùng 1024 mẫu vào, và mọi nền tảng phải khớp từng mẫu với golden model. Mỗi con số trong `results/` mang một nhãn: `đo`, `mô phỏng`, `ước lượng công cụ`, `tính` hoặc `nguồn`.

| Bước | Nội dung | Chạy ở đâu | Đầu ra |
| --- | --- | --- | --- |
| E0 | Golden model, hệ số, vector | máy nào cũng được | `common/fir/fir_vectors.h`, `e2_fpga/mem/*.hex`, `results/e0_spec.json` |
| E1 | STM32F103C6 (Blue Pill @ 72 MHz): 4 phiên bản FIR, độ trễ ngắt, các pha đo dòng | Blue Pill + ST-Link V2 (SWD) | `results/e1_mcu.json` |
| E2 | Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz, thuần LUT / 0 DSP): mô phỏng RTL, Vivado, tự kiểm trên board | PC có Vivado + Arty Z7-20 | `results/e2_fpga_{sim,impl,board}.json` |
| E3 | Raspberry Pi 4: thông lượng FIR, `cyclictest` | Pi 4 | `results/e3_*.json` |
| E5 | Bảng kiểm chứng chéo với PLAN.md + chart | máy nào cũng được | `results/E5_crosscheck.md`, `results/numbers.tex`, `results/charts/` |

## Chạy nhanh bằng Makefile

```bash
make ports                              # xem cổng serial đang cắm
make mcu                                # STM32: build, nạp ST-Link, tự đọc kết quả qua SWD
make fpga                               # Arty Z7-20: Vivado build (0 DSP), nạp JTAG, tự đọc kết quả
make pi   PI=pi@192.168.1.50            # Pi 4 qua SSH: copy code, chạy benchmark + cyclictest, kéo kết quả về
make collect                            # bảng kiểm chứng chéo + chart + numbers.tex
```

`make help` liệt kê từng bước riêng (`mcu-flash`, `fpga-build`, `pi-bench`…). Các phần dưới đây mô tả chi tiết từng thí nghiệm.

## E0 · Golden model (đã chạy)

```bash
python3 e0_golden/gen_vectors.py
```

- Hệ số: low-pass windowed-sinc (Hamming), fc = 0,2·fs, tổng = 2^15 (khuếch đại DC = 1).
- Vector gồm xung đơn vị, bậc thang, giá trị biên, mẫu đối kháng (ép bão hòa: 60 mẫu ra) và ngẫu nhiên (seed 3053).
- Có sửa hệ số thì chạy lại E0 trước mọi bước khác.

## E1 · MCU STM32F103 (Blue Pill — đã đo trên phần cứng thật)

**Nối dây:**
- ST-Link V2 nối 4 dây `SWDIO`, `SWCLK`, `GND`, `3.3V` vào header SWD của Blue Pill.
- **Đọc kết quả trực tiếp qua ST-Link SWD** (không cần cáp USB-UART rời), hoặc tùy chọn nối thêm **PA9 (TX) → RX của USB-UART**.

```bash
cd e1_mcu
pio run -e f103c6 -t upload                         # build + nạp qua ST-Link (STM32F103C6: 32KB Flash, 10KB RAM)
python ../tools/capture_serial.py mcu swd           # tự reset, đợi 9s và trích xuất kết quả từ SRAM qua SWD -> results/e1_mcu.json
# Hoặc nếu dùng USB-UART rời nối vào PA9:
python ../tools/capture_serial.py mcu /dev/ttyUSB0  # rồi nhấn RESET trên Blue Pill
```

**Firmware đo những gì** (khoảng 9 giây, lưu vào SRAM và phát JSON qua USART1):
- **Thông lượng** của 4 phiên bản: C dịch đường trễ (`c_shift_loop`), C bộ đệm vòng khai triển (`c_circular_unrolled`), CMSIS `arm_fir_q15`, CMSIS `arm_fir_fast_q15`.
  - Mỗi phiên bản được kiểm tra với golden (0 sai lệch / 1024 mẫu) và đếm chu kỳ bằng `DWT->CYCCNT` khi đã tắt ngắt; lấy median của 7 lần chạy.
  - Cortex-M3 **không có SIMD** (`SMLAD`), nên bản bộ đệm vòng khai triển (`c_circular_unrolled`) đạt tốt nhất **216,26 chu kỳ/mẫu** (**332,93 kS/s ≈ 0,33 MSPS** ở 72 MHz, đạt 7% mức lý thuyết 1 MAC/chu kỳ).
- **Độ trễ ngắt** với TIM2 ở 10 kHz, 20 000 mẫu cho mỗi kịch bản:
  - CPU rảnh (`idle_loop`): cố định **19 chu kỳ = 263,89 ns** (jitter = 0 chu kỳ);
  - CPU đang chạy FIR (`fir_load`): **0–25 chu kỳ = 0–347,22 ns** (trung bình 19,72 chu kỳ);
  - CPU chạy FIR và có thêm ngắt TIM3 **ưu tiên cao hơn** chiếm ~20 µs: xấu nhất **1 575 chu kỳ = 21,88 µs**.
  - Kịch bản thứ ba chứng minh thực nghiệm: worst-case của MCU do kiến trúc phần mềm/ngắt lồng nhau quyết định, không phải do giới hạn phần cứng.
- **Các pha đo dòng**, chạy sau khi in JSON (`RUN_FIR` 20 s → `SLEEP` 20 s → `STANDBY`).

## E2 · FPGA Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz, thuần LUT / 0 DSP — đã đo trên phần cứng thật)

```bash
cd e2_fpga
./run_sim.sh                                   # Icarus: 2 lượt (liên tục + có khoảng trống), tự so golden -> results/e2_fpga_sim.json
vivado -mode batch -source vivado/build.tcl    # tổng hợp thuần LUT (-max_dsp 0) -> results/e2_fpga_impl.json + bitstream
vivado -mode batch -source vivado/program.tcl  # nạp vào board + tự đọc kết quả qua JTAG USER4 -> results/e2_fpga_board.json
```

- **RTL** ([rtl/fir16.v](e2_fpga/rtl/fir16.v)): pipeline 7 tầng, 1 mẫu/chu kỳ, có bão hòa giống golden, gắn thuộc tính `(* use_dsp = "no" *)` và cờ tổng hợp `-max_dsp 0` để thực thi **100% bằng logic LUT + CARRY4 (0 khối DSP48E1)**.
- **Tự kiểm trên board** ([rtl/top_arty.v](e2_fpga/rtl/top_arty.v)):
  - Chạy trực tiếp trên vùng logic khả trình **Artix-7 PL** của chip Zynq-7020 (`xc7z020clg400-1`, 220 khối DSP48E1, 53 200 LUT, 106 400 FF) ở xung nhịp gốc **125,0 MHz** (chân `H16`, chu kỳ 8 ns).
  - Đọc 1024 mẫu từ BRAM ở 125 MHz, so từng mẫu với golden ngay trên chip: **PASS 1024/1024 mẫu (0 lỗi)**, độ trễ **7 chu kỳ = 56,0 ns**, thông lượng **1,0000 mẫu/chu kỳ = 125,00 MSPS** (nhanh gấp **375×** thông lượng và **53,6×** độ trễ so với STM32F103).
  - Xuất kết quả đồng thời qua JTAG `USER4` (`BSCANE2`, tự động đọc bởi `vivado/program.tcl`) và qua UART 115200 8N1 tại chân **Pmod `JA[0]` (`Y18`)**: `FIR16 PASS N=0400 ERR=0000 LAT=0007 CYC=00000407 FBAD=FFFF`.
- **Vivado** (`build.tcl`, chế độ thuần LUT `-max_dsp 0`):
  - (A) chỉ khối FIR, out-of-context: **0 / 220 DSP48E1 (0%)**, **1 672 / 53 200 LUT (3,14%)**, **1 046 / 106 400 FF (0,98%)**, **Fmax ≈ 134,6 MHz**;
  - (B) cả thiết kế `top_arty` ở 125 MHz: **0 DSP48E1**, **2 BRAM tiles**, `WNS = +0,326 ns`, tổng công suất ước tính **0,124 W** (dynamic 0,018 W, static 0,106 W).

## E3 · Raspberry Pi 4

Copy thư mục `experiments/` sang Pi (`scp -r` hoặc `git clone`), rồi chạy:

```bash
cd experiments/e3_soc
./run_bench.sh                        # FIR -O2 (không NEON) và -O3 (GCC tự vector hóa NEON)
sudo apt install rt-tests stress-ng
sudo ./run_cyclictest.sh              # rảnh + có tải; LOOPS=600000 cho số liệu cuối
```

## E5 · Gom kết quả & Cập nhật LaTeX

```bash
python e5_crosscheck/collect.py
```

- Tự động đọc `results/*.json`, sinh `results/E5_crosscheck.md`, `results/numbers.tex` và 3 biểu đồ trong `results/charts/`.
- Thiếu file nào thì dòng đó ghi `chưa có` / `\chuado{}`. Script không bao giờ tự điền số giả định.

## Kết quả đã có tính đến 02/11/2026

- **E0 (Golden model):** Hoàn tất 100% (1024 mẫu, seed 3053, 60 mẫu bão hòa).
- **E1 (MCU STM32F103C6 @ 72 MHz — đo trên board thật):** Hoàn tất 100%. Đã nạp qua ST-Link V2 và đo thực tế bằng `DWT->CYCCNT` & `TIM2`: 4 biến thể FIR đúng 100% (tốt nhất `c_circular_unrolled`: 216,26 chu kỳ/mẫu, 332,93 kS/s); độ trễ ngắt TIM2: 263,89 ns (rảnh), 0–347,22 ns (tải FIR), xấu nhất 21,88 µs (khi có ngắt ưu tiên cao hơn chiếm 20 µs).
- **E2 (FPGA Digilent Arty Z7-20 `xc7z020clg400-1` @ 125 MHz, thuần LUT 0 DSP — mô phỏng, Vivado & đo trên board thật):** Hoàn tất 100%. Đã nạp bitstream và tự kiểm qua JTAG `BSCANE2`: PASS 1024/1024 mẫu, độ trễ 7 chu kỳ (56,0 ns), thông lượng 1,0000 mẫu/chu kỳ (125,00 MSPS); 0/220 DSP48E1, 1 672/53 200 LUT (3,14%), 1 046/106 400 FF (0,98%), Fmax ≈ 134,6 MHz, `WNS = +0,326 ns`, công suất 0,124 W.
- **E3 (SoC):** Đã kiểm chứng code trên laptop x86 (`e3_soc_fir_x86_64_*.json`); chờ đo trên Raspberry Pi 4 khi có board.
- **E5 & Báo cáo LaTeX:** Đã tổng hợp bảng kiểm chứng chéo, biểu đồ và biên dịch `report.pdf`, `slides.pdf`, `slides_hcmut.pdf`.
