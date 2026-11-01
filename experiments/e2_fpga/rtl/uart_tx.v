// UART TX 8N1 don gian
`timescale 1ns / 1ps
`default_nettype none

module uart_tx #(
    parameter integer CLKS_PER_BIT = 868   // 100 MHz / 115200
) (
    input  wire       clk,
    input  wire       rst,
    input  wire       start,   // chi nhan khi busy = 0
    input  wire [7:0] data,
    output reg        tx,
    output reg        busy
);
    reg [8:0]  shreg;   // {stop, data[7:0]}
    reg [3:0]  left;    // so bit con lai sau bit dang phat
    reg [15:0] cnt;

    always @(posedge clk) begin
        if (rst) begin
            tx   <= 1'b1;
            busy <= 1'b0;
        end else if (!busy) begin
            if (start) begin
                shreg <= {1'b1, data};
                tx    <= 1'b0;          // bit start
                left  <= 4'd9;
                cnt   <= 0;
                busy  <= 1'b1;
            end
        end else if (cnt != CLKS_PER_BIT - 1) begin
            cnt <= cnt + 1;
        end else begin
            cnt <= 0;
            if (left == 0) begin
                busy <= 1'b0;           // da phat du bit stop
            end else begin
                tx    <= shreg[0];
                shreg <= {1'b1, shreg[8:1]};
                left  <= left - 1;
            end
        end
    end
endmodule

`default_nettype wire
