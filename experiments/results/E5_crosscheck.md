# E5 · Kết quả thí nghiệm và kiểm chứng chéo

Tự động sinh bởi `e5_crosscheck/collect.py`. Nhãn: **đo** (nhóm tự đo trên phần cứng), **mô phỏng**, **ước lượng công cụ** (Vivado), **tính**, **nguồn** (tài liệu trong PLAN.md).

Bài toán chung: FIR 16-tap Q15, 1024 mẫu (seed 3053), 60 mẫu ra bão hòa; mọi nền tảng so từng mẫu với golden model.

## Thông lượng

| Nền tảng | Cấu hình | MSPS | Nhãn | Kiểm tra |
| --- | --- | --- | --- | --- |
| FPGA | RTL · giả định clock 100 MHz | 100.00 | mô phỏng | PASS |

## Độ trễ xấu nhất

| Nền tảng | Kịch bản | Xấu nhất | Nhãn | Đại lượng đo |
| --- | --- | --- | --- | --- |
| FPGA | pipeline FIR · 100 MHz | 0.07 µs | mô phỏng | mẫu vào → mẫu ra |

Các dòng đo những đại lượng khác nhau (ngắt phần cứng, lập lịch Linux, pipeline), chỉ so bậc độ lớn.

## Năng lượng mỗi mẫu

| Nền tảng | Điều kiện | Công suất (W) | nJ/mẫu | Nhãn | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| — | chưa có số đo công suất | | | | |

## Kiểm chứng chéo với PLAN.md

| Câu hỏi | Nhóm đo được | Tài liệu nói | Ghi chú |
| --- | --- | --- | --- |
| — | chưa đủ số liệu | | |
