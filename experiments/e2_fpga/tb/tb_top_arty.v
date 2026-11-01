// Kiem tra top_arty truoc khi nap board: giai ma UART, chay 2 lan (sau reset + nhan BTN0).
`timescale 1ns / 1ps

module tb_top_arty;
    localparam integer CPB = 8;   // UART nhanh cho mo phong
    reg clk = 0, ck_rst = 0, btn0 = 0;
    wire [3:0] led;
    wire tx;

    top_arty #(.CLKS_PER_BIT(CPB)) dut (.CLK100MHZ(clk), .ck_rst(ck_rst), .btn0(btn0),
                                        .led(led), .uart_rxd_out(tx));
    always #5 clk = ~clk;

    reg [8*80-1:0] line;
    integer nch, nlines, b;
    reg [7:0] c;

    // Bo thu UART: lay mau giua moi bit
    initial begin
        nch = 0; nlines = 0; line = 0;
        forever begin
            @(negedge tx);
            #(CPB * 10 / 2);
            for (b = 0; b < 8; b = b + 1) begin
                #(CPB * 10);
                c[b] = tx;
            end
            #(CPB * 10);
            if (c == 8'h0A) begin
                nlines = nlines + 1;
                $display("UART dong %0d: %0s", nlines, line);
                line = 0;
            end else if (c != 8'h0D) begin
                line = {line[8*79-1:0], c};
            end
        end
    end

    initial begin
        repeat (5) @(posedge clk);
        ck_rst = 1;
        wait (nlines == 1);
        $display("LED = %b (LD7..LD4)", led);
        #100 btn0 = 1; #100 btn0 = 0;
        wait (nlines == 2);
        $finish;
    end

    initial begin
        #5_000_000;
        $display("TIMEOUT");
        $finish;
    end
endmodule
