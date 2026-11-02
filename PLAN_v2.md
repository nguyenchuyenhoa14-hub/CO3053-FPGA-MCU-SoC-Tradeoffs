# Kế hoạch thực hiện v2: MCU – SoC – FPGA

Nov 1, 2026 · thay thế phần demo cũ trong `README.md` và `demo/`

## 1. Quyết định chính

- **Nội dung:** lấy `PLAN.md` làm xương sống (nguồn, 6 ứng dụng, ma trận quyết định, hạn chế). Không viết lại phần này.
- **Demo:** làm lại từ đầu. Code trong `demo/` chỉ để tham khảo ý tưởng. Mọi số trong code cũ (36 chu kỳ/mẫu, 0,25 W, 1,2 W, NRE 5K/80K, ASIC, N≈48) **không được dùng** khi chưa đo hoặc chưa có nguồn.
- **Định nghĩa nền tảng:** theo `PLAN.md`.
  - MCU = Cortex-M bare-metal/RTOS.
  - SoC = Cortex-A chạy Linux.
  - FPGA = Artix-7.
  - Zynq = phương án lai, không gọi là "SoC".
- **Mục tiêu của demo:** kiểm chứng chéo các con số lấy từ tài liệu trong `PLAN.md` (theo `pe3`). Demo không nhằm chứng minh FPGA thắng (theo `pe2`).

## 2. Nguyên tắc số liệu

Mỗi con số trên slide, chart và lời thoại phải mang đúng một nhãn:

| Nhãn | Ý nghĩa | Ví dụ |
| --- | --- | --- |
| **đo** | Nhóm tự đo trên phần cứng thật | Số chu kỳ bằng DWT->CYCCNT trên STM32 |
| **mô phỏng** | Kết quả từ simulator (iverilog, Renode…) | Độ trễ pipeline 5 chu kỳ trong RTL |
| **ước lượng công cụ** | Báo cáo của Vivado hoặc Yosys | Fmax, số DSP, công suất từ Power Report |
| **tính** | Nhóm tự tính từ số đã có, kèm giả thiết | 1 MAC/chu kỳ × 480 MHz |
| **nguồn** | Lấy từ tài liệu, có link | CoreMark của ST |

Quy tắc cụ thể:
- Không có nhãn thì không đưa lên.
- Chart chỉ đọc số từ file JSON do thí nghiệm sinh ra, không gõ số thẳng vào code vẽ.
- Không dùng các từ "vượt trội", "vô địch", "0.00 ns tuyệt đối".

## 3. Thí nghiệm mới

Bài toán chung: **FIR 16-tap Q15**, cùng hệ số, cùng bộ vector đầu vào cho mọi nền tảng.

### E0. Mô hình chuẩn (golden model)
- Viết bằng Python/numpy: sinh vector bậc thang, xung đơn vị, ngẫu nhiên và giá trị biên (±32767, để thử tràn số).
- Xuất `vectors_in.txt` và `golden_out.txt`. Mọi nền tảng phải khớp file này, có script tự so sánh.

### E1. MCU (ưu tiên cao nhất)
- **Nếu có board STM32 (F4/H7/Nucleo bất kỳ):**
  - Chạy 3 phiên bản: C thường, C unroll, CMSIS-DSP `arm_fir_q15`.
  - Đo số chu kỳ bằng DWT->CYCCNT (nhãn **đo**).
  - Tùy chọn: đo dòng bằng đồng hồ vạn năng hoặc INA219 khi chạy và khi Standby (nhãn **đo**).
- **Nếu không có board:**
  - Biên dịch bằng `arm-none-eabi-gcc -O3 -mcpu=cortex-m4`, đếm lệnh trong vòng lặp (nhãn **tính**).
  - Hoặc chạy trên Renode để kiểm tra kết quả đúng (nhãn **mô phỏng**, không lấy số chu kỳ).
- **Đầu ra:** chu kỳ/mẫu, MSPS, so với mức lý thuyết ≈0,48 G MAC/s của H743 trong `PLAN.md`.

### E2. FPGA
- Viết lại RTL pipeline. Có thể giữ ý tưởng cây cộng của file cũ, phần đó đúng.
- Testbench đọc `vectors_in.txt` và tự so với `golden_out.txt`, báo PASS/FAIL (nhãn **mô phỏng**).
- Synthesis bằng Yosys `synth_xilinx` hoặc Vivado cho Digilent Arty Z7-20 (`xc7z020clg400-1` @ 125 MHz) để lấy số DSP/LUT, Fmax và Power Report (nhãn **ước lượng công cụ**).
- Nếu có board FPGA thật: nạp và kiểm tra qua UART hoặc ILA. Đây là phần cộng điểm, không bắt buộc.
- **Đầu ra:** độ trễ (chu kỳ), thông lượng (mẫu/chu kỳ × Fmax), tài nguyên, công suất ước tính.

### E3. SoC Linux
- **Nếu có Raspberry Pi hoặc board Cortex-A:**
  - Chạy cùng file C FIR, đo thông lượng (nhãn **đo**).
  - Chạy `cyclictest` trên kernel thường, và nếu có thể trên kernel PREEMPT_RT, để lấy độ trễ xấu nhất (nhãn **đo**).
  - Đây là cách kiểm chứng trực tiếp con số 30–80 µs và "vài ms" của AC6 trong `PLAN.md`. Đây là thí nghiệm có giá trị nhất về determinism.
- **Nếu không có board:** chạy trên laptop Linux, ghi rõ "x86, chỉ để tham chiếu".

### E4. Phương án lai: overhead DMA (tùy chọn)
- Giữ ý tưởng hay của demo cũ: gói nhỏ thì để CPU tính, gói lớn mới đáng đẩy sang FPGA.
- Trình bày như **mô hình giải tích** (nhãn **tính**). Tham số overhead phải có nguồn (tài liệu AXI DMA của AMD, hoặc bài báo đo trên Zynq). Điểm hòa vốn tự tính lại từ công thức.
- Không có nguồn cho tham số thì bỏ E4, chỉ nói định tính.

### E5. Kiểm chứng chéo với PLAN.md
Một bảng đặt số nhóm tự đo cạnh số trong tài liệu:
- Tỉ lệ FPGA/CPU so với 27× của Arucu & Iliev.
- Độ trễ Linux so với số của AC6.
- Thông lượng MCU so với mức lý thuyết.

Lệch nhiều thì giải thích vì sao. Phần này chính là mục "Hạn chế" của `PLAN.md` được xử lý.

## 4. Chart mới

Mỗi chart ghi nhãn số liệu ngay dưới tiêu đề.

1. Thông lượng FIR: MCU (C thường / CMSIS), SoC, FPGA. Cùng bài toán, ghi xung nhịp từng nền tảng.
2. Độ trễ xấu nhất, thang log: MCU (đo hoặc nguồn), Linux thường và RT (đo bằng `cyclictest` hoặc nguồn), FPGA (mô phỏng).
3. Năng lượng mỗi mẫu: chỉ vẽ nếu có công suất **đo** hoặc **ước lượng công cụ**.
4. Ma trận quyết định: dạng bảng màu, lấy từ `PLAN.md`.
5. Dạng sóng RTL: chụp từ GTKWave.
6. (Nếu làm E4) Tăng tốc theo kích thước gói.

Bỏ chart điểm hòa vốn NRE/ASIC.

## 5. Khung thuyết trình

| Phần | Nội dung | Nguồn |
| --- | --- | --- |
| Mở đầu | Câu hỏi: chọn MCU, SoC hay FPGA khi nào; 3 tiêu chí | `PLAN.md` mục Mục tiêu |
| Kiến trúc | Tuần tự (MCU/SoC) vs song song không gian (FPGA); vì sao SoC cần MMU/Linux | Lecture 2, 3 |
| Số liệu tài liệu | Hiệu năng, chi phí/công suất, linh hoạt | `PLAN.md` |
| Thí nghiệm nhóm | E1–E3 (+E4), chart 1, 2, 5 | Mới |
| Kiểm chứng chéo | Bảng E5 | Mới |
| Ứng dụng | 6 tình huống, mỗi cái có một con số quyết định | `PLAN.md` |
| Kết luận | Ma trận quyết định + hạn chế | `PLAN.md` |

Lời thoại demo: viết lại sau khi có số thật. Kết bằng "FPGA thắng thông lượng nhưng đổi bằng giá và độ khó, MCU thắng năng lượng và giá", không kết bằng "FPGA vượt trội".

## 6. Thứ tự làm

| Ưu tiên | Việc | Phụ thuộc |
| --- | --- | --- |
| 1 | E0 golden model + vector | Không |
| 2 | E2 RTL + testbench tự so sánh + Yosys | E0 |
| 3 | E1 MCU (nhánh có hoặc không có board) | E0, phần cứng |
| 4 | E3 SoC Linux + `cyclictest` | E0, phần cứng |
| 5 | E5 bảng kiểm chứng chéo + chart | E1–E3 |
| 6 | Viết lại `README.md` theo nhãn số liệu; xóa hoặc lưu trữ demo cũ | E5 |
| 7 | Slide + lời thoại + Q&A | Tất cả |
| 8 | E4 (nếu còn thời gian) | E2 |

Mức tối thiểu để thuyết trình được: mục 1, 2, 5 và 7. Lúc đó MCU và SoC dùng nhãn **tính** hoặc **nguồn**, và phải nói rõ trên slide.

## 7. Chuẩn bị Q&A

- *"MCU đã tối ưu chưa?"* → Có số CMSIS-DSP (E1). Nếu chưa đo thì nói thẳng là chưa.
- *"Jitter FPGA bằng 0 thật à?"* → Mô phỏng RTL không có thời gian thực. Trên chip thật, logic đồng bộ có độ trễ cố định theo số chu kỳ, chỉ còn clock jitter cỡ ps.
- *"Sao so chip với board?"* → Đã ghi trong `PLAN.md`; con số chỉ để so bậc độ lớn.
- *"Số công suất ở đâu ra?"* → Mỗi số có nhãn và nguồn trên slide.
- *"Sao không có NRE?"* → Chưa có số công bố. Nhóm ghi thời gian thực tế viết bản C và bản HDL trong chính thí nghiệm này làm dẫn chứng định tính.

## 8. Việc nhóm cần quyết

- Nhóm có board STM32, Raspberry Pi hoặc FPGA thật không? Câu trả lời quyết định nhánh của E1, E2 và E3.
- Có cài được Vivado không, hay chỉ dùng Yosys?
- Hạn nộp và thời lượng thuyết trình, để chia thời gian cho mục 6.
