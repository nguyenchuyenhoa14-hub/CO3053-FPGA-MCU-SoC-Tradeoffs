# Nạp và chạy từng board bằng `make`

Mọi lệnh chạy trong thư mục `experiments/`:

```bash
cd CO3053-FPGA-MCU-SoC-Tradeoffs/experiments
make help      # xem toàn bộ lệnh
make ports     # xem cổng serial đang cắm (cắm board rồi chạy để biết cổng)
```

Kết quả của mọi board đều ghi vào `results/`.

## STM32F103 (Blue Pill — `STM32F103C6` / `STM32F103C8`)

**Nối dây:**
- ST-Link V2: nối 4 dây `SWDIO`, `SWCLK`, `GND`, `3.3V` vào header SWD của Blue Pill.
- **Cách 1 (Khuyên dùng — không cần USB-UART rời):** Đọc kết quả trực tiếp từ SRAM qua ST-Link SWD:

```bash
make mcu                           # build + nạp ST-Link + tự đọc SRAM qua SWD -> results/e1_mcu.json
```

- **Cách 2 (Dùng USB-UART rời nối vào `PA9`):** Nối thêm `PA9 (TX) → RX` của adapter và `GND`:

```bash
make mcu MCU_PORT=/dev/ttyUSB0     # build + nạp + đọc kết quả qua cổng serial
```

Có thể chạy riêng từng bước:

```bash
make mcu-build                     # chỉ build firmware (mặc định env:f103c6)
make mcu-flash                     # build + nạp qua ST-Link
make mcu-capture                   # tự reset và đọc SRAM qua SWD -> results/e1_mcu.json
```

- Sau khi chạy xong 4 biến thể FIR và 3 kịch bản đo độ trễ ngắt (~9 giây), board tự chuyển qua các pha đo dòng (`RUN 20 s` → `SLEEP 20 s` → `STANDBY`). Ghi số đo vào `results/e1_mcu_power.json`; file mẫu nằm ở `results/templates/`.

## Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz, thuần LUT / 0 DSP)

**Nối dây:** cắm một cáp micro-USB vào cổng **PROG/UART (J14)** và bật công tắc nguồn (chọn nguồn USB hoặc jack ngoài).
- Bitstream tổng hợp ở chế độ **thuần Soft-Logic (`(* use_dsp = "no" *)`, `-max_dsp 0` $\rightarrow$ 0 khối DSP48E1, 1 672 LUT, 1 046 FF)**, chạy trực tiếp trên vùng logic khả trình **Artix-7 PL** ở xung nhịp gốc **125 MHz** (chân `H16`, chu kỳ 8 ns $\rightarrow$ thông lượng 125 MSPS, độ trễ 7 chu kỳ = 56 ns).
- Kết quả tự kiểm (`PASS`, `ERR`, `LAT`, `CYC`) được đọc **tự động qua chính cáp USB-JTAG** ngay trong `vivado/program.tcl` (thông qua khối `BSCANE2 USER4`), đồng thời cũng phát ra UART 115200 8N1 tại chân **Pmod `JA[0]` (chân 1 của cổng JA, pin `Y18`)**.

```bash
make fpga                          # Vivado build (0 DSP) + nạp JTAG + tự đọc kết quả -> results/e2_fpga_board.json
```

Có thể chạy riêng từng bước:

```bash
make fpga-build                    # synth/impl/bitstream + báo cáo (3-5 phút) -> results/e2_fpga_impl.json
make fpga-flash                    # nạp bitstream qua JTAG + tự động đọc kết quả về results/e2_fpga_board.json
make fpga-capture FPGA_PORT=/dev/ttyUSB1  # (tùy chọn) đọc qua USB-UART rời nối vào Pmod JA[0] (Y18)
```

- Cần chạy lại phép thử trên board: **nhấn BTN0** (chân `D19`) để chạy lại, hoặc **nhấn BTN1** (chân `D20`) để reset.
- Đèn LED trên Arty Z7-20: **LD0** (`R14`) = xong, **LD1** (`P14`) = PASS, **LD2** (`N16`) = FAIL, **LD3** (`M14`) = nhịp tim (đang chạy).
- Nạp qua JTAG lưu vào SRAM, tắt nguồn là mất. Mỗi lần bật lại board chạy `make fpga-flash`.

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
make mcu
make fpga
make pi   PI=pi@192.168.1.50
make collect
```
