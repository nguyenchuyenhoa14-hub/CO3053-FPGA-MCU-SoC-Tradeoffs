# CẨM NANG THUYẾT TRÌNH PHẦN DEMO MÔ PHỎNG (DEMO PRESENTATION GUIDE)
## Đề tài 9: FPGA vs. MCU vs. SoC — Đánh đổi Hiệu năng, Chi phí, Độ linh hoạt
### Dành cho thành viên trình diễn Demo (Presenter 3) | Thời lượng: 1.5 – 2.0 phút (Slide 18)

---

## 1. Mục Tiêu Trình Diễn
Trong vòng **90 đến 120 giây**, bạn phải chứng minh cho Thầy H.A và cả lớp thấy:
1. **Không phải lý thuyết suông:** Nhóm đã hiện thực cả mã C trên ARM và mã phần cứng Verilog HDL trên FPGA, chạy đo đạc thực chứng.
2. **Hiển thị trực quan:** Chỉ rõ dạng sóng xung nhịp vật lý (Clock cycle) và pipeline tuôn dữ liệu ra liên tục.
3. **Số liệu định lượng đanh thép:** FPGA đạt thông lượng cao hơn **gấp 21.4 lần** Cortex-M4 và **gấp 7.5 lần** Cortex-M7 dù xung nhịp hoạt động thấp hơn nhiều.

---

## 2. Kịch Bản Thao Tác Chi Tiết (Step-by-Step Live Action)

### Tình huống A: Trình diễn Live trên Terminal & GTKWave (Khuyến nghị để đạt 10/10)
1. **Trước khi bắt đầu buổi thuyết trình:**
   - Mở sẵn cửa sổ PowerShell tại thư mục `n:\nhung_present\demo\`.
   - Mở sẵn phần mềm **GTKWave** load sẵn file `demo\outputs\fir_simulation.vcd`.
2. **Khi Slide 18 xuất hiện trên màn chiếu:**
   - Diễn giả 3 bước lên, nói câu mở đầu (xem mục 3 bên dưới).
   - Alt-Tab sang cửa sổ Terminal gõ lệnh:
     ```powershell
     python run_demo.py
     ```
   - Terminal chạy vùn vụt qua 4 bước trong vòng 3 giây và in ra bảng số liệu xanh đẹp mắt.
   - Alt-Tab sang GTKWave: Chỉ tay vào các đường tín hiệu:
     - `clk`: Xung nhịp 100 MHz.
     - `data_in`: Mẫu đầu vào bơm liên tục.
     - `valid_out` & `data_out`: Tín hiệu ngõ ra xuất hiện đều đặn **1 chu kỳ / mẫu** mà không có bất kỳ khoảng trống trễ nào!

### Tình huống B: Trình chiếu an toàn trên Slide (Safe Mode)
Nếu không tiện chuyển đổi cửa sổ, Slide 18 đã chèn sẵn:
- Ảnh chụp 4 biểu đồ sắc nét từ thư mục `demo/outputs/charts/`:
  - `chart1_throughput_comparison.png` (Cột thông lượng 100 MSPS vs 4.66 MSPS).
  - `chart2_latency_and_jitter.png` (So sánh độ trễ & zero jitter).
- Diễn giả chỉ cần dùng bút laser chỉ vào biểu đồ và đọc lưu loát kịch bản.

---

## 3. Lời Thoại Thuyết Trình Khớp Từng Giây (Verbatim Speech)

> *(Thời lượng: 90 giây | Phong thái: Tự tin, giọng đĩnh đạc, mắt hướng về Thầy H.A)*
>
> "Kính thưa Thầy và các bạn, để kiểm chứng cho toàn bộ những luận điểm kiến trúc mà nhóm đã phân tích, nhóm chúng em đã hiện thực một thử nghiệm đối sánh kinh điển: **Thuật toán bộ lọc số FIR 16-Tap dạng điểm cố định Q15**.
>
> Nhóm đã tiến hành đo đạc trên cả hai nền tảng:
> - **Thứ nhất, trên vi điều khiển ARM Cortex-M:** Thuật toán được lập trình bằng C tối ưu với vòng lặp khai triển unrolled. Do cơ chế nạp chỉ lệnh và chia sẻ ALU tuần tự, mỗi mẫu tín hiệu tiêu tốn trung bình **36 chu kỳ xung nhịp**. Ở xung nhịp 168 MHz của chip STM32F4, thông lượng tối đa đạt **4.66 triệu mẫu/giây**.
> - **Thứ hai, trên FPGA Artix-7:** Nhóm đã thiết kế kiến trúc phần cứng **Pipelined Systolic FIR** bằng Verilog HDL với 16 khối nhân DSP chạy song song kết hợp cây cộng dồn 4 tầng. 
>
> *(Chỉ tay vào Slide / Màn hình GTKWave)*
> Kết quả mô phỏng chu kỳ chính xác cho thấy: Sau 5 chu kỳ khởi động đường ống ban đầu, mạch phần cứng xuất ra **đúng 1 mẫu kết quả trên mỗi chu kỳ xung nhịp clock**! Ở xung nhịp chỉ 100 MHz, thông lượng đạt **100 triệu mẫu/giây**, nhanh hơn **gấp 21.4 lần** so với Cortex-M4, với độ dao động ngắt Jitter bằng **đúng 0.00 nano-giây**!
>
> Đồng thời, mô phỏng trên Heterogeneous SoC Zynq cho thấy: Với các gói dữ liệu từ 1.024 mẫu trở lên, việc đẩy dữ liệu qua kênh DMA AXI-Stream sang FPGA giúp tăng tốc hệ thống và **giải phóng hơn 96% tải CPU**, cho phép CPU rảnh tay chạy hệ điều hành Linux.
>
> Đây chính là minh chứng sống động khẳng định sức mạnh vượt trội của tính toán không gian song song!"

---

## 4. Ba Câu Hỏi Bẫy Thầy Cô Hay Hỏi Nhất Về Phần Demo & Cách Trả Lời

### Câu hỏi 1: "Tại sao nhóm em chọn xung nhịp FPGA là 100 MHz mà không phải 500 MHz như MCU?"
**Trả lời:**
> "Dạ thưa Thầy, tần số xung nhịp 100 MHz đến 200 MHz là tần số hoạt động tiêu chuẩn và an toàn của các dòng FPGA tầm trung như Xilinx Artix-7 hoặc Spartan-7. Việc nhóm chọn 100 MHz (chu kỳ 10ns) là để đảm bảo thỏa mãn hoàn toàn ràng buộc về thời gian thiết lập và thời gian giữ (Timing Closure: Setup/Hold Slack đều dương) sau khi đi qua cây cộng dồn 4 tầng. Và điểm mấu chốt nhóm muốn chứng minh là: **Dù chạy ở xung nhịp thấp hơn 40%, FPGA vẫn nhanh hơn vi điều khiển hơn 20 lần nhờ tính song song phần cứng**."

### Câu hỏi 2: "Tại sao độ trễ khởi động của bộ lọc FPGA trong mô phỏng là 5 chu kỳ xung nhịp?"
**Trả lời:**
> "Dạ thưa Thầy, độ trễ 5 chu kỳ (50 ns) này chính là độ sâu của đường ống (Pipeline Depth):
> - Chu kỳ 1: Nạp mẫu vào thanh ghi trễ và thực hiện 16 phép nhân DSP song song.
> - Chu kỳ 2: Tầng 1 của cây cộng (cộng 16 kết quả thành 8).
> - Chu kỳ 3: Tầng 2 của cây cộng (cộng 8 kết quả thành 4).
> - Chu kỳ 4: Tầng 3 của cây cộng (cộng 4 kết quả thành 2).
> - Chu kỳ 5: Tầng 4 của cây cộng (cộng 2 kết quả thành tổng cuối cùng) và xuất ra `data_out`.
> Sau 5 chu kỳ khởi động này, đường ống được lấp đầy và từ đó trở đi, mỗi chu kỳ đều xuất ra 1 mẫu mới liên tục (Throughput = 1 sample/cycle)."

### Câu hỏi 3: "Nếu muốn mở rộng bộ lọc từ 16-tap lên 64-tap, kiến trúc FPGA này sẽ thay đổi thế nào so với MCU?"
**Trả lời:**
> "Dạ thưa Thầy:
> - **Trên MCU:** Số phép tính tăng gấp 4 lần $\rightarrow$ thời gian xử lý tăng tuyến tính gấp 4 lần (mất ~144 chu kỳ CPU/mẫu), thông lượng tụt giảm nghiêm trọng chỉ còn ~1.1 MSPS.
> - **Trên FPGA:** Ta chỉ cần cấp phát thêm 48 khối DSP Slices và tăng độ sâu cây cộng thêm 2 tầng pipeline ($64 \rightarrow 32 \rightarrow 16 \rightarrow 8 \rightarrow 4 \rightarrow 2 \rightarrow 1$). Độ trễ khởi động tăng lên 7 chu kỳ, nhưng **thông lượng vẫn giữ nguyên tuyệt đối: 1 mẫu / chu kỳ xung nhịp (100 MSPS)**! Đây chính là khả năng mở rộng quy mô (Scalability) vô địch của FPGA."
