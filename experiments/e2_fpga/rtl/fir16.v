// ============================================================================
// E2 - FIR 16-tap Q15, pipeline day du, 1 mau / chu ky (LUT-only, NO DSP).
// Dac ta: y[n] = sat16(floor(sum h[k]*x[n-k] / 2^15))  (giong golden model E0)
//
// Pipeline (moi tang 1 chu ky):
//   S0 thanh ghi duong tre (chi dich khi in_valid)
//   S1 16 phep nhan song song bang soft-logic LUTs (use_dsp = "no")
//   S2..S5 cay cong 16->8->4->2->1 bang LUTs + CARRY4
//   S6 dich 15 bit + bao hoa
// Do tre = 7 tang thanh ghi (S0..S6) = 7 chu ky (testbench do va xac nhan).
// ============================================================================
`timescale 1ns / 1ps
`default_nettype none

(* use_dsp = "no" *)
module fir16 (
    input  wire               clk,
    input  wire               rst,        // dong bo, muc cao
    input  wire               in_valid,
    input  wire signed [15:0] in_data,
    output reg                out_valid,
    output reg  signed [15:0] out_data
);
    `include "fir_coeffs.vh"

    localparam integer N = 16;
    localparam integer VDEPTH = 6;   // co valid cho S0..S5; out_valid la tang S6

    function signed [15:0] coeff(input integer k);
        case (k)
            0: coeff = H0;   1: coeff = H1;   2: coeff = H2;   3: coeff = H3;
            4: coeff = H4;   5: coeff = H5;   6: coeff = H6;   7: coeff = H7;
            8: coeff = H8;   9: coeff = H9;  10: coeff = H10; 11: coeff = H11;
           12: coeff = H12; 13: coeff = H13; 14: coeff = H14; default: coeff = H15;
        endcase
    endfunction

    integer i;

    // S0: duong tre, x_d[k] = x[n-k]
    reg signed [15:0] x_d [0:N-1];
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < N; i = i + 1) x_d[i] <= 16'sd0;
        end else if (in_valid) begin
            x_d[0] <= in_data;
            for (i = 1; i < N; i = i + 1) x_d[i] <= x_d[i-1];
        end
    end

    // S1: nhan song song bang Logic LUTs (khong dung DSP48E1)
    (* use_dsp = "no" *) reg signed [31:0] p [0:N-1];
    always @(posedge clk)
        for (i = 0; i < N; i = i + 1) p[i] <= x_d[i] * coeff(i);

    // S2..S5: cay cong bang LUTs + CARRY4. |acc| <= 32768 * sum|h| < 2^31, dung 34 bit cho an toan
    (* use_dsp = "no" *) reg signed [33:0] s1 [0:7];
    (* use_dsp = "no" *) reg signed [33:0] s2 [0:3];
    (* use_dsp = "no" *) reg signed [33:0] s3 [0:1];
    (* use_dsp = "no" *) reg signed [33:0] s4;
    always @(posedge clk) begin
        for (i = 0; i < 8; i = i + 1) s1[i] <= p[2*i] + p[2*i+1];
        for (i = 0; i < 4; i = i + 1) s2[i] <= s1[2*i] + s1[2*i+1];
        for (i = 0; i < 2; i = i + 1) s3[i] <= s2[2*i] + s2[2*i+1];
        s4 <= s3[0] + s3[1];
    end

    // S6: floor(/2^15) + bao hoa
    wire signed [18:0] q = s4 >>> 15;   // 34-15 = 19 bit
    always @(posedge clk) begin
        if (q > 19'sd32767)       out_data <= 16'sd32767;
        else if (q < -19'sd32768) out_data <= -16'sd32768;
        else                      out_data <= q[15:0];
    end

    // Co valid di song song voi du lieu (S0..S5), out_valid cung tang voi S6
    reg [VDEPTH-1:0] vpipe;
    always @(posedge clk) begin
        if (rst) begin
            vpipe     <= {VDEPTH{1'b0}};
            out_valid <= 1'b0;
        end else begin
            vpipe     <= {vpipe[VDEPTH-2:0], in_valid};
            out_valid <= vpipe[VDEPTH-1];
        end
    end
endmodule

`default_nettype wire
