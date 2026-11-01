# Nạp và chạy từng board bằng `make`

Mọi lệnh chạy trong thư mục `experiments/`:

```bash
cd CO3053-FPGA-MCU-SoC-Tradeoffs/experiments
make help      # xem toàn bộ lệnh
make ports     # xem cổng serial đang cắm (cắm board rồi chạy để biết cổng)
```

Kết quả của mọi board đều ghi vào `results/`.

## STM32F103 (Blue Pill)

**Nối dây:**
- ST-Link V2: nối SWDIO, SWCLK, GND, 3.3V.
- USB-UART: **PA9 → RX** của adapter, nối chung GND.

```bash
make mcu MCU_PORT=/dev/ttyUSB0     # build + nạp + đọc kết quả
```

Lệnh trên gộp 3 bước. Có thể chạy riêng từng bước:

```bash
make mcu-build                     # chỉ build firmware
make mcu-flash                     # build + nạp qua ST-Link
make mcu-capture MCU_PORT=/dev/ttyUSB0   # đọc kết quả serial -> results/e1_mcu.json
```

- Khi `mcu-capture` báo đang chờ, **nhấn RESET** trên Blue Pill.
- Sau khi in kết quả, board tự chuyển qua các pha đo dòng (RUN 20 s → SLEEP 20 s → STANDBY). Ghi số đo vào `results/e1_mcu_power.json`; file mẫu nằm ở `results/templates/`.

## Arty A7-100T

**Nối dây:** một cáp micro-USB vào cổng PROG/UART. Cáp này vừa nạp qua JTAG vừa dùng làm UART.

```bash
make fpga FPGA_PORT=/dev/ttyUSB1   # Vivado build + nạp + đọc kết quả
```

Lệnh trên gộp 3 bước. Có thể chạy riêng từng bước:

```bash
make fpga-build                    # synth/impl/bitstream + báo cáo (5-10 phút)
make fpga-flash                    # nạp bitstream qua JTAG
make fpga-capture FPGA_PORT=/dev/ttyUSB1  # đọc dòng tự kiểm -> results/e2_fpga_board.json
```

- Arty hiện ra **2 cổng** `ttyUSB`. Cổng UART thường là cổng thứ hai.
- Cần chạy lại phép thử thì **nhấn BTN0**.
- Đèn LED: LD4 = xong, LD5 = PASS, LD6 = FAIL, LD7 = nhịp tim (đang chạy).
- Nạp qua JTAG chỉ lưu vào SRAM, tắt nguồn là mất. Mỗi lần cắm lại board phải chạy `make fpga-flash`.

## Raspberry Pi 4 (qua SSH)

**Chuẩn bị (một lần):**

```bash
ssh-copy-id pi@192.168.1.50                         # đăng nhập không cần mật khẩu
ssh pi@192.168.1.50 'sudo apt install -y rt-tests stress-ng'
```

**Chạy:**

```bash
make pi PI=pi@192.168.1.50         # copy code + benchmark + cyclictest + kéo kết quả về
```

Lệnh trên gộp 4 bước. Có thể chạy riêng từng bước:

```bash
make pi-sync  PI=pi@192.168.1.50   # copy code sang Pi
make pi-bench PI=pi@192.168.1.50   # benchmark FIR (-O2 và -O3)
make pi-cyclictest PI=pi@192.168.1.50 LOOPS=600000   # đo độ trễ, khoảng 2 phút mỗi kịch bản
make pi-fetch PI=pi@192.168.1.50   # kéo results/ từ Pi về máy
```

- `pi-cyclictest` sẽ hỏi mật khẩu `sudo` của Pi.
- `LOOPS=100000` (mặc định) đủ để chạy thử. Với số liệu cuối cùng thì dùng `LOOPS=600000`.

## Không cần board

```bash
make sim       # mô phỏng RTL FIR, tự so với golden
make wave      # mô phỏng + mở GTKWave
make collect   # bảng kiểm chứng chéo + chart -> results/E5_crosscheck.md, results/charts/
make clean     # xóa các thư mục build
```

## Thứ tự gợi ý

```bash
make sim
make mcu  MCU_PORT=/dev/ttyUSB0
make fpga FPGA_PORT=/dev/ttyUSB1
make pi   PI=pi@192.168.1.50
make collect
```
