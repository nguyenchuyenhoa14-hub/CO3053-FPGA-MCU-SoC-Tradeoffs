# E5 · Kết quả thí nghiệm và kiểm chứng chéo

Tự động sinh bởi `e5_crosscheck/collect.py`. Nhãn: **đo** (nhóm tự đo trên phần cứng), **mô phỏng**, **ước lượng công cụ** (Vivado), **tính**, **nguồn** (tài liệu trong PLAN.md).

Bài toán chung: FIR 16-tap Q15, 1024 mẫu (seed 3053), 60 mẫu ra bão hòa; mọi nền tảng so từng mẫu với golden model.

## Thông lượng

| Nền tảng | Cấu hình | MSPS | Nhãn | Kiểm tra |
| --- | --- | --- | --- | --- |
| FPGA | Arty Z7-20 · 125 MHz trên board | 125.00 | đo | PASS |
| FPGA | XC7Z020 · Fmax ≈ 135 MHz | 134.60 | ước lượng công cụ | Vivado timing, chỉ khối FIR |

## Độ trễ xấu nhất

| Nền tảng | Kịch bản | Xấu nhất | Nhãn | Đại lượng đo |
| --- | --- | --- | --- | --- |
| FPGA | pipeline FIR · 125 MHz | 0.06 µs | đo | mẫu vào → mẫu ra |

Các dòng đo những đại lượng khác nhau (ngắt phần cứng, lập lịch Linux, pipeline), chỉ so bậc độ lớn.

## Năng lượng mỗi mẫu

| Nền tảng | Điều kiện | Công suất (W) | nJ/mẫu | Nhãn | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| FPGA | XC7Z020 cả chip @125 MHz | 0.117 | 0.94 | ước lượng công cụ | Vivado vector-less, gồm static |

## Kiểm chứng chéo với PLAN.md

| Câu hỏi | Nhóm đo được | Tài liệu nói | Ghi chú |
| --- | --- | --- | --- |
| Tài nguyên logic cho FIR 16-tap (chế độ thuần LUT, 0 DSP) | 0/220 DSP48E1 (0%), 1672/53200 LUTs (3.1%) | Kiến trúc soft-logic thuần túy (0 DSP) | 16 nhân + bộ cộng dạng cây tổng hợp hoàn toàn trên LUT, Fmax ≈ 135 MHz |
