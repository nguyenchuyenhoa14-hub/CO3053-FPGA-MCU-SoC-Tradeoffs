# CẨM NANG THUYẾT TRÌNH PHẦN THỰC NGHIỆM & DEMO (PRESENTATION GUIDE)
## Đề tài 09: So sánh MCU – SoC – FPGA: Đánh đổi Hiệu năng, Chi phí và Độ linh hoạt
### Dành cho thành viên trình diễn Thực nghiệm / Demo | Thời lượng: 2 – 3 phút

---

## 1. Mục Tiêu Trình Diễn
Trong vòng **120 đến 180 giây**, bạn phải chứng minh cho Giảng viên và cả lớp thấy:
1. **Không phải lý thuyết suông:** Nhóm đã đo đạc trực tiếp trên **phần cứng thật 100%** (STM32F103C6 Blue Pill @ 72 MHz và Digilent Arty Z7-20 @ 125 MHz), cùng chạy thuật toán **FIR 16-tap Q15** và khớp từng mẫu với Golden Model.
2. **Số liệu định lượng đanh thép:** 
   - **Thông lượng:** FPGA đạt **125,00 MSPS**, nhanh gấp **375×** so với bản tối ưu nhất của MCU (**0,33 MSPS**) và gấp **763×** bản C cơ bản.
   - **Độ trễ xử lý:** FPGA phản hồi trong **56,0 ns** (7 chu kỳ pipeline), nhanh hơn **53,6×** so với MCU (**3 003,7 ns**).
   - **Độ tiền định (Jitter):** FPGA có jitter = **0 ns**; trong khi MCU có jitter 0–347 ns khi chạy tải, và vọt lên **21,88 µs** khi có ngắt ưu tiên cao chen ngang.
3. **Hiểu sâu về kiến trúc:** 
   - Lõi ARM Cortex-M3 không có tập lệnh SIMD (`SMLAD`), khiến MCU chỉ đạt 7% mức lý thuyết "1 MAC/chu kỳ".
   - FPGA chạy ở chế độ **thuần LUT (0 DSP48E1)**, chỉ chiếm 3,14% LUT của chip Zynq-7020 nhưng vẫn duy trì đúng **1 mẫu/chu kỳ** ở 125 MHz.

---

## 2. Các Kịch Bản Thao Tác Trình Diễn (Live Action)

### Kịch bản 1: Trình diễn Báo cáo & Số liệu Đo thật trên Board (Ưu tiên số 1 - Khớp với Slide & Report)
- Sử dụng trực tiếp các slide 6–9 trong `report/slides_hcmut.pdf` (hoặc `slides.pdf`):
  - **Slide 6:** Phương pháp thực nghiệm E0–E5 (1 024 mẫu, seed 3053, 60 mẫu bão hòa, khớp 100% golden).
  - **Slide 7:** Biểu đồ thông lượng (`e5_throughput.png`) — FPGA 125 MSPS vs MCU 0,33 MSPS (gấp 375×).
  - **Slide 8:** Biểu đồ độ trễ xấu nhất (`e5_worst_latency.png`) — FPGA 56 ns vs MCU 264 ns (rảnh) / 21,88 µs (ngắt lồng nhau).
  - **Slide 9:** Bảng kiểm chứng chéo với tài liệu (cận trên lý thuyết 1 MAC/chu kỳ vs thực tế 7%).
- Nếu có board cắm trực tiếp trên lớp:
  - Nạp STM32 và đọc SRAM qua SWD: `make -C experiments mcu` (kết quả in ra trong 9s).
  - Tự kiểm Arty Z7-20 qua JTAG: `make -C experiments fpga-flash` (in ra `PASS N=0400 ERR=0000 LAT=0007`).

### Kịch bản 2: Minh họa Dạng sóng Mô phỏng trên GTKWave (Minh họa trực quan xung nhịp)
1. **Trước khi bắt đầu:**
   - Mở sẵn PowerShell tại thư mục `experiments/e2_fpga` hoặc `demo/`.
   - Mở GTKWave xem file sóng VCD `demo/outputs/fir_simulation.vcd`.
2. **Thao tác nhanh:**
   - Chạy `python demo/run_demo.py` để biểu diễn quy trình kiểm thử tự động.
   - Chỉ vào tín hiệu trên GTKWave: `clk`, `data_in`, `valid_out`, `data_out` để minh họa rõ nét khái niệm "đường ống 1 mẫu/chu kỳ không ngắt quãng".

---

## 3. Lời Thoại Thuyết Trình Mẫu (Verbatim Speech)

> *(Thời lượng: ~2 phút | Phong thái: Tự tin, đĩnh đạc, bám sát số liệu có nhãn [đo])*
>
> "Kính thưa Thầy và các bạn, để trả lời câu hỏi khi nào nên chọn MCU, SoC hay FPGA một cách thuyết phục nhất, nhóm không chỉ dựa vào lý thuyết mà đã **trực tiếp đo đạc thực nghiệm trên phần cứng thật**:
> - Nhóm sử dụng cùng một bài toán chuẩn: **Bộ lọc số FIR 16-tap Q15** với bộ vector 1 024 mẫu thử thách, đối chiếu từng mẫu với Golden Model viết bằng Python.
>
> **Kết quả đo đạc mang lại ba phát hiện kỹ thuật quan trọng:**
>
> 1. **Về Thông lượng:** 
>    - Trên vi điều khiển **STM32F103 (Cortex-M3 @ 72 MHz)**, nhóm thử nghiệm 4 thuật toán. Bản tối ưu nhất dùng bộ đệm vòng khai triển đạt **0,33 MSPS** (216 chu kỳ/mẫu). Do Cortex-M3 không có tập lệnh SIMD DSP, MCU chỉ đạt khoảng 7% so với giả thiết lý thuyết '1 MAC/chu kỳ'.
>    - Trong khi đó, trên **FPGA Digilent Arty Z7-20 @ 125 MHz**, dù nhóm cấu hình ở chế độ **thuần Soft-Logic (0 khối DSP, dùng 1 672 LUT)**, mạch pipeline 7 tầng vẫn xuất ra đều đặn **1 mẫu/chu kỳ**, đạt thông lượng **125 MSPS** — **nhanh gấp 375 lần MCU**.
>
> 2. **Về Độ trễ và Độ tiền định:**
>    - FPGA xử lý mẫu chỉ mất **56 nano-giây**, với jitter bằng **đúng 0 ns**.
>    - Ngược lại, độ trễ ngắt của MCU dao động từ 264 ns lúc rảnh đến 347 ns khi chạy tải, và khi có ngắt ưu tiên cao hơn chen ngang 20 µs, độ trễ xấu nhất vọt lên tới **21,88 micro-giây**. Điều này chứng minh: *Worst-case latency của MCU do kiến trúc phần mềm quyết định, không phải chỉ do phần cứng*.
>
> 3. **Về Năng lượng:**
>    - FPGA tiêu tốn khoảng **0,99 nano-Joule cho mỗi mẫu**. Nhưng khi hệ thống cần ngủ dài chờ sự kiện, MCU lại vượt trội với dòng Standby chỉ vài micro-ampe.
>
> Tóm lại, không có nền tảng nào toàn năng: FPGA vượt trội về thông lượng song song và độ trễ cố định cỡ nano-giây, còn MCU vô địch về chi phí và tiết kiệm năng lượng ở chế độ nghỉ."

---

## 4. Bốn Câu Hỏi Phản Biện Trọng Tâm & Cách Trả Lời Chuẩn Barem

### Câu hỏi 1: "Tại sao nhóm đo trên STM32F103 mà không phải STM32F4/F7 có tập lệnh DSP?"
**Trả lời:**
> "Dạ thưa Thầy, STM32F103 lõi Cortex-M3 đại diện cho phân khúc vi điều khiển 32-bit phổ thông giá rẻ (dưới 2 USD). Phép đo trên M3 giúp bộc lộ rõ giới hạn của kiến trúc nạp-nhân-lưu tuần tự khi không có SIMD (đạt 216 chu kỳ/mẫu). Nếu nâng lên Cortex-M4/M7 có tập lệnh `SMLAD` (nhân-cộng kép 1 chu kỳ), số chu kỳ sẽ giảm khoảng 3–4× (xuống ~36–50 chu kỳ/mẫu), nhưng vẫn chậm hơn FPGA hàng chục đến hàng trăm lần vì FPGA tính toán song song không gian toàn bộ 16 tap cùng lúc."

### Câu hỏi 2: "Tại sao thiết kế FPGA lại chạy chế độ thuần LUT (0 DSP) thay vì dùng khối DSP48E1?"
**Trả lời:**
> "Dạ thưa Thầy, đây là một thử nghiệm có chủ ý của nhóm:
> - Trên chip Zynq XC7Z020 có sẵn 220 khối DSP48E1. Nhóm chủ động gán thuộc tính `(* use_dsp = "no" *)` và tổng hợp với cờ `-max_dsp 0` để kiểm tra năng lực của mạng logic LUT.
> - Kết quả cho thấy: chỉ cần **1 672 Slice LUTs (3,14%)** và **1 046 Flip-Flops (0,98%)**, FPGA đã có thể tự dựng toàn bộ 16 bộ nhân Q15 và cây cộng nhị phân 4 tầng đạt tần số $F_{\max} \approx 134,6\text{ MHz}$ và đóng timing `WNS = +0,326 ns` ở 125 MHz.
> - Điều này chứng minh FPGA cực kỳ linh hoạt: ngay cả khi tài nguyên DSP bị chiếm hết cho tác vụ khác, ta vẫn có thể dùng tài nguyên logic thường để xử lý tín hiệu tốc độ cao."

### Câu hỏi 3: "Jitter của FPGA bằng 0 thật không, hay chỉ là lý thuyết?"
**Trả lời:**
> "Dạ thưa Thầy:
> - Về mặt logic chu kỳ (Cycle-accurate), độ trễ đường ống của FPGA là tiền định tuyệt đối: đúng 7 chu kỳ xung nhịp từ `in_valid` đến `out_valid`, không có bất kỳ trạng thái chờ hay tranh chấp bộ nhớ nào, nên Jitter chu kỳ bằng đúng 0 chu kỳ.
> - Ở mức vật lý tín hiệu, chỉ có độ rung pha (Phase Jitter) của bộ tạo xung nhịp thạch anh trên board (cỡ vài chục pico-giây), hoàn toàn không đáng kể so với mức nano-giây hoặc micro-giây của MCU và SoC."

### Câu hỏi 4: "Nếu tăng bộ lọc từ 16-tap lên 64-tap, kết quả so sánh sẽ thay đổi thế nào?"
**Trả lời:**
> "Dạ thưa Thầy:
> - **Trên MCU:** Số phép tính tăng gấp 4 lần $\rightarrow$ thời gian xử lý tăng tuyến tính gấp 4 lần (~860 chu kỳ/mẫu), thông lượng tụt xuống chỉ còn ~0,08 MSPS (khoảng 80 kS/s).
> - **Trên FPGA:** Ta mở rộng thêm 48 bộ nhân và thêm 2 tầng pipeline ($64 \rightarrow 32 \rightarrow 16 \rightarrow 8 \rightarrow 4 \rightarrow 2 \rightarrow 1$). Độ trễ đường ống tăng từ 7 chu kỳ lên 9 chu kỳ (72 ns), nhưng **thông lượng vẫn giữ nguyên tuyệt đối: 1 mẫu / chu kỳ xung nhịp = 125,00 MSPS**!
> - Khi đó tỉ lệ cách biệt thông lượng giữa FPGA và MCU sẽ tăng từ **375× lên tới hơn 1 500×**!"
