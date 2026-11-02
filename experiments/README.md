# Thí nghiệm của nhóm (E0–E5)

Bộ thí nghiệm viết lại theo [PLAN_v2.md](../PLAN_v2.md). Thư mục `demo/` cũ chỉ còn để tham khảo, không lấy số từ đó.

Bài toán chung là **FIR 16-tap Q15**: cùng hệ số, cùng 1024 mẫu vào, và mọi nền tảng phải khớp từng mẫu với golden model. Mỗi con số trong `results/` mang một nhãn: `do`, `mo phong`, `uoc luong cong cu`, `tinh` hoặc `nguon`.

| Bước | Nội dung | Chạy ở đâu | Đầu ra |
| --- | --- | --- | --- |
| E0 | Golden model, hệ số, vector | máy nào cũng được | `common/fir/fir_vectors.h`, `e2_fpga/mem/*.hex`, `results/e0_spec.json` |
| E1 | STM32F103: 4 phiên bản FIR, độ trễ ngắt, các pha đo dòng | Blue Pill + ST-Link + USB-UART | `results/e1_mcu.json` |
| E2 | Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz): mô phỏng RTL, Vivado, tự kiểm trên board | PC có Vivado + Arty Z7-20 | `results/e2_fpga_{sim,impl,board}.json` |
| E3 | Raspberry Pi 4: thông lượng FIR, `cyclictest` | Pi 4 | `results/e3_*.json` |
| E5 | Bảng kiểm chứng chéo với PLAN.md + chart | máy nào cũng được | `results/E5_crosscheck.md`, `results/charts/` |

## Chạy nhanh bằng Makefile

```bash
make ports                              # xem cổng serial đang cắm
make mcu  MCU_PORT=/dev/ttyUSB0         # STM32: build, nạp ST-Link, đọc kết quả
make fpga                               # Arty Z7-20: Vivado build, nạp JTAG, tự đọc kết quả
make pi   PI=pi@192.168.1.50            # Pi 4 qua SSH: copy code, chạy benchmark + cyclictest, kéo kết quả về
make collect                            # bảng kiểm chứng chéo + chart
```

`make help` liệt kê từng bước riêng (`mcu-flash`, `fpga-build`, `pi-bench`…). Các phần dưới đây mô tả chi tiết từng thí nghiệm.

## E0 · Golden model (đã chạy)

```bash
python3 e0_golden/gen_vectors.py
```

- Hệ số: low-pass windowed-sinc (Hamming), fc = 0,2·fs, tổng = 2^15 (khuếch đại DC = 1).
- Vector gồm xung đơn vị, bậc thang, giá trị biên, mẫu đối kháng (ép bão hòa: 60 mẫu ra) và ngẫu nhiên (seed 3053).
- Có sửa hệ số thì chạy lại E0 trước mọi bước khác.

## E1 · MCU STM32F103 (Blue Pill)

**Nối dây:**
- ST-Link V2 nối SWDIO, SWCLK, GND, 3.3V.
- USB-UART nối **PA9 (TX) → RX của adapter** và GND.

```bash
cd e1_mcu
pio run -t upload                                   # build + nạp qua ST-Link
python ../tools/capture_serial.py mcu /dev/ttyUSB0  # rồi nhấn RESET trên Blue Pill
```

Python cần có `pyserial`; venv của PlatformIO đã có sẵn.

**Firmware đo những gì** (khoảng 10 giây, sau đó in JSON):
- **Thông lượng** của 4 phiên bản: C dịch đường trễ, C bộ đệm vòng khai triển, CMSIS `arm_fir_q15`, CMSIS `arm_fir_fast_q15`.
  - Mỗi phiên bản được kiểm tra với golden và đếm chu kỳ bằng `DWT->CYCCNT` khi đã tắt ngắt; lấy median của 7 lần chạy.
  - Cortex-M3 **không có SIMD** (SMLAD), nên CMSIS-DSP không được tăng tốc kiểu SIMD như trên M4/M7. Đây là điểm nên nói khi thuyết trình.
- **Độ trễ ngắt** với TIM2 ở 10 kHz, 20 000 mẫu cho mỗi kịch bản:
  - CPU rảnh;
  - CPU đang chạy FIR;
  - CPU chạy FIR và có thêm một ngắt TIM3 **ưu tiên cao hơn**, mỗi lần chạy 20 µs.

  Kịch bản thứ ba cho thấy worst-case của MCU do thiết kế phần mềm quyết định.
- **Các pha đo dòng**, chạy sau khi in JSON. Dùng đồng hồ vạn năng, ghi vào `results/e1_mcu_power.json` (mẫu ở `results/templates/`):
  1. `RUN_FIR` 20 s: CPU chạy FIR liên tục, LED PC13 sáng;
  2. `SLEEP` 20 s: WFI, SysTick đánh thức mỗi 1 ms;
  3. `STANDBY`: giữ cho đến khi nhấn RESET.

  Lưu ý khi đo:
  - Đo dòng của **chip** ở chân 3.3V và gỡ LED nguồn. Nếu đo cả board, phải ghi rõ trong trường `where`.
  - **Rút ST-Link** khi đo STANDBY, vì debug giữ một phần mạch luôn được cấp nguồn.

**Nếu board không phải Blue Pill:** đổi `board` trong `platformio.ini`. Clock tự rơi về HSI 64 MHz nếu không có thạch anh HSE, và JSON ghi lại nguồn clock thực tế. Nếu chip clone không có DWT, firmware tự chuyển sang SysTick và ghi điều đó vào JSON.

## E2 · FPGA Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz)

```bash
cd e2_fpga
./run_sim.sh            # Icarus: 2 lượt (liên tục + có khoảng trống), tự so golden -> results/e2_fpga_sim.json
./run_sim.sh vcd        # thêm build/fir16.vcd cho GTKWave
vivado -mode batch -source vivado/build.tcl    # khoảng 3-5 phút -> results/e2_fpga_impl.json + bitstream
vivado -mode batch -source vivado/program.tcl  # nạp vào board + tự đọc kết quả qua JTAG -> results/e2_fpga_board.json
python ../tools/capture_serial.py fpga /dev/ttyUSB1   # (tùy chọn) đọc qua USB-UART rời nối vào Pmod JA[0] (Y18)
```

- **RTL** ([rtl/fir16.v](e2_fpga/rtl/fir16.v)): pipeline 7 tầng, 1 mẫu/chu kỳ, có bão hòa giống golden.
- **Tự kiểm trên board** ([rtl/top_arty.v](e2_fpga/rtl/top_arty.v)):
  - Chạy trực tiếp trên vùng logic khả trình **Artix-7 PL** của chip Zynq-7020 (`xc7z020clg400-1`, 220 khối DSP48E1, 53 200 LUT) ở xung nhịp gốc **125 MHz** (chân `H16`, chu kỳ 8 ns).
  - Đọc 1024 mẫu từ BRAM ở 125 MHz (thông lượng 125 MSPS, độ trễ 7 chu kỳ = 56 ns), so từng mẫu với golden ngay trên chip, đếm chu kỳ.
  - Xuất kết quả đồng thời qua JTAG `USER4` (`BSCANE2`, tự động đọc bởi `vivado/program.tcl`) và qua UART 115200 8N1 tại chân **Pmod `JA[0]` (`Y18`)**, ví dụ: `FIR16 PASS N=0400 ERR=0000 LAT=0007 CYC=00000407 FBAD=FFFF`.
  - LED trên Arty Z7-20: **LD0** (`R14`) = xong, **LD1** (`P14`) = PASS, **LD2** (`N16`) = FAIL, **LD3** (`M14`) = nhịp tim. Nút nhấn: **BTN0** (`D19`) = chạy lại, **BTN1** (`D20`) = reset.
  - Testbench [tb/tb_top_arty.v](e2_fpga/tb/tb_top_arty.v) đã kiểm tra toàn bộ quy trình tự chạy sau POR và chạy lại khi nhấn `BTN0`.
- **Vivado** chạy 2 phần:
  - (A) chỉ khối FIR, out-of-context, ép clock 400 MHz (`2,5 ns`) → **Fmax ước tính** và số DSP48E1 (trên 220);
  - (B) cả thiết kế ở 125 MHz (`8,0 ns`) → bitstream `top_arty.bit` và **công suất ước tính** (`report_power` vector-less).

  Cả hai đều mang nhãn `uoc luong cong cu`, không phải số đo.

## E3 · Raspberry Pi 4

Copy thư mục `experiments/` sang Pi (`scp -r` hoặc `git clone`), rồi chạy:

```bash
cd experiments/e3_soc
./run_bench.sh                        # FIR -O2 (không NEON) và -O3 (GCC tự vector hóa NEON)
sudo apt install rt-tests stress-ng
sudo ./run_cyclictest.sh              # rảnh + có tải; LOOPS=600000 cho số liệu cuối (khoảng 2 phút mỗi kịch bản)
```

- Để giảm nhiễu khi chạy: dùng tản nhiệt hoặc quạt; `vcgencmd get_throttled` phải trả về `0x0` (script ghi vào `results/e3_sysinfo_*.txt`). Nếu được, đặt governor là `performance`.
- **Kernel PREEMPT_RT (tùy chọn):** nếu cài được kernel RT trên Pi, chạy lại `run_cyclictest.sh`. File kết quả sẽ có hậu tố `_rt_`.
- **Công suất:** đo cả board bằng USB-C power meter khi rảnh và khi đang chạy `run_bench.sh`, rồi ghi vào `results/e3_pi_power.json`.

Các file `e3_soc_fir_x86_64_*.json` là kết quả chạy thử trên laptop. Chúng chỉ dùng để kiểm tra code, không phải số liệu SoC, và E5 bỏ qua chúng trừ khi chạy với `--x86`.

## E5 · Gom kết quả

```bash
/usr/bin/python3 e5_crosscheck/collect.py     # cần matplotlib
```

- Sinh `results/E5_crosscheck.md` gồm các bảng thông lượng, độ trễ xấu nhất, năng lượng mỗi mẫu và **bảng kiểm chứng chéo với PLAN.md** (27× của Arucu & Iliev, 30–80 µs và "vài ms" của AC6, giả thiết 1 MAC/chu kỳ…).
- Sinh chart trong `results/charts/`.
- Thiếu file nào thì dòng đó ghi "chưa có". Script không bao giờ tự điền số.

## Kết quả đã có tính đến 02/11/2026

- **E0:** xong.
- **E2 mô phỏng & Vivado (`xc7z020clg400-1` @ 125 MHz):** PASS 1024/1024 ở cả hai lượt; độ trễ 7 chu kỳ (56 ns ở 125 MHz); 1,0000 mẫu/chu kỳ (125 MSPS ở 125 MHz); đã tổng hợp và sinh bitstream `top_arty.bit` cùng báo cáo Fmax, DSP48E1 và công suất từ Vivado.
- **E3:** code đã chạy đúng trên laptop x86, chưa chạy trên Pi.
- **Chưa có:** E1 (board), nạp board cho E2, E3 trên Pi, số đo công suất.
