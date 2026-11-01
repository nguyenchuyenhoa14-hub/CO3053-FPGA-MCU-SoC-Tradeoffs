/**
 * ============================================================================
 * FULLY-PIPELINED SYSTOLIC FIR FILTER 16-TAP TRÊN FPGA (VERILOG HDL)
 * Môn học: [HK261] CO3053 - Hệ thống nhúng | Đề tài 9
 * ============================================================================
 * Đặc tính:
 * - 16 khối nhân DSP Slices chạy SONG SONG đồng thời trên không gian phần cứng.
 * - Cây cộng dồn Pipelined Adder Tree 4 tầng.
 * - Đạt thông lượng cực đại: 1 mẫu dữ liệu ngõ ra trên MỖI chu kỳ xung nhịp clock!
 */

`timescale 1ns / 1ps

module fir_filter_16tap (
    input  wire                     clk,        // Xung nhịp hệ thống (ví dụ: 100 MHz, chu kỳ 10ns)
    input  wire                     rst_n,      // Tín hiệu Reset tích cực mức thấp (Active-low reset)
    input  wire                     valid_in,   // Báo hiệu mẫu đầu vào x[n] hợp lệ
    input  wire signed [15:0]       data_in,    // Mẫu tín hiệu đầu vào dạng Q15 (16-bit signed)
    output reg                      valid_out,  // Báo hiệu mẫu ngõ ra y[n] đã tính toán xong
    output reg  signed [15:0]       data_out    // Mẫu tín hiệu ngõ ra sau lọc Q15
);

    // Mảng 16 hệ số bộ lọc Q15 đối xứng
    wire signed [15:0] h [0:15];
    assign h[0]  = -16'sd120; assign h[1]  = 16'sd180;  assign h[2]  = 16'sd350;  assign h[3]  = 16'sd720;
    assign h[4]  = 16'sd1250; assign h[5]  = 16'sd1890; assign h[6]  = 16'sd2450; assign h[7]  = 16'sd2800;
    assign h[8]  = 16'sd2800; assign h[9]  = 16'sd2450; assign h[10] = 16'sd1890; assign h[11] = 16'sd1250;
    assign h[12] = 16'sd720;  assign h[13] = 16'sd350;  assign h[14] = 16'sd180;  assign h[15] = -16'sd120;

    // Đường trễ dữ liệu đầu vào (15 thanh ghi lưu x[n-1] ... x[n-15])
    reg signed [15:0] shift_reg [0:14];

    // Mảng tín hiệu tổ hợp 16 taps: tap_x[0] = x[n] hiện tại, tap_x[1..15] = x[n-1..n-15]
    wire signed [15:0] tap_x [0:15];
    assign tap_x[0] = data_in;
    genvar g;
    generate
        for (g = 1; g < 16; g = g + 1) begin : gen_taps
            assign tap_x[g] = shift_reg[g-1];
        end
    endgenerate

    // Tầng 1 (Chu kỳ 1): 16 phép nhân phần cứng song song đồng thời (16 DSP Slices)
    reg signed [31:0] mult_reg [0:15];

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 15; i = i + 1) begin
                shift_reg[i] <= 16'sd0;
            end
            for (i = 0; i < 16; i = i + 1) begin
                mult_reg[i]  <= 32'sd0;
            end
        end else if (valid_in) begin
            // 16 bộ nhân DSP hoạt động đồng thời ngay khi mẫu x[n] xuất hiện!
            for (i = 0; i < 16; i = i + 1) begin
                mult_reg[i] <= tap_x[i] * h[i];
            end

            // Cập nhật đường trễ phần cứng cho chu kỳ kế tiếp
            shift_reg[0] <= data_in;
            for (i = 1; i < 15; i = i + 1) begin
                shift_reg[i] <= shift_reg[i-1];
            end
        end
    end

    // Tầng 2..5 (Chu kỳ 2..5): Cây cộng dồn Pipelined Adder Tree (4 tầng đường ống)
    reg signed [35:0] sum_stg1 [0:7];
    reg signed [35:0] sum_stg2 [0:3];
    reg signed [35:0] sum_stg3 [0:1];
    wire signed [35:0] sum_final_w = sum_stg3[0] + sum_stg3[1];

    // Pipeline cờ báo Valid (Độ trễ đường ống chuẩn xác 5 chu kỳ: mult -> stg1 -> stg2 -> stg3 -> out)
    reg [3:0] valid_pipe;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_pipe <= 4'b0000;
            valid_out  <= 1'b0;
            data_out   <= 16'sd0;
            for (i = 0; i < 8; i = i + 1) sum_stg1[i] <= 36'sd0;
            for (i = 0; i < 4; i = i + 1) sum_stg2[i] <= 36'sd0;
            for (i = 0; i < 2; i = i + 1) sum_stg3[i] <= 36'sd0;
        end else begin
            valid_pipe <= {valid_pipe[2:0], valid_in};

            // Tầng cộng 1 (Chu kỳ 2): 16 -> 8
            sum_stg1[0] <= mult_reg[0]  + mult_reg[1];
            sum_stg1[1] <= mult_reg[2]  + mult_reg[3];
            sum_stg1[2] <= mult_reg[4]  + mult_reg[5];
            sum_stg1[3] <= mult_reg[6]  + mult_reg[7];
            sum_stg1[4] <= mult_reg[8]  + mult_reg[9];
            sum_stg1[5] <= mult_reg[10] + mult_reg[11];
            sum_stg1[6] <= mult_reg[12] + mult_reg[13];
            sum_stg1[7] <= mult_reg[14] + mult_reg[15];

            // Tầng cộng 2 (Chu kỳ 3): 8 -> 4
            sum_stg2[0] <= sum_stg1[0] + sum_stg1[1];
            sum_stg2[1] <= sum_stg1[2] + sum_stg1[3];
            sum_stg2[2] <= sum_stg1[4] + sum_stg1[5];
            sum_stg2[3] <= sum_stg1[6] + sum_stg1[7];

            // Tầng cộng 3 (Chu kỳ 4): 4 -> 2
            sum_stg3[0] <= sum_stg2[0] + sum_stg2[1];
            sum_stg3[1] <= sum_stg2[2] + sum_stg2[3];

            // Tầng cộng 4 & Xuất kết quả Q15 (Chu kỳ 5): 2 -> 1
            data_out    <= sum_final_w[30:15];
            valid_out   <= valid_pipe[3];
        end
    end

endmodule
