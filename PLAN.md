# So sánh MCU – SoC – FPGA: hiệu năng, chi phí, linh hoạt

Nov 1, 2026 · @Thang

## Mục tiêu và phạm vi

Bài trả lời một câu hỏi: khi nào nên chọn MCU, SoC hay FPGA, xét theo hiệu năng, chi phí và tính linh hoạt. Bài không nhằm chứng minh một nền tảng "tốt nhất", vì `pe2` xếp mục tiêu thiên vị vào danh sách lỗi thường gặp.

| Nền tảng | Đại diện dùng để lấy số liệu | Cách chạy phần mềm |
| --- | --- | --- |
| MCU | ARM Cortex-M: STM32F4, STM32H743, STM32U5 | Bare-metal hoặc RTOS |
| SoC | ARM Cortex-A + Linux: Raspberry Pi 4, STM32MP1 (theo Lecture 2) | Linux có sẵn driver, mạng, file system |
| FPGA | Xilinx Artix-7 XC7A100T; Zynq (CPU + FPGA) làm phương án lai | Mô tả phần cứng bằng HDL/HLS, không có "chương trình" tuần tự |

Số liệu lấy từ datasheet và benchmark đã công bố, không phải do nhóm tự đo. Giá trị tự tính từ số liệu đó được ghi "(tính)" kèm giả thiết. Chip và board không cùng cấp: giá MCU và FPGA là giá linh kiện, giá Raspberry Pi là giá cả board.

## Số liệu định lượng

Theo số liệu công bố, FPGA vượt MCU khoảng 100 lần về thông lượng MAC tối đa (lý thuyết) và khoảng 70–200 lần về độ trễ xấu nhất (hai phép đo khác bản chất, nên đọc thận trọng), còn MCU thắng rõ về công suất nghỉ và giá. SoC có CoreMark cao nhất nhưng độ trễ xấu nhất kém ổn định hơn MCU.

### Hiệu năng

**CPU thuần (CoreMark, càng cao càng nhanh).** CoreMark không áp dụng cho FPGA vì FPGA không chạy chương trình tuần tự; FPGA được đo bằng thông lượng MAC ở bảng kế tiếp.

| Nền tảng | Chip | Lõi / xung nhịp | CoreMark | Nguồn |
| --- | --- | --- | --- | --- |
| MCU | STM32F4 | Cortex-M4, 180 MHz | 608 | [ST product overview](https://www.st.com/resource/en/product_presentation/microcontrollers_stm32h72x-3x_line_product-overview.pdf) |
| MCU | STM32H743 | Cortex-M7, 480 MHz | 2424 | [ST STM32H743](https://www.st.com/en/microcontrollers-microprocessors/stm32h743-753.html) |
| SoC | STM32MP1 | Cortex-A7, 800 MHz | 4158 | [ST product overview](https://www.st.com/resource/en/product_presentation/microcontrollers_stm32h72x-3x_line_product-overview.pdf) |
| SoC | Raspberry Pi 4 | 4 × Cortex-A72, 1,8 GHz | 38 200 (tổng 4 lõi) | [OpenBenchmarking](https://mail.openbenchmarking.org/result/2511110-NE-BROADCOMB24&export=html) |

**Thông lượng MAC song song.** Bài toán mẫu là lọc ảnh 3×3 trên video 1080p, 3 kênh màu, 30 khung/giây. Theo Lee & Seshia mục 8.1, bài này cần 1 679 616 000 phép nhân mỗi giây (≈1,68 G MAC/s).

| Chỉ số | MCU STM32H743 | FPGA Artix-7 XC7A100T |
| --- | --- | --- |
| Đơn vị tính toán | 1 lõi Cortex-M7, 480 MHz | 240 khối DSP48E1 chạy song song |
| MAC/s tối đa | ≈0,48 G (tính: 1 MAC/chu kỳ × 480 MHz) | ≈48 G (tính: 240 × 200 MHz); hãng công bố tới 264 G ([datasheet XA Artix-7](https://datasheet.chipsmall.com/XA7A25T-1CPG238Q/297909.pdf)) |
| Đáp ứng 1,68 G MAC/s | Không: chỉ đạt ≈29% dù hiệu suất 100% (tính) | Có: dùng ≈3,5% năng lực ở 200 MHz (tính) |

Giả thiết: MCU làm 1 MAC mỗi chu kỳ; nếu dùng lệnh SIMD 2 MAC 16-bit mỗi chu kỳ thì MCU đạt ≈57%, vẫn thiếu. FPGA chạy ở 200 MHz là giả định bảo thủ, thấp hơn mức tối đa mà chip cho phép. Tỉ lệ ≈48 / 0,48 = 100 lần là giới hạn lý thuyết, không phải tốc độ đo được.

**Benchmark FIR đã công bố** (bộ lọc 27 tap, [Arucu & Iliev, 2025](https://www.mdpi.com/2079-9268/15/3/40)):

| Nền tảng | Thời gian xử lý | Công suất |
| --- | --- | --- |
| FPGA (Zynq XC7Z020) | 0,004 s | 1,431 W, đo (gồm ARM 1,296 W, logic FIR 0,135 W) |
| GPU (Tesla K80) | 0,008 s | 50–100 W, tác giả ước tính |
| CPU (Arm Cortex-A9) | 0,107 s | 5–10 W, tác giả ước tính |

FPGA nhanh hơn CPU Cortex-A khoảng 27 lần. Năng lượng mỗi lần chạy của FPGA ≈5,7 mJ, của CPU ≈0,54–1,07 J, chênh khoảng 95–190 lần (tính, vì công suất CPU chỉ là ước tính). Bài này so FPGA với Cortex-A, không có MCU Cortex-M, và không nêu số mẫu đầu vào, nên chỉ dùng để so bậc độ lớn. Với phương án lai, bộ lọc FIR trên SoC FPGA+ARM nhanh gấp 8,86 lần ARM đơn, chậm hơn Intel i7 1,98 lần và có tỉ lệ giá/hiệu năng tốt nhất trong ba cấu hình thử ([Tatar đồng tác giả, 2022](https://acikerisim.fsm.edu.tr/items/5936ddea-aee1-4899-abad-21e05293bae6)).

**Độ trễ xấu nhất (determinism).**

| Nền tảng | Độ trễ xấu nhất điển hình | Ghi chú |
| --- | --- | --- |
| FPGA | 13,9 ns | Kỷ lục STAC-T0 của Exegy/AMD cho độ trễ I/O mạng khi giao dịch ([A-Team Insight](https://a-teaminsight.com/blog/exegy-and-amd-achieve-record-breaking-tick-to-trade-latency-in-stac-t0-benchmark/)); không phải mọi bài toán |
| MCU Cortex-M bare-metal | 1–3 µs | [AC6](https://www.ac6-formation.com/en/articles/real-time-latency-linux-preempt-rt) |
| SoC Linux PREEMPT\_RT, Cortex-A đã tinh chỉnh | 30–80 µs | AC6 |
| SoC Linux thường | vài ms | AC6 |

AC6 lưu ý đây là bậc độ lớn quan sát được, không phải thông số đảm bảo, và cùng cấu hình trên hai SoC có thể lệch ba lần.

### Chi phí và công suất

MCU rẻ nhất và tiết kiệm điện nhất khi nghỉ; FPGA đắt nhất trên mỗi chip; SoC rẻ ở mức board nhưng tiêu thụ vài watt ngay cả khi rảnh.

| Chỉ số | MCU STM32H743 | SoC Raspberry Pi 4 | FPGA Artix-7 XC7A100T |
| --- | --- | --- | --- |
| Giá (mua lẻ) | £9,26–11,97 mỗi chip, tùy số lượng ([RS UK](https://uk.rs-online.com/web/p/microcontrollers/1653272)) | $35 mỗi board khi ra mắt ([AnandTech](https://at-web1.www.anandtech.com/show/14581/raspberry-pi-4-launched-quad-cortex-a72-project-board-for-35-dollars)) | €143,90 mỗi chip, mua 1 cái ([Farnell](https://at.farnell.com/xilinx/xc7a100t-1csg324c/fpga-artix-7-210-i-o-cspbga-324/dp/2760123)) |
| Công suất khi chạy | ≈0,44 W ở 480 MHz (tính: 275 µA/MHz × 480 MHz × 3,3 V, tắt ngoại vi) | ≈7 W lúc đỉnh, cả board ([Raspberry Pi qua TechFeed](https://techfeed.io/entries/5d112019e50460ac6f5ccf16)) | 1,431 W đo trên Zynq XC7Z020 trong bài FIR, gồm cả phần ARM (chip khác, chỉ tham khảo) |
| Công suất nghỉ | 2,43 µA ở Standby ([ST](https://www.st.com/en/microcontrollers-microprocessors/stm32h743-753.html)); 300 nA ở STM32U5 ([Arrow](https://www.arrow.com/en/research-and-events/articles/stm32u5-ultra-low-power-arm-cortex-m33-32-bit-microcontroller)) | ≈3 W khi rảnh, cả board | Chưa có số liệu trong các nguồn đã mở |

Với 300 nA ở 3,3 V, STM32U5 chỉ dùng ≈1 µW khi nghỉ (tính), so với ≈3 W của Pi 4 rảnh: chênh khoảng 3 triệu lần. So sánh chip với board nên con số chỉ dùng để thấy bậc độ lớn. Một thiết kế mẫu của TI cho nút cảm biến dùng MCU đạt hơn 10 năm trên pin CR2032 ([TI TIDU797](https://ti.com/lit/pdf/tidu797)).

Câu hỏi mở: chưa có số giờ công phát triển đã công bố để so NRE giữa ba nền tảng; phần này dùng thang định tính bên dưới. Nếu thầy cần số, nhóm nên tự đo thời gian làm cùng một bài FIR trên C và trên HDL.

### Tính linh hoạt

MCU và SoC linh hoạt về phần mềm nhất; FPGA linh hoạt về phần cứng nhưng khó lập trình nhất. Bảng dưới đây lấy từ Lecture 2, Lecture 3 và bài FIR, không phải số đo.

| Tiêu chí | MCU | SoC + Linux | FPGA |
| --- | --- | --- | --- |
| Cách lập trình | Truy cập thanh ghi mức thấp (Lecture 2) | OS đầy đủ, driver và network stack có sẵn (Lecture 2) | Mọi phép toán phải mô tả từ đầu ở mức phần cứng ([Arucu & Iliev](https://www.mdpi.com/2079-9268/15/3/40)) |
| Time-to-market | Nhanh với chức năng đơn giản, cố định (Lecture 2) | Nhanh với sản phẩm nhiều tính năng, có kết nối (Lecture 2) | Lecture 3: thêm FPGA làm linh hoạt giảm từ Cao (CPU đơn) xuống Trung bình; thêm cả DSP thì xuống Thấp nhất |
| Thời gian thực | Rất tốt với bare-metal/RTOS (Lecture 2) | Yếu hơn nếu không có bản vá real-time (Lecture 2) | Timing phần cứng xác định, không phụ thuộc tải CPU (Lecture 3) |
| Đổi chức năng sau triển khai | Nạp lại firmware | Cập nhật phần mềm/OS | Nạp lại cấu hình phần cứng (tính tái cấu hình, theo Arucu & Iliev) |

## Ứng dụng thực tế: vì sao chọn nền tảng đó

Mỗi ứng dụng dưới đây bị một con số quyết định: năng lượng khi nghỉ, deadline, tính năng phần mềm, độ trễ hay thông lượng. Nền tảng được chọn là nền tảng đủ đáp ứng con số đó với chi phí thấp nhất, đúng tinh thần Lecture 2: không có nền tảng tốt nhất cho mọi trường hợp.

### 1. Nút cảm biến chạy pin: MCU

- **Con số quyết định:** năng lượng khi nghỉ. STM32U5 ở Standby chỉ dùng 300 nA, và thiết kế mẫu của TI đạt hơn 10 năm trên pin CR2032 ([Arrow](https://www.arrow.com/en/research-and-events/articles/stm32u5-ultra-low-power-arm-cortex-m33-32-bit-microcontroller), [TI TIDU797](https://ti.com/lit/pdf/tidu797)).
- **Vì sao chọn:** tác vụ nhẹ (thức dậy, đo, gửi, ngủ), nên MCU ngủ gần như toàn thời gian là đủ.
- **Vì sao không chọn SoC hay FPGA:** Pi 4 rảnh đã ≈3 W, khoảng 3 triệu lần MCU ở Standby (tính, so board với chip). FPGA thì không có số liệu nghỉ trong nguồn đã mở, và bài toán không cần song song.

### 2. Điều khiển động cơ BLDC/PMSM (FOC): MCU

- **Con số quyết định:** deadline. Ở 20 kHz, toàn bộ chuỗi Clarke, Park, 2 PID và SVPWM phải xong trong 50 µs ([Applied EE](https://applied-ee.github.io/embedded/docs/motor-control/brushless-motors/field-oriented-control/)). Thư viện vector control của ST ghi dưới 21 µs trên Cortex-M3 ([ST, 2008](https://www.promelec.ru/UPLOAD/fck/file/stm_files/stm32/Motor_control_with_STM32.pdf)).
- **Vì sao chọn:** MCU đáp ứng với dư hơn gấp 2 lần deadline, có sẵn timer PWM và ADC, giá chỉ vài bảng.
- **Vì sao không chọn SoC:** Linux PREEMPT\_RT đã tinh chỉnh có độ trễ xấu nhất 30–80 µs, có thể tự nó ngốn hết hoặc vượt deadline 50 µs. FPGA chỉ đáng tiền khi deadline hẹp hơn khả năng MCU (suy luận của nhóm).

### 3. Camera thông minh, gateway IoT: SoC

- **Con số quyết định:** tính năng phần mềm. MCU thường không có MMU nên không chạy được Linux hay Android ([Google Developers](https://medium.com/google-developers/computing-at-the-edge-of-iot-140a888007bd)), còn Pi 4 có CoreMark gấp ≈16 lần STM32H743 (38 200 so với 2424, tính).
- **Vì sao chọn:** camera MIPI CSI hoặc USB chạy ngay qua V4L2 trên Linux; trên MCU phải tự viết driver, quản lý DMA và xử lý ảnh ([Applied EE](https://applied-ee.github.io/ee-notebook/docs/embedded/mpu-and-sbc-architecture/where-mpus-fit)).
- **Vì sao không chọn MCU hay FPGA:** firmware MCU sẽ phải tái tạo TCP/IP, file system, scheduler. FPGA thì phải mô tả cả network stack bằng HDL, trong khi yêu cầu thời gian thực chỉ "mềm", Linux là đủ.

### 4. Lọc video 1080p 30 khung/giây: FPGA

- **Con số quyết định:** thông lượng. Bài lọc 3×3 cần ≈1,68 G MAC/s (Lee & Seshia mục 8.1); MCU STM32H743 chỉ đạt tối đa ≈0,48 G, FPGA XC7A100T đạt ≈48 G ở 200 MHz (tính).
- **Vì sao chọn:** mỗi pixel độc lập, nên 240 khối DSP chạy song song. Trên Zynq, FIR 27 tap nhanh hơn Cortex-A9 khoảng 27 lần và dùng ít năng lượng hơn khoảng 95–190 lần (tính) ([Arucu & Iliev](https://www.mdpi.com/2079-9268/15/3/40)).
- **Vì sao không chọn MCU:** thiếu ≈3,5 lần năng lực ngay cả khi hiệu suất 100%. SoC làm được nếu có SIMD/GPU, nhưng mất tính xác định và tốn điện hơn (xem bảng công suất).

### 5. Giao dịch tần suất cao: FPGA

- **Con số quyết định:** độ trễ tick-to-trade. Kỷ lục STAC-T0 hiện là 13,9 ns, thấp hơn kỷ lục 24,2 ns trước đó, cả hai trên bộ tăng tốc của AMD ([A-Team Insight](https://a-teaminsight.com/blog/exegy-and-amd-achieve-record-breaking-tick-to-trade-latency-in-stac-t0-benchmark/)).
- **Vì sao chọn:** giải mã gói tin, định giá và kiểm tra rủi ro chạy thành pipeline song song trong phần cứng, độ trễ cố định theo chu kỳ xung nhịp.
- **Vì sao không chọn MCU hay SoC:** Linux tinh chỉnh tốt nhất vẫn ở 30–80 µs, Linux thường là vài ms ([AC6](https://www.ac6-formation.com/en/articles/real-time-latency-linux-preempt-rt)). Đây là hai phép đo khác nhau (I/O mạng và độ trễ lập lịch) nên chỉ so bậc độ lớn.

### 6. ECU ô tô, ADAS, điều khiển công nghiệp: phương án lai CPU + FPGA

- **Con số quyết định:** cần cả tính năng phần mềm lẫn timing đảm bảo. Lecture 3 xếp CPU đơn là "timing yếu, có thể trễ deadline"; CPU + FPGA là "tốt cho điều khiển actuator", chi phí trung bình.
- **Vì sao chọn:** CPU lo nhận dữ liệu và tính toán mềm dẻo; FPGA giữ phần timing nghiêm ngặt dù CPU đang bận (Lecture 3, Option #2). Zynq UltraScale+ gom sẵn 4 lõi Cortex-A53 chạy Linux, 2 lõi Cortex-R5 real-time có thể chạy lockstep và fabric FPGA trên một chip, nhắm tới ADAS và điều khiển công nghiệp ([eeNews Europe](https://www.eenewseurope.com/en/programmable-multi-processor-soc-targets-vision-adas-iot-and-5g/)). Một thử nghiệm FIR trên SoC FPGA+ARM cho kết quả nhanh gấp 8,86 lần ARM đơn và có giá/hiệu năng tốt nhất ([Tatar đồng tác giả](https://acikerisim.fsm.edu.tr/items/5936ddea-aee1-4899-abad-21e05293bae6)).
- **Vì sao không chọn một nền tảng đơn:** MCU thiếu sức cho vision, SoC đơn khó đảm bảo timing, FPGA đơn khó chạy hệ điều hành phong phú. Cái giá là chi phí cao hơn và linh hoạt thấp hơn Option #1.

## Ma trận quyết định và kết luận

Không nền tảng nào thắng toàn diện: muốn timing và thông lượng cao hơn thì phải trả bằng giá cao hơn và linh hoạt thấp hơn, đúng chiều của bảng trade-off ở Lecture 3. Chọn MCU khi deadline ở mức vài chục µs trở lên và giá hay năng lượng là ràng buộc; chọn SoC khi cần OS, mạng, đa phương tiện với timing mềm; chọn FPGA khi thông lượng song song hoặc độ trễ vượt khả năng CPU; chọn phương án lai khi cần cả hai.

| Điều kiện của bài toán | Nền tảng | Căn cứ |
| --- | --- | --- |
| Pin nhiều năm, tác vụ nhẹ | MCU | 300 nA ở Standby; hơn 10 năm trên CR2032 |
| Deadline vài chục µs, cần độ trễ ổn định | MCU | 1–3 µs bare-metal, so với 30–80 µs trên Linux RT |
| Cần Linux, camera, mạng, giao diện; timing mềm | SoC | CoreMark gấp ≈16 lần MCU; driver và network stack có sẵn |
| Trên ≈0,5 G MAC/s liên tục (vượt 1 lõi Cortex-M7) | FPGA hoặc lai | ≈48 G MAC/s (tính) so với ≈0,48 G |
| Độ trễ cỡ ns, pipeline cố định | FPGA | 13,9 ns tick-to-trade |
| Cần cả OS phong phú lẫn timing hay song song cứng | Lai (Zynq) | Lecture 3, Option #2 |

Xếp hạng theo từng tiêu chí của thầy, dựa trên các bảng ở trên:

| Tiêu chí | Hạng 1 | Hạng 2 | Hạng 3 | Lưu ý |
| --- | --- | --- | --- | --- |
| Thông lượng song song | FPGA | SoC | MCU | SoC xếp giữa theo CoreMark; chưa có benchmark MAC song song riêng cho SoC |
| Độ trễ và tính xác định | FPGA | MCU | SoC | Hai phép đo khác bản chất, chỉ so bậc độ lớn |
| Giá linh kiện | MCU | SoC | FPGA | So chip với board nên SoC có thể đổi chỗ theo cấu hình |
| Linh hoạt lập trình, time-to-market | MCU, SoC |  | FPGA | MCU hợp bài đơn giản, SoC hợp bài nhiều tính năng (Lecture 2) |

Hạn chế cần nêu khi trình bày:

- Số liệu lấy từ nhiều nguồn với điều kiện khác nhau, chưa phải một thí nghiệm đồng nhất trên cùng workload.
- Không tìm thấy benchmark FIR công bố cho MCU Cortex-M trong các nguồn đã dùng; phần MCU dựa trên tính toán lý thuyết.
- Bài FIR chỉ dùng bộ lọc 27 tap và không nêu số mẫu, công suất CPU/GPU là ước tính của tác giả.
- Theo `pe3`, kết quả chưa kiểm chứng chéo bằng phép đo hoặc mô phỏng vẫn đáng ngờ; bước tiếp theo là tự đo cùng một bài FIR trên STM32 và trên FPGA.

## Nguồn tham khảo

Tra cứu ngày 01/11/2026. Ba trang đã mở trọn: Arucu & Iliev (MDPI), AC6, ST STM32H743. Các nguồn còn lại lấy số từ đoạn trích trong kết quả tìm kiếm; giá bán lẻ có thể đổi theo ngày.

**Tài liệu môn học (project):** Lecture 2 (Choosing a Platform, slide 47), Lecture 3 (ECU Design Option #1–#3, slide 33–35), `pe2-PE-steps`, `pe3-technique-metrics-selection`, Lee & Seshia *Introduction to Embedded Systems* mục 8.1–8.2.

**Hiệu năng:**

- [ST: product overview STM32H7/F4/MP1 (CoreMark)](https://www.st.com/resource/en/product_presentation/microcontrollers_stm32h72x-3x_line_product-overview.pdf)
- [ST: STM32H743/753](https://www.st.com/en/microcontrollers-microprocessors/stm32h743-753.html)
- [OpenBenchmarking: Raspberry Pi 4 (CoreMark)](https://mail.openbenchmarking.org/result/2511110-NE-BROADCOMB24&export=html)
- [Datasheet XA Artix-7 (240 DSP48E1, 264 GMACs)](https://datasheet.chipsmall.com/XA7A25T-1CPG238Q/297909.pdf)
- [Arucu & Iliev, J. Low Power Electron. Appl. 2025: FPGA, GPU, CPU FIR](https://www.mdpi.com/2079-9268/15/3/40)
- [Tatar đồng tác giả, AICT 2022: FIR trên Zynq SoC](https://acikerisim.fsm.edu.tr/items/5936ddea-aee1-4899-abad-21e05293bae6)
- [AC6: độ trễ real-time Linux với PREEMPT\_RT](https://www.ac6-formation.com/en/articles/real-time-latency-linux-preempt-rt)
- [A-Team Insight: Exegy/AMD STAC-T0](https://a-teaminsight.com/blog/exegy-and-amd-achieve-record-breaking-tick-to-trade-latency-in-stac-t0-benchmark/)

**Chi phí và công suất:**

- [RS UK: STM32H743ZIT6](https://uk.rs-online.com/web/p/microcontrollers/1653272)
- [AnandTech: Raspberry Pi 4](https://at-web1.www.anandtech.com/show/14581/raspberry-pi-4-launched-quad-cortex-a72-project-board-for-35-dollars)
- [Farnell: XC7A100T-1CSG324C](https://at.farnell.com/xilinx/xc7a100t-1csg324c/fpga-artix-7-210-i-o-cspbga-324/dp/2760123)
- [TechFeed: công suất Raspberry Pi 4](https://techfeed.io/entries/5d112019e50460ac6f5ccf16)
- [Arrow: STM32U5](https://www.arrow.com/en/research-and-events/articles/stm32u5-ultra-low-power-arm-cortex-m33-32-bit-microcontroller)
- [TI TIDU797: nút cảm biến 10+ năm trên CR2032](https://ti.com/lit/pdf/tidu797)

**Ứng dụng:**

- [Applied EE: Field-Oriented Control](https://applied-ee.github.io/embedded/docs/motor-control/brushless-motors/field-oriented-control/)
- [ST: Motor control with STM32 (2008)](https://www.promelec.ru/UPLOAD/fck/file/stm_files/stm32/Motor_control_with_STM32.pdf)
- [Applied EE: Where MPUs fit](https://applied-ee.github.io/ee-notebook/docs/embedded/mpu-and-sbc-architecture/where-mpus-fit)
- [Google Developers: Computing at the edge of IoT](https://medium.com/google-developers/computing-at-the-edge-of-iot-140a888007bd)
- [eeNews Europe: Zynq UltraScale+ MPSoC](https://www.eenewseurope.com/en/programmable-multi-processor-soc-targets-vision-adas-iot-and-5g/)
