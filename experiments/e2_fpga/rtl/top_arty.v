// ============================================================================
// E2 - Tu kiem FIR16 tren board Arty A7-100T.
//
// Sau reset (hoac nhan BTN0): doc 1024 mau tu BRAM, bom vao FIR16 MOI chu ky
// 100 MHz, so tung mau ra voi golden (cung BRAM) ngay tren chip, dem chu ky.
// Bao cao qua USB-UART 115200 8N1 (dang hex, scripts/read_uart.py doi ra JSON):
//   FIR16 PASS N=0400 ERR=0000 LAT=0007 CYC=00000407 FBAD=FFFF   (0x407 = 1031 = 1024 + 7)
// LED: LD4 = xong, LD5 = PASS, LD6 = FAIL, LD7 = nhip tim (board dang chay)
// ============================================================================
`timescale 1ns / 1ps
`default_nettype none

module top_arty #(
    parameter integer CLKS_PER_BIT = 868,
    parameter integer NS = 1024
) (
    input  wire       CLK100MHZ,
    input  wire       ck_rst,        // nut RESET do, muc thap
    input  wire       btn0,
    output wire [3:0] led,
    output wire       uart_rxd_out   // FPGA -> PC
);
    wire clk = CLK100MHZ;

    // ---------------- Reset & nut nhan (dong bo hoa) ----------------
    reg [2:0] rst_sync = 3'b111;
    always @(posedge clk) rst_sync <= {rst_sync[1:0], ~ck_rst};
    wire rst = rst_sync[2];

    reg [2:0] btn_sync = 0;
    always @(posedge clk) btn_sync <= {btn_sync[1:0], btn0};
    wire btn_rise = btn_sync[1] & ~btn_sync[2];

    // ---------------- BRAM: vector vao va golden ----------------
    (* rom_style = "block" *) reg [15:0] rom_in   [0:NS-1];
    (* rom_style = "block" *) reg [15:0] rom_gold [0:NS-1];
    initial begin
        $readmemh("vectors_in.hex", rom_in);
        $readmemh("golden_out.hex", rom_gold);
    end

    // ---------------- FSM ----------------
    localparam S_IDLE = 0, S_RUN = 1, S_DRAIN = 2, S_REPORT = 3;
    reg [1:0]  state;
    reg        run_req;
    reg [10:0] rd_addr;
    reg        rd_en;

    reg               fir_rst;
    reg               in_valid;
    reg signed [15:0] in_data;
    wire              out_valid;
    wire signed [15:0] out_data;

    fir16 u_fir (.clk(clk), .rst(fir_rst), .in_valid(in_valid), .in_data(in_data),
                 .out_valid(out_valid), .out_data(out_data));

    // Doc BRAM co thanh ghi: rd_en o chu ky t -> in_valid/in_data o chu ky t+1
    always @(posedge clk) begin
        in_data  <= rom_in[rd_addr[9:0]];
        in_valid <= rd_en;
    end

    // Golden doc truoc 1 chu ky: gold_q luon = rom_gold[gold_addr]
    reg  [10:0] gold_addr;
    wire [10:0] gold_addr_n = gold_addr + (out_valid ? 11'd1 : 11'd0);
    reg  [15:0] gold_q;
    always @(posedge clk) gold_q <= rom_gold[gold_addr_n[9:0]];

    reg [15:0] n_err, first_bad;
    reg [31:0] cyc;          // tu chu ky in_valid dau tien den out_valid cuoi cung (tinh ca 2)
    reg [15:0] lat;          // tu in_valid dau tien den out_valid dau tien
    reg        counting, got_first, done, pass;
    reg        msg_go, tx_active;

    always @(posedge clk) begin
        msg_go <= 1'b0;
        if (rst) begin
            state <= S_IDLE; run_req <= 1'b1;   // tu chay 1 lan sau reset
            rd_en <= 0; rd_addr <= 0; fir_rst <= 1;
            done <= 0; pass <= 0;
        end else begin
            if (btn_rise) run_req <= 1'b1;
            case (state)
            S_IDLE: begin
                fir_rst <= 1;
                if (run_req && !tx_active) begin
                    run_req <= 0;
                    rd_addr <= 0; rd_en <= 1;
                    gold_addr <= 0;
                    n_err <= 0; first_bad <= 16'hFFFF;
                    cyc <= 0; lat <= 0; counting <= 0; got_first <= 0;
                    fir_rst <= 0;
                    state <= S_RUN;
                end
            end
            S_RUN: begin
                rd_addr <= rd_addr + 1;
                if (rd_addr == NS - 1) begin
                    rd_en <= 0;
                    state <= S_DRAIN;
                end
            end
            S_DRAIN: begin
                if (gold_addr == NS) begin
                    done <= 1;
                    pass <= (n_err == 0);
                    msg_go <= 1'b1;
                    state <= S_REPORT;
                end
            end
            S_REPORT: begin
                if (msg_fin) state <= S_IDLE;
            end
            endcase

            // Dem chu ky va so sanh (chay song song voi FSM)
            if (state != S_IDLE) begin
                if (in_valid && !counting) counting <= 1;
                if (counting || in_valid) cyc <= cyc + 1;
                if (!got_first && !out_valid && (counting || in_valid)) lat <= lat + 1;
                if (out_valid) begin
                    got_first <= 1;
                    gold_addr <= gold_addr_n;
                    if (out_data != $signed(gold_q)) begin
                        n_err <= n_err + 1;
                        if (first_bad == 16'hFFFF) first_bad <= {5'd0, gold_addr};
                    end
                    if (gold_addr == NS - 1) counting <= 0;
                end
            end
        end
    end
    // lat = so chu ky tu in_valid dau tien den truoc out_valid dau tien (= do tre pipeline)
    // cyc = so chu ky tu in_valid dau tien den out_valid cuoi cung; 1 mau/chu ky <=> cyc = NS + lat

    // ---------------- Phat chuoi bao cao qua UART ----------------
    // "FIR16 PASS N=hhhh ERR=hhhh LAT=hhhh CYC=hhhhhhhh FBAD=hhhh\r\n" = 60 byte
    localparam integer MSG_LEN = 60;
    localparam [15:0]  NS16 = NS;
    reg  [5:0] ci;
    reg  [7:0] tx_byte;
    reg        tx_start, msg_fin;
    wire       tx_busy;

    function [7:0] hexc(input [3:0] v);
        hexc = (v < 10) ? (8'h30 + v) : (8'h41 + v - 10);
    endfunction

    reg [7:0] ch;
    always @(*) begin
        case (ci)
            0: ch = "F";  1: ch = "I";  2: ch = "R";  3: ch = "1";  4: ch = "6";  5: ch = " ";
            6: ch = pass ? "P" : "F";  7: ch = "A";
            8: ch = pass ? "S" : "I";  9: ch = pass ? "S" : "L";
            10: ch = " "; 11: ch = "N"; 12: ch = "=";
            13: ch = hexc(NS16[15:12]); 14: ch = hexc(NS16[11:8]); 15: ch = hexc(NS16[7:4]); 16: ch = hexc(NS16[3:0]);
            17: ch = " "; 18: ch = "E"; 19: ch = "R"; 20: ch = "R"; 21: ch = "=";
            22: ch = hexc(n_err[15:12]); 23: ch = hexc(n_err[11:8]); 24: ch = hexc(n_err[7:4]); 25: ch = hexc(n_err[3:0]);
            26: ch = " "; 27: ch = "L"; 28: ch = "A"; 29: ch = "T"; 30: ch = "=";
            31: ch = hexc(lat[15:12]); 32: ch = hexc(lat[11:8]); 33: ch = hexc(lat[7:4]); 34: ch = hexc(lat[3:0]);
            35: ch = " "; 36: ch = "C"; 37: ch = "Y"; 38: ch = "C"; 39: ch = "=";
            40: ch = hexc(cyc[31:28]); 41: ch = hexc(cyc[27:24]); 42: ch = hexc(cyc[23:20]); 43: ch = hexc(cyc[19:16]);
            44: ch = hexc(cyc[15:12]); 45: ch = hexc(cyc[11:8]);  46: ch = hexc(cyc[7:4]);   47: ch = hexc(cyc[3:0]);
            48: ch = " "; 49: ch = "F"; 50: ch = "B"; 51: ch = "A"; 52: ch = "D"; 53: ch = "=";
            54: ch = hexc(first_bad[15:12]); 55: ch = hexc(first_bad[11:8]);
            56: ch = hexc(first_bad[7:4]);   57: ch = hexc(first_bad[3:0]);
            58: ch = 8'h0D; 59: ch = 8'h0A;
            default: ch = " ";
        endcase
    end

    // msg_go (tu FSM) -> phat MSG_LEN byte -> msg_fin 1 xung
    always @(posedge clk) begin
        tx_start <= 1'b0;
        msg_fin  <= 1'b0;
        if (rst) begin
            tx_active <= 1'b0; ci <= 0;
        end else if (msg_go) begin
            tx_active <= 1'b1; ci <= 0;
        end else if (tx_active && !tx_busy && !tx_start) begin
            if (ci < MSG_LEN) begin
                tx_byte <= ch; tx_start <= 1'b1; ci <= ci + 1;
            end else begin
                tx_active <= 1'b0; msg_fin <= 1'b1;
            end
        end
    end

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (
        .clk(clk), .rst(rst), .start(tx_start), .data(tx_byte),
        .tx(uart_rxd_out), .busy(tx_busy));

    // ---------------- LED ----------------
    reg [26:0] hb = 0;
    always @(posedge clk) hb <= hb + 1;
    assign led = {hb[26], ~pass & done, pass & done, done};
endmodule

`default_nettype wire
